# Design

## Context

See proposal.md (Why). Facts this design rests on, read on 2026-11-20:

**The upstream image carries its recipe.** `ghcr.io/dadsmmolab/forever-bots@sha256:ebef1a2e…`
(4.16 GB, Ubuntu 24.04, GCC 13, Boost 1.83) holds:
- `/opt/forever/src/build/Dockerfile` and `Dockerfile.dockerignore`: a two-stage build of the
  unpacked release zip with `-DSCRIPTS=static -DBUILD_PLAYERBOT_V2=1`.
- `/opt/forever/src/build/patches/`: `0001-casclib-local-storage-read-only.patch` and a
  `README.txt`.
- `/opt/forever/yulon/*.sh`: `certs`, `common`, `configure`, `console`, `db-init`, `extract`, `tdb`
  and `world`.
- OCI labels: source URL and sha256 (`wow-forever-source-0.1.36.zip`, `1e92c3d8…`), version
  `0.1.36`, license `GPL-2.0-only`.

That Dockerfile never applies `patches/`; the patches were applied to the build context by hand.
The recipe is not in this repo.

**Stacks build nothing.** `SingleStack.source` is "never cloned". Wrath Unbound's patches belong
to the `native` engine: `install.native.azerothcore.patches`, applied on the player's computer by
the tolerant `catalog/families/patch.py`, and pinned by `tests/test_unbound_entry.py` (sha256 per
file, order, a reason for each). The `stack` schema has no `patches` field.

**Gossip in ForeverCore 0.1.36** (`Karrz1/TrinityCore@5c8b18a`):
- `WorldSession` (`Handlers/NPCHandler.cpp`) calls
  `unit->AI()->OnGossipSelect(player, packet.GossipID, gossipMenuItem->OrderIndex)`, and calls
  `Player::OnGossipSelect` only when that returns false. So `Player::OnGossipSelect`'s `BoxMoney`
  check and charge are skipped when the AI handles the option.
- `GossipMenu::GetItemByIndex(orderIndex)` returns the option the player picked, from the menu the
  server prepared, and conditions have already filtered that menu.
- `ObjectMgr::LoadGossipMenuItems` does not validate `SpellID`. `Player::OnGossipSelect` casts
  `SpellID` only for item-creating spells, and the column is also sent to the client.
- `scripts/Custom/custom_script_loader.cpp` calls `AddClassicScripts()` (Karrz's
  `Custom/Classic/`). TrinityCore's CMake collects new source files under `Custom/` by itself.

**Installs keep what install wrote.** `StackInstaller.write_compose()` renders both compose files
and copies `stack/files/`. It skips identical files and refuses a compose file Yu'lon did not
write. Only the install stage and Play's certificate remake (`remake_certificates`, T888) call it.
`StackController.start()` runs `compose up` on whatever is in the folder. So an existing install
keeps the old image ref, and the phase 1 Mentor SQL, until something re-renders.

## Goals / Non-Goals

**Goals:**
- A recipe in this repo that reproduces `forever-bots` exactly, plus Yu'lon's patches, applied by
  the Dockerfile itself.
- A Mentor script that has no data of its own. Spell, price and gates stay in the generated SQL,
  so #3 (a bigger list) stays data only.
- An upgrade path at Start that both Forever entries share.

**Non-Goals:**
- A Python build tool or CI workflow for the image. The maintainer runs the documented `docker`
  commands; a tool can come with the second patch that needs one.
- Changing how WoW Forever's own image is pinned or built.
- Wrath Unbound's tolerant `patch.py`. It exists for player-side applies on changing upstream
  trees. Here the tree is a fixed, sha256-pinned zip, so a strict apply that fails the build is
  correct (spec: "The build SHALL fail if any patch does not apply").

## Decisions

### D1. The recipe lives beside the entry, patches in Wrath Unbound's layout

```
pylauncher/catalog/installers/wow-forever-unbound/
  stack/                 (phase 1: compose templates, files/)
  image/
    Dockerfile           forever-bots' Dockerfile + a patch step + Unbound labels
    Dockerfile.dockerignore
    yulon/*.sh           byte copies of forever-bots' /opt/forever/yulon
    README.md            build, smoke-test and publish steps; credits
  patches/
    0001-casclib-local-storage-read-only.patch    byte copy from forever-bots
    0002-yulon-mentor-script.patch                new
    README.txt           one reason sentence per patch (forever-bots' convention)
```

