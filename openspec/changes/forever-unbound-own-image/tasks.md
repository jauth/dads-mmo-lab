# Tasks

## 1. Recover the recipe and branch

- [x] 1.1 Check branch `feat/forever-unbound-own-image` was made from `feat/wow-forever-unbound` (done when this change was proposed). Verify: `git merge-base --is-ancestor feat/wow-forever-unbound HEAD` succeeds and `git status` shows only this change's files.
- [x] 1.2 From the pinned `forever-bots` digest (`docker create` then `docker cp`), copy `/opt/forever/src/build/{Dockerfile,Dockerfile.dockerignore}` into `pylauncher/catalog/installers/wow-forever-unbound/image/`, `/opt/forever/yulon/*.sh` into `image/yulon/`, and `patches/0001-casclib-local-storage-read-only.patch` and `README.txt` into `wow-forever-unbound/patches/`. Record each file's sha256. Verify: each copy's sha256 equals the same file read from a fresh `docker cp`.
- [x] 1.3 Download `wow-forever-source-0.1.36.zip` into a scratch folder outside the repo, check its sha256 is `1e92c3d8…` (the image's label), and unpack it. Build the recovered Dockerfile unchanged with `0001` applied by hand, as upstream did. Verify: the build succeeds and `/opt/forever/bin/worldserver` exists in the result (a baseline that proves the recipe reproduces).

## 2. The image recipe and its tests

- [x] 2.1 Change `image/Dockerfile` as design D1 says: apply `patches/*.patch` in name order with `patch -p1 --forward --batch` before `cmake`, failing on any reject. Copy the same patches into `/opt/forever/src/build/patches/`, and set title `forever-unbound` and version `0.1.36-u1`, keeping the source URL, sha256 and license labels. Verify: building with only `0001` succeeds without any hand patching, and a deliberately broken copy of `0001` makes the build fail at the patch step.
- [x] 2.2 Write `image/README.md`: what the image is, the exact build and smoke-test commands (D6), the publish steps marked "owner's go-ahead only", how to bump to a new ForeverCore release, and credits (Karrz, advocaite, TrinityCore, DaddyCool). Verify: following its build command from a clean scratch folder produces the image.
- [x] 2.3 Add `pylauncher/tests/test_forever_unbound_image.py`. It checks the patch folder is exactly `0001`, `0002` in order with pinned sha256s; each patch has a reason sentence in `patches/README.txt`; the `yulon/*.sh` and `Dockerfile.dockerignore` copies match their recorded sha256s; the Dockerfile's `SOURCE_VERSION`, `SOURCE_URL` and `SOURCE_SHA256` match the release in `wow-forever`'s server image label; and `wow-forever-unbound`'s `emulator.sources` equals `wow-forever`'s (D5). Verify: `pytest tests/test_forever_unbound_image.py` passes, and fails when one byte of a patch is changed or `SOURCE_VERSION` is edited.

## 3. The Mentor script and its data

- [x] 3.1 Write `0002-yulon-mentor-script.patch` against the unpacked 0.1.36 tree. It adds `src/server/scripts/Custom/Yulon/yulon_mentor.cpp` (`npc_yulon_mentor`, as design D2 says) with `AddYulonScripts()` and calls it from `custom_script_loader.cpp`. Include the GPL-2 header and a credit to the Wrath Unbound design (DaddyCool). Verify: the image builds with both patches, and the world log at start shows no unknown-ScriptName error for `npc_yulon_mentor`.
- [x] 3.2 Add `price` (copper) to `MentorSpell` in `forever_unbound_catalog.py`. Read each spell's `MoneyCost` from `world.trainer_spell` on a running WoW Forever world database, taking the lowest across its class trainers (D3). Record the query and date in the module docstring. Verify: a `test_wow_forever_unbound.py` test checks every price is a positive int, and the query's output is pasted in this change's notes.md.
- [x] 3.3 Change `forever_unbound_sql.py` as D3 says: `ScriptName 'npc_yulon_mentor'` and empty `AIName`; spell options carry `BoxMoney`, `SpellID` and `BoxText`; no `serverside_spell*` or `smart_scripts` inserts, but their reserved ranges are still cleared. Re-render the shipped SQL with `python -m yulon.forever_unbound_sql`. Update phase 1's tests: replace `test_nothing_is_charged_in_v1` and `test_each_spell_has_a_teaching_spell_a_script_and_its_gates` with tests that each spell option has its catalog price and spell, and that the file still clears the old teach-spell and SmartAI ranges. Verify: `pytest tests/test_wow_forever_unbound.py` passes, including the re-render byte-compare and the D3 ranges test.
- [x] 3.4 In game on a locally built image (tag `forever-unbound:0.1.36-u1`, substituted in the Unbound install's compose file by hand for this test only). Check:
  - (a) A paladin with enough money learns Frostbolt. The confirm box shows the price, it is taken exactly once, and the spell casts.
  - (b) A paladin with too little money gets the not-enough-money error, and nothing changes.
  - (c) Known and too-low spells stay hidden.
  - (d) Warriors and rogues still get the "nothing yet" text.
  - (e) A bot party plays normally.
  - (f) Whether `BoxText` showed without a `broadcast_text` row (the design's open question).

  Verify: results are written in notes.md. If (f) fails, add the `broadcast_text` row inside the reserved ranges and re-check.
- [x] 3.5 (Added at the owner's request, 2026-11-20.) Show each spell's price in the Mentor's spell list, before the player picks it: `option_text()` renders "Teach me Frostbolt (1 silver)." through `price_text()` (gold, silver, copper). It is data only, with no image change; the shipped SQL is re-rendered. Verify: the tests pass, and in game (with 6.1) every spell line shows its price and the confirm box still shows it too.

## 4. Start follows the pinned image

- [x] 4.1 In `stack_controller.py`, add the `refresh` seam bound to `StackInstaller.write_compose`, and call it in `start()` after the port check (D4). A foreign compose file becomes a `SingleServerError` with the installer's sentence. When `docker-compose.yml` changed, run the existing pull with its output going to the live log, then `up`. Verify: new `test_stack_controller.py` cases with fake seams cover the following, each also passing `mypy yulon main.py`:
  - unchanged files: no pull, `up` called once
  - a changed image ref: refresh, then pull, then `up`, in that order
  - a foreign compose file: refused, nothing pulled or started
  - a port conflict: refused before any refresh
- [x] 4.2 Update the `pyplan/write-ledger.md` rows for `stack_install.py::write_compose` / `_place_stack_files` so "when" includes Start. Verify: `pytest tests/test_write_ledger.py` passes.
- [x] 4.3 Upgrade test on the real phase 1 install at `F:\yulon-forever-unbound`, with characters. With the catalog pointing at the locally built image (by its local image ID, for this test only), press Start. Verify: the compose file shows the new ref, the world log shows the Mentor SQL re-applied, every character is there with its learned spells, phase 1's teach spells and SmartAI rows are gone (`SELECT COUNT(*) … BETWEEN 3100100 AND 3100399` returns 0), and WoW Forever's Start afterwards rewrites nothing.

## 5. Publish and pin

- [x] 5.1 **Ask the owner before this step.** Push `ghcr.io/jauth/forever-unbound:0.1.36-u1` and make the package public. Verify: `docker logout ghcr.io` followed by `docker pull ghcr.io/jauth/forever-unbound@sha256:<digest>` succeeds.
- [x] 5.2 Set `wow-forever-unbound`'s `server` image ref in `catalog.json` to that digest, with the label "ForeverCore with Karrz's bots and Yu'lon's Forever Unbound patches, release 0.1.36", and add a note naming the image, its source and patches, and the credits. Change `test_it_is_its_own_entry_on_the_same_server_as_wow_forever` to "own `ghcr.io/jauth/forever-unbound@sha256:` ref, different from Forever's, same release" (D5). Verify: `pytest tests/test_wow_forever_unbound.py tests/test_forever_unbound_image.py tests/test_single_catalog.py` passes.
- [x] 5.3 Update `docs/games-and-bots/wow-forever-unbound.md` in plain language:
  - Spells now cost what their own class trainer charges.
  - The first Start after updating downloads Yu'lon's server (about 4 GB) and keeps your characters.
  - Troubleshooting: "not enough money", "the first Start takes a while", and "the download fails".
  - Credits: Karrz, advocaite, TrinityCore, DaddyCool.
  - A line saying a bigger spell list is planned.

  Verify: the section has each part, and no full trademarked game name appears.
- [x] 5.4 Add `CHANGELOG.md` lines under `## Unreleased`. `### Changed`: "The Mentor on WoW Forever Unbound now charges what each spell's own class trainer charges." `### Changed`: "Starting a WoW Forever server brings an older install up to date first and keeps your characters." Verify: `pytest tests/test_changelog_style.py` passes.

## 6. End-to-end check

- [x] 6.1 On Windows, after 5.2: a fresh install of WoW Forever Unbound beside an installed WoW Forever pulls Yu'lon's image. Then: Play, learn a paid spell at the Mentor in Orgrimmar and in Stormwind, relog, and play with a bot party. Verify: spells are kept and cast, the money is taken once, bots are single-class and behave normally, and WoW Forever's own Start and Play still work with its own image.
- [x] 6.2 From `pylauncher/` with the venv active, run the four checks in `pyplan/contribution.md`: `pytest`, `mypy yulon main.py`, `ruff check .`, `black --check .`. Run the full suite in `yulon-dev:py311`, and compare failures against a clean worktree of `feat/wow-forever-unbound` (about 52 fail there whatever the branch). Verify: no failure that the base does not have, and the other three checks are clean.

## Workflow follow-up

- Commit and push to `origin` only when the owner asks. No pull request to DadsMmoLab.
- Archive with `/opsx:archive forever-unbound-own-image` after the owner's review.
- Next changes, in the order the owner set (2026-11-20): #3 (bigger Mentor spell list, data only; see the proposal's Out of scope and the `forever-unbound-bigger-spell-list` memory), then the #4 and #5a spikes on this image pipeline, then #8 (training dummies, both Forever entries, data only), and #7 (Steam Deck tiles) last.
