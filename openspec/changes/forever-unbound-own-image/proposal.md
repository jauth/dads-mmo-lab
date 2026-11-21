# Proposal

## Why

Every Forever Unbound feature left after phase 1 (prices, cross-power casting, proficiencies,
talents, class unlocks) needs C++ in ForeverCore. Today the realm runs the upstream `forever-bots`
image, which nobody here can change. This change builds Yu'lon's own Forever Unbound image from the
same release source, ships its GPL-2 source and patches with it, and pins it by digest the way WoW
Forever pins its image. It proves the pipeline with the smallest worthwhile C++ feature: the Mentor
takes money before it teaches.

## What Changes

- **The image recipe moves into the repo.** The `forever-bots` image carries its own recipe (its
  `Dockerfile`, `patches/` and Yu'lon's realm scripts under `/opt/forever/src/build/` and
  `/opt/forever/yulon/`). Those files come into this repo as the Forever Unbound image recipe, with
  one fix: the Dockerfile applies the patches itself. Upstream applied them to the tree by hand.
- **Core patches follow Wrath Unbound's layout.** Numbered `.patch` files in the entry's folder,
  each pinned byte for byte by sha256, in a tested order, each with a one-line reason:
  - `0001-casclib-local-storage-read-only.patch`: the patch `forever-bots` already carries.
  - `0002-yulon-mentor-script.patch`: a new file under `src/server/scripts/Custom/` plus one line in
    the custom script loader. No core file outside `Custom/` changes.
- **The Mentor charges a price.** Its creature uses the new C++ script instead of SmartAI. When a
  player picks a spell, the script checks the option's price, takes the money, then teaches the
  spell. A player without enough money gets the core's "not enough money" error, and nothing is
  taken or learned. Bots are refused in code. The price of each spell is its own class trainer's
  cost for it, from this realm's `trainer_spell`, so the client's gossip confirm box shows it.
- **Published to `ghcr.io/jauth/forever-unbound`** (tag `0.1.36-u1`), pinned by `@sha256:` in
  `catalog.json`. The image holds the source zip's URL and sha256 in its labels, plus the Dockerfile
  and patches. That is the GPL-2 corresponding source, the same way `forever-bots` ships it.
- **BREAKING (spec):** WoW Forever Unbound no longer runs the same image as WoW Forever. It runs
  its own image, built from the same release source. A test keeps the two on the same ForeverCore
  release.
- **Start brings an existing install up to date.** A stack's image ref and files are written into
  its folder at install, and nothing rewrites them later. Start now renders the compose files and
  stack files again (the same `write_compose()` Play's certificate remake uses), and pulls a changed
  image with live output before `up`. Characters and databases are kept. WoW Forever gets this too,
  which also serves its own future digest bumps.

**Base branch**: `feat/wow-forever-unbound` (phase 1, archived), on a new branch
`feat/forever-unbound-own-image`. Yu'lon is a personal fork: commits and pushes go to `origin`
(`jauth/dads-mmo-lab`) only, and only when asked. No pull requests to DadsMmoLab. The GHCR push
publishes a public package and needs the owner's explicit go-ahead at that step.

**Out of scope** (each is its own later change):
- **#3, a bigger Mentor spell list**: more spells, higher ranks, higher levels. It is data only and
  does not need this image. The owner wants it done later. Start from this list and the deferred
  note in the agent's project memory (`forever-unbound-bigger-spell-list`). It will need submenus
  (about 32 options per gossip menu), stays within teach IDs 3100100–3100399, and each new spell is
  cast once in game, as in phase 1.
- **#8, the training dummies** (176443, 177469) outside Stormwind and Orgrimmar that move and fight
  back: a separate data-only fix for both Forever entries.
- **#7, Steam Deck Gaming Mode tiles** for the entry.
- **#2, cross-power casting** and rage/energy spell lists; **#4, off-class proficiencies** and skill
  lines kept at login; **#5, talents** across classes or taught as spells; **#6, whole-class
  unlocks** and milestones. Each needs core changes outside `Custom/`, after this pipeline has been
  through one ForeverCore release bump.
- Building the image on the player's computer. The image is built once by the maintainer, and
  players pull it.
- Multi-class bots, client addons, hotfix rows.

## Capabilities

### New Capabilities
- `forever-unbound/server-image`: Yu'lon's own Forever Unbound server image. It is built from WoW
  Forever's release source plus pinned, ordered patches, carries its GPL-2 source, and is published
  and pinned by digest.

### Modified Capabilities
- `forever-unbound/server-entry`: "Same server image as WoW Forever" is replaced by running the
  entry's own pinned image built from the same release. New: an existing install moves to the pinned
  image and files at Start, keeping its data.
- `forever-unbound/mentor`: spells now have a price that the server checks and takes before
  teaching. The Mentor's rows drop their server-side teach spells and SmartAI rows for a C++ script.
  Bots are refused by that script.

## Impact

- New `pylauncher/catalog/installers/wow-forever-unbound/image/`: `Dockerfile`,
  `Dockerfile.dockerignore`, `yulon/*.sh` (from the `forever-bots` image), and a README with the
  build and publish steps.
- New `pylauncher/catalog/installers/wow-forever-unbound/patches/`: `0001-…`, `0002-…`.
- `pylauncher/yulon/forever_unbound_catalog.py`: a price on each spell.
  `pylauncher/yulon/forever_unbound_sql.py`: `ScriptName`, `BoxMoney`/`SpellID` on options, no
  `serverside_spell*` or `smart_scripts` rows. The shipped Mentor SQL is re-rendered.
- `pylauncher/yulon/catalog/catalog.json`: the `wow-forever-unbound` server image ref and notes.
- `pylauncher/yulon/stack_controller.py` (and its seams): re-render and pull before `up`.
- `pyplan/write-ledger.md`: the stack-file and compose-file write rows gain Start as a caller.
- Tests: `test_wow_forever_unbound.py`, a new `test_forever_unbound_image.py`, and
  `test_stack_controller.py`.
- `docs/games-and-bots/wow-forever-unbound.md`, `CHANGELOG.md`.
- Players who also run WoW Forever download a second ~4 GB image.
- Credits: Karrz (PlayerbotV2, release 0.1.36), advocaite (Forever core), TrinityCore, DaddyCool (the
  Unbound design).