- **Getting the files:** `docker create` the pinned `forever-bots` digest, then `docker cp` its
  `/opt/forever/src/build` and `/opt/forever/yulon`. The sha256 of each copied file is recorded in
  the test. Nothing is rewritten by hand except the Dockerfile's diff, which this design lists.
- **The Dockerfile's diff from upstream:**
  1. In the build stage, before `cmake`: `COPY --from=patches *.patch /patches/`, then for each
     patch in name order, `patch -p1 --forward --batch -d /src < $p || exit 1`.
  2. The final stage copies the same `patches/` into `/opt/forever/src/build/patches/`.
  3. The labels: title `forever-unbound`, a description naming Yu'lon's patches, and
     `org.opencontainers.image.version` `0.1.36-u1`. The source URL, sha256 and license labels are
     unchanged.
- **Build contexts:** the context is the unpacked zip. Named contexts are `yulon=image/` and
  `patches=patches/`.
- **Reasons** live in `patches/README.txt`, as in `forever-bots`, not in `catalog.json`: the stack
  schema has no `patches` field, and adding one only for documentation is not worth a schema
  change.

*Alternatives considered:*
- Build `FROM forever-bots` and recompile only `worldserver`: impossible, because the image has no
  source tree or toolchain.
- A `native` ForeverCore family built on the player's computer: about an hour of compiling per
  install, and the extract, certificate and Play code all assume `stack`.
- Patches in `catalog.json`: needs a schema change for no runtime use.

### D2. The Mentor script reads everything from the option row

`0002` adds `src/server/scripts/Custom/Yulon/yulon_mentor.cpp`, with `AddYulonScripts()`, and one
call to it in `custom_script_loader.cpp`. It holds a `ScriptedAI` named `npc_yulon_mentor`:
- **`OnGossipHello`:** not overridden. The core builds the menu from `creature_template_gossip`
  and the type-15 conditions, as in phase 1.
- **`OnGossipSelect(player, menuId, orderIndex)`:** reads
  `item = player->PlayerTalkClass->GetGossipMenu().GetItemByIndex(orderIndex)`.
  - No item, an item with `ActionMenuID`, or no `SpellID`: return false, so the core opens the
    submenu as before.
  - A bot's session (`GetSession()->IsBot()`) or a spell already known: close the menu, return
    true. Nothing is taken.
  - `!HasEnoughMoney(BoxMoney)`: `SendBuyError(BUY_ERR_NOT_ENOUGHT_MONEY, …)`, close, return true.
    This is exactly what `Player::OnGossipSelect` does.
  - Otherwise: `ModifyMoney(-BoxMoney)`, `LearnSpell(SpellID, false)`, close, return true.

