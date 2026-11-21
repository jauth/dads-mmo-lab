# Notes

## Task 1.2: the recipe copied out of forever-bots (2026-11-20)

Source: `ghcr.io/dadsmmolab/forever-bots@sha256:ebef1a2ef9dd6123420ddfb4d4be152d0d8846801266391e9d45a254dc7ac5e2`,
copied with `docker create` + `docker cp` from two separate containers. Every file was byte-identical
in both copies.

| Repo path (under `pylauncher/catalog/installers/wow-forever-unbound/`) | From the image | sha256 |
|---|---|---|
| `image/Dockerfile` | `/opt/forever/src/build/Dockerfile` | `0ab7086f410b39e99616936ff247f7d44029ce311898f1135b9dc5a5821ba328` |
| `image/Dockerfile.dockerignore` | `/opt/forever/src/build/Dockerfile.dockerignore` | `8af73c3cf6b6e2b07d0d6e1f724be31e5c53d71c1a84ad88e3f2ec34d3500b1b` |
| `image/yulon/certs.sh` | `/opt/forever/yulon/certs.sh` | `8da2c41678c45a80aa675f3f3c0898945c772cc1b379421e834ddfefa82f38f0` |
| `image/yulon/common.sh` | `/opt/forever/yulon/common.sh` | `b89dbc9f528f26b87d5511667201b72adc5968dce2b48dfba76c51ee424a0555` |
| `image/yulon/configure.sh` | `/opt/forever/yulon/configure.sh` | `22f624789df4735027f65bec917eda3c5f9e96444bfacc0f7035b40fbf10fbd0` |
| `image/yulon/console.sh` | `/opt/forever/yulon/console.sh` | `b27005119d70a2c32ab1d163346cabb42731bcc15a82d3828d3fb40ec2bf16e3` |
| `image/yulon/db-init.sh` | `/opt/forever/yulon/db-init.sh` | `5fb00f19647bca596670df51968a6da7e0629b3d7903eb90f8b37c8ba8dd7a23` |
| `image/yulon/extract.sh` | `/opt/forever/yulon/extract.sh` | `b157a8797c898871ee78f7612ed3c43ff2711b0776fb57e4da5ae2b45a666fa8` |
| `image/yulon/tdb.sh` | `/opt/forever/yulon/tdb.sh` | `fab32e38cb1cdff24396440c052bbcb243e0b165a70827537018d749de0868ab` |
| `image/yulon/world.sh` | `/opt/forever/yulon/world.sh` | `4348ffa046482a3d84f90352cf807faf5c5f28d744622e1ff6571dfba7aabc0d` |
| `patches/0001-casclib-local-storage-read-only.patch` | `/opt/forever/src/build/patches/…` | `74903cbda80c30afaa3dd3665f0bc8ef3cdd7aebcddbf8fd4d7198084308f151` |
| `patches/README.txt` (as copied; Yu'lon adds 0002's reason later) | `/opt/forever/src/build/patches/README.txt` | `f646ce25f3464b1941a8f6e932b08cf532e160707665152267844ee8d9df12c6` |

- `0001` has mixed CRLF and LF lines (its hunks touch CascLib files that use CRLF). `.gitattributes`
  marks `image/**` and `patches/**` `-text`, so no checkout converts a byte.
- `image/Dockerfile` is the upstream recipe as copied. Task 2.1 changes it, and the test pins the
  changed bytes. The sha256 above is the baseline the diff is measured against.

## Task 3.2: trainer prices (2026-11-20 13:34 UTC)

Read from the running WoW Forever world database (`wowforever-database`, schema `world`,
TDB_full_forever_2026_10_14 + ForeverCore 0.1.36 updates), read-only:

```sql
SELECT SpellId, COUNT(*) AS trainers, MIN(MoneyCost) AS min_cost, MAX(MoneyCost) AS max_cost,
       MIN(ReqLevel) AS min_lvl, MAX(ReqLevel) AS max_lvl
FROM trainer_spell WHERE SpellId IN (<the 30 catalog spell ids>) GROUP BY SpellId ORDER BY SpellId;
```