`LearnSpell` is the path phase 1 proved: no class gate, kept at login. The script keeps no table
of its own, so a longer catalog (#3) changes only SQL.

*Alternatives considered:*
- Keep phase 1's server-side teach spells and cast them from the script: two more tables of rows
  for nothing the script needs.
- A separate `yulon_mentor_spell` table: duplicates what the option row already holds.

### D3. SQL generator changes

`forever_unbound_sql.py`:
- `creature_template` 3100001: `AIName ''`, `ScriptName 'npc_yulon_mentor'`.
- Each spell option: `BoxMoney` = its price, `SpellID` = the taught spell, and a `BoxText` such as
  "Learn <spell>?". The client shows this text with the price in its confirm box.
- No `serverside_spell`, `serverside_spell_effect` or `smart_scripts` rows are written. The
  delete-then-insert header still clears their reserved ranges (3100100–3100399, entry 3100001),
  which removes phase 1's rows from existing worlds.
- The D3 ranges from phase 1 are unchanged. The serverside range stays reserved for later use.

`forever_unbound_catalog.py`: `MentorSpell` gains `price` (copper, `int`), copied from
`world.trainer_spell.MoneyCost` for that spell's class trainers. If a spell's trainers disagree,
the lowest price wins, and the test records it.

*Alternative considered:* a price formula by level. Rejected: the trainer price is already this
realm's own number for the spell, and needs no tuning.

### D4. Start re-renders, then pulls a changed image, then starts

`StackController.start()`, after its port check and before `up`:
1. Calls a new seam, `refresh(server_dir) -> Sequence[str]`, bound to
   `StackInstaller(entry).write_compose`. It returns the lines naming what changed, and its
   refusal for a compose file Yu'lon did not write becomes a `SingleServerError`.
2. If `docker-compose.yml` changed, runs the existing `compose_pull` with its output going to the
   server's live log, then `up`.

The refresh is the same function the install and the certificate remake already use, so no new
kind of write is added. The ledger rows for compose and stack files gain "Start" as when they
happen. WoW Forever goes through the same path. With unchanged files it writes nothing and pulls
nothing.

*Alternatives considered:*
- Tell players to remove and reinstall: that loses characters.
- An "Update" button for stacks: more UI and a new flow, for something Start can do invisibly.

### D5. Keeping the two Forever entries on one release

`test_forever_unbound_image.py` checks:
- The Dockerfile's `SOURCE_VERSION`, `SOURCE_URL` and `SOURCE_SHA256` args name the release in
  `wow-forever`'s server image label (`release 0.1.36`).
- `wow-forever-unbound`'s `emulator.sources` equals `wow-forever`'s.
- The patch folder holds exactly the listed patches, in order, matching their sha256s, and each
  has a reason in `README.txt`.
- The `yulon/*.sh` copies match their recorded sha256s.
- The catalog ref is `ghcr.io/jauth/forever-unbound@sha256:<64 hex>`.

Phase 1's `test_it_is_its_own_entry_on_the_same_server_as_wow_forever` changes from "equal refs" to
"different refs, same release".

### D6. Publishing

The maintainer runs these steps, from `image/README.md`:
1. Download the zip and check its sha256.
2. Unpack it.
3. `docker build -f image/Dockerfile --build-context yulon=image --build-context patches=patches
   -t ghcr.io/jauth/forever-unbound:0.1.36-u1 <unpacked>`.
4. Smoke-test it locally: run the existing Unbound install with that tag substituted.
5. **With the owner's explicit go-ahead:** `docker push`, then make the GHCR package public.
6. Record the pushed digest in `catalog.json`.

## Risks / Trade-offs

- **A different compiler run could change bot behavior.** → The same source, toolchain, flags and
  Dockerfile are used. The end-to-end check plays a bot party on the new image.
- **The image must be public on GHCR**, or every install's pull fails. → A task checks an
  anonymous `docker pull` from a signed-out daemon.
- **About 4 GB more disk** for players with both Forever servers. → Accepted. It is stated in the
  guide.
- **Upstream bumps ForeverCore.** → D5's test fails until Unbound is rebuilt. Strict patch applies
  fail the build if `0002`'s context moved, though it only adds a loader line.
- **Start now writes files.** → It is the same idempotent `write_compose()`, and it refuses a
  compose file the player wrote. Tests cover the unchanged, changed-ref and foreign-file cases.
- **A pull inside Start takes minutes.** → Its output goes to the live log; it happens only when
  the ref changed.
- **New SQL meeting the old image** (no `npc_yulon_mentor` in the binary). The core would log an
  unknown `ScriptName`, and `Player::OnGossipSelect` would charge the price and teach nothing. →
  Both ship in one catalog entry and change together. The test for D4 checks that the image ref and
  the SQL move as a pair.
- **The client's confirm box** may not render `BoxMoney` on this client. → Checked in game before
  publish. If it doesn't, the price goes into `BoxText` and the script's check still enforces it.

## Migration Plan

1. Release Yu'lon with the new ref and SQL.
2. On an existing Unbound install, the next Start re-renders the folder, pulls Yu'lon's image and
   starts.
3. The updater sees the changed Mentor SQL ("Reapplying update … (it changed)",
   `Updates.Redundancy = 1`, seen in phase 1) and applies it. Phase 1's teach spells and SmartAI
   rows go away; spells already learned stay in `character_spell`.

**Rollback:** revert the catalog ref and the SQL file together. The next Start re-renders back to
the upstream image, and the phase 1 SQL brings back the teach spells and SmartAI rows. Prices
already paid are not refunded.

## Open Questions

- Whether `BoxText` needs a `broadcast_text` row to show on this client, or plain `BoxText` is
  enough. Answered in game in task 3; either way it stays inside the reserved ranges.
  **Answered (task 3.4, 2026-11-20):** plain `BoxText` shows, and no `broadcast_text` row is needed.