| SpellId | trainers | min_cost | max_cost | min_lvl | max_lvl |
|---|---|---|---|---|---|
| 17 | 33 | 100 | 100 | 6 | 6 |
| 116 | 27 | 100 | 100 | 4 | 4 |
| 139 | 27 | 200 | 200 | 8 | 8 |
| 172 | 23 | 100 | 100 | 4 | 4 |
| 324 | 10 | 100 | 100 | 8 | 8 |
| 339 | 15 | 200 | 200 | 8 | 8 |
| 348 | 23 | 10 | 10 | 1 | 1 |
| 370 | 10 | 700 | 800 | 12 | 12 |
| 465 | 13 | 10 | 10 | 1 | 1 |
| 467 | 18 | 100 | 100 | 6 | 6 |
| 498 | 13 | 100 | 100 | 6 | 6 |
| 589 | 33 | 100 | 100 | 4 | 4 |
| 702 | 23 | 100 | 100 | 4 | 4 |
| 774 | 18 | 100 | 100 | 4 | 4 |
| 853 | 10 | 100 | 100 | 8 | 8 |
| 1126 | 18 | 10 | 10 | 1 | 1 |
| 1130 | 32 | 100 | 100 | 6 | 6 |
| 1152 | 10 | 100 | 100 | 8 | 8 |
| 1243 | 33 | 10 | 10 | 1 | 1 |
| 1454 | 23 | 100 | 100 | 6 | 6 |
| 1459 | 27 | 10 | 10 | 1 | 1 |
| 1494 | 33 | 10 | 93 | 0 | 1 |
| 2136 | 27 | 100 | 100 | 6 | 6 |
| 5143 | 22 | 200 | 200 | 8 | 8 |
| 5782 | 18 | 200 | 200 | 8 | 8 |
| 8017 | 13 | 10 | 10 | 1 | 1 |
| 8042 | 13 | 100 | 100 | 4 | 4 |
| 8921 | 18 | 100 | 100 | 4 | 4 |
| 13163 | 32 | 100 | 100 | 4 | 4 |
| 19740 | 13 | 100 | 100 | 4 | 4 |

All 30 catalog spells have trainer rows. `price` = `min_cost`. The levels agree with phase 1's
catalog (1494's 0 was already raised to 1).

## Tasks 2.1 and 3.1: patch application

- GNU patch 2.8 on Linux applies 0001 to the clean 0.1.36 tree. Git for Windows' `patch` refuses
  it ("different line endings"), which does not matter, because the Dockerfile applies patches on
  Linux.
- `--target source` on a clean tree: 0001 alone applies, then 0001 + 0002 apply, and no hand
  patching is needed.
- A byte-safe broken copy of 0001 (one context line changed, CRLF kept) stops the build at
  `PATCH FAILED: 0001-broken.patch` with exactly that hunk rejected. A first attempt made with Git
  Bash's `sed` stripped the CRs and failed on line endings instead, so it did not test what it was
  meant to.
- Scripts' CMake (`cmake/macros/AutoCollect.cmake`) globs sub-folders recursively, so
  `Custom/Yulon/` is compiled the same way `Custom/Classic/` is.
- In 0002, `custom_script_loader.cpp` keeps its CRLF lines (13 CRs, one per hunk line). The new
  `yulon_mentor.cpp` is LF.
- The "nothing to teach yet" option has no submenu and no spell. The script closes the menu for
  it, as phase 1's SmartAI did.

## Task 1.3: baseline build (2026-11-20)

The recovered Dockerfile was built unchanged, with 0001 applied to the tree by hand (as upstream
did), from `wow-forever-source-0.1.36.zip` (sha256 `1e92c3d8…`, matching the image's label), with
`JOBS=6` on 8 CPUs, in about 40 minutes:
- `forever-unbound-baseline:0.1.36`: image `sha256:95d36d1f…`, 4,161,628,305 bytes, against
  `forever-bots`' 4,161,637,698.
- `bnetserver` is 106,743,464 bytes, the same size as in `forever-bots`. `worldserver` is
  2,324,044,808 bytes (RelWithDebInfo).

The recipe reproduces the published image.

## Task 3.1: the image with both patches (2026-11-20)

Built with `image/README.md`'s exact command (`--build-context yulon=image --build-context
patches=patches`, `JOBS=6`) from a clean unpacked 0.1.36 tree, with no hand patching:
- The `source` stage printed "Applying 0001-…" and "Applying 0002-…", and `Custom/Yulon/yulon_mentor.cpp`
  compiled in the scripts target.
- `ghcr.io/jauth/forever-unbound:0.1.36-u1` (local only, not pushed): image `sha256:139848fc…`,
  4,163,421,131 bytes, labels `forever-unbound` / `0.1.36-u1`.
- `/opt/forever/src/build/` holds the Dockerfile, its ignore file, the README and `patches/` (0001,
  0002, README.txt). `worldserver` contains `npc_yulon_mentor`.

## Task 4.3: upgrade of the real phase 1 install (2026-11-20, owner's go-ahead)

Install: `F:\yulon-forever-unbound` (project `yulon-wow-forever-unbound-1cdb12e3`), made by phase 1 on
`forever-bots@sha256:ebef1a2e…`.

1. **Safety copy.** `mysqldump` of `characters`, `auth` and `playerbot` into the session scratchpad.
   Only the database container was started for it. The snapshot taken then: 1,559 characters.
   Testy (paladin) holds 8 off-class Mentor spells and Fasdfsdf (druid) holds Frostbolt and
   Blessing of Might. The world held 30 teach spells and 61 SmartAI rows.
2. **Read-only pre-check.** Rendered with the then-current catalog, both compose files were
   byte-identical to the install's. Only the Mentor SQL differed.
3. **The test image.** Pushed to a throwaway local registry (`registry:2` on `127.0.0.1:5000`) as
   `localhost:5000/forever-unbound@sha256:139848fc…`. Only `wow-forever-unbound`'s server ref in
   `catalog.json` was pointed at it, as a test-only change.
4. **Stop WoW Forever.** Done with `StackController.stop()` on `F:\yulon-wowf-forever`.
5. **Start.** `StackController.start()` on the Unbound install said: "Wrote docker-compose.yml",
   "Wrote sql/2026_11_20_00_…mentor.sql", the "server changed, downloading" line, then the pull's
   own "Pulling" and "Pulled" lines, then `up`.
6. **The world log.** `Reapplying update "2026_11_20_00_world_yulon_forever_unbound_mentor.sql"
   '4862A6B' -> '510EF15' (it changed)`, then `(worldserver-daemon) ready`, with no ScriptName
   error.
7. **The world rows after.**
   - teach spells 0, their effects 0, SmartAI rows 0
   - `creature_template` 3100001 with `AIName ''` and `ScriptName 'npc_yulon_mentor'`
   - 6 spawns
   - menu 3100006 rows carry `BoxMoney`, `BoxText` and `SpellID` (e.g. 100, "Learn Frostbolt?", 116)
8. **Characters after.** Every pre-existing character row and Mentor-spell set is identical to the
   snapshot, including Testy's and Fasdfsdf's off-class spells. The only differences are 13 random
   bots the bot system created at startup (1,559 → 1,572), each with only its own class's spells;
   they also account for the changed money and level totals.
9. **WoW Forever afterwards.** Stop Unbound, then `StackController.start()` on WoW Forever said
   nothing: no file was rewritten and nothing was pulled. Its compose file still names
   `forever-bots@sha256:ebef1a2e…`. WoW Forever was left running, as found.

The Unbound install's compose file now names the test image. The catalog's test ref and the local
registry stay until task 5.2 puts in the published GHCR digest. Until then, a Start from this branch
keeps that install on the patched image instead of re-rendering it back to `forever-bots`, which
would pair the new SQL with a core that lacks the script.

## Task 3.4: in game on the patched image (2026-11-20, played by the owner)

The upgraded Unbound install ran the locally built image (`localhost:5000/forever-unbound@sha256:139848fc…`,
the same image as `ghcr.io/jauth/forever-unbound:0.1.36-u1`). All six checks passed:

- (a) A paladin learned Frostbolt. The confirm box showed 1 silver, the money was taken once, and the
  spell casts.
- (b) A character with too little money got the not-enough-money error and lost nothing.
- (c) Known and too-low-level spells stayed hidden.
- (d) Warriors and rogues still got the "nothing to teach yet" text.
- (e) A bot party played normally.
- (f) The "Learn …?" `BoxText` showed in the confirm box without a `broadcast_text` row, so none is
  needed. The design's open question is closed.

## Tasks 5.1 and 5.2: published and pinned (2026-11-20, owner's go-ahead)

- Pushed `ghcr.io/jauth/forever-unbound:0.1.36-u1` (signed in as jauth). The registry digest is
  `sha256:139848fcfd3da62f6206142de9745c04bc34c0b2ced44d7b1baae7c69289544b`, the same image that
  passed the upgrade test (4.3) and the in-game checks (3.4).
- `catalog.json` now pins `ghcr.io/jauth/forever-unbound@sha256:139848fc…` with the label "ForeverCore
  with Karrz's bots and Yu'lon's Forever Unbound patches, release 0.1.36", and the entry's
  description and notes say what the image is, where its recipe and patches are, and that the Mentor
  charges trainer prices. The temporary `localhost:5000` ref is gone.
- Right after the push the package was private: an anonymous manifest read returned HTTP 403. It is
  made public on GitHub's package settings page (no API changes a container package's visibility).
- The owner made the package public. Verified without any sign-in, keeping the owner's stored
  token (an empty `DOCKER_CONFIG` stands in for `docker logout`):
  - `docker pull ghcr.io/jauth/forever-unbound@sha256:139848fc…` succeeded.
  - Over plain HTTPS with an anonymous token, the OCI index, the amd64 image manifest
    (`sha256:f56f542d…`) and the attestation manifest all answered, and every config and layer blob
    (11) answered 200/206.
- Removed the `yulon-test-registry` container with its volume and the `localhost:5000` tag. No
  `localhost:5000` is left in the code. The Unbound install's compose file still names the
  `localhost:5000` ref until its next Start re-renders it to the GHCR ref (same digest, so the pull
  only fetches the manifest).

## Tasks 3.5 and 6.1: in game on the published image (2026-11-20, played by the owner)

- A Start from a Yu'lon launched before the catalog moved to GHCR failed ("localhost:5000 … i/o timeout"):
  that running Yu'lon still held the temporary test ref in memory, and the test registry and its tag
  had been removed. After a Yu'lon restart, Start rewrote the compose file to
  `ghcr.io/jauth/forever-unbound@sha256:139848fc…` and started. Players get catalog changes only with a
  new Yu'lon, so they cannot hit this.
- Passed on the upgraded install, in Orgrimmar and Stormwind:
  - every spell line in the Mentor's lists shows its price (e.g. "Teach me Frostbolt (1 silver).") (3.5)
  - a bought spell takes the money once and casts
  - after logging out and back in, the spell is still known
  - a bot party plays normally

## Task 6.2: checks (2026-11-20)

- `ruff check .`, `black --check .` and `mypy yulon main.py` (280 files): clean.
- Full suite: compared earlier in this change (13 failed and 6 errors on both the branch and a clean
  base worktree of `feat/wow-forever-unbound`). After the price-in-list and GHCR catalog edits, the
  owner chose not to wait for a second full run (it takes hours on this machine). Instead, every test
  file touching the changed areas (catalog, forever, stack, single server and client, write ledger,
  changelog, compose, spine: 26 files) ran on the branch and on the base:
  - branch: 13 failed, 1078 passed, 2 skipped
  - base: 13 failed, 1050 passed, 2 skipped
  - The same 13 fail on both, all environmental on Windows: catalog_view layout and WSL tests, the
    certificate swap that needs WSL bash, and the Linux-only Steam Deck tests. The branch adds 28
    passing tests.
- Step 5 (2026-11-20): after stopping Unbound, WoW Forever's Start rewrote nothing and pulled
  nothing. It still runs its own `forever-bots@sha256:ebef1a2e…` image, and the owner logged in and
  played. The first Login press failed with 319 until the key watch wrote the key (22:25:21); the
  next press worked. That is the known key-watch behaviour, not this change.
- The fresh-install variant (a new folder pulling from GHCR) was not run. Pulling from GHCR without a
  sign-in was verified in 5.1, and the upgrade path was played end to end.
