# Proposal

## Why

Players want an Unbound-style multi-class realm on WoW Forever (Classic 1.60.1), like WoW Unbound
gives WotLK: one home class that also learns spells from other classes. ForeverCore enforces class
almost everywhere, but `Player::LearnSpell` and `Spell::EffectLearnSpell` do not check class. So a
first, data-only version can ship on the upstream image, without building a server, as a separate
catalog option that never touches a player's plain WoW Forever realm.

## What Changes

- **New catalog entry `wow-forever-unbound`, "WoW Forever Unbound"**: a single stack server in the
  `forevercore` family. Its folder (`yulon-forever-unbound`), containers (`foreverunbound-*`),
  volumes, databases and CA are its own. It runs the same pinned `forever-bots` image as
  `wow-forever`, plus its own world SQL. It is listed on the WoW card next to WoW Forever, with the
  🌀 glyph, the subtitle "WoW Forever Classic, multi-class" and the software line "ForeverCore with
  Karrz's PlayerbotV2 bots and Forever Unbound".
- **The Mentor**: an NPC spawned in the six Classic capitals. Through its gossip menu it teaches a
  curated list of other classes' spells, each with a level requirement, **free in v1**. Choosing one
  makes the player cast a Yu'lon server-side spell (`SPELL_EFFECT_LEARN_SPELL`), so the spell goes
  into `character_spell` like any learned spell. v1 lists only spells that cost mana or nothing, and
  offers them only to classes that have mana. Prices wait for v2: in this core the gossip script runs
  before the gossip price is checked, so a price could not be enforced without C++.
- **Shared login for the two Forever entries**: the client always dials port 1119 and resolves
  `trinity.actual.battle.net` through one tagged hosts line. So:
  - Starting either Forever server is refused while the other is running, with a message naming it.
  - Removing one Forever server keeps the hosts line while any install of a `forevercore` entry
    remains. Today the check only looks at installs of the same entry id.
- **Bots unchanged**: PlayerbotV2 bots never use the Mentor and stay single-class. The core is not
  modified.
- No change to `wow-forever` beyond the shared-login rules above. It keeps its id, digest, files and
  behavior.

**Base branch**: `origin/fix/t888-forever-must-fixes` (which contains `feat/wow-forever-steamos`),
on a new branch `feat/wow-forever-unbound`. When upstream merges WoW Forever into `Yulon`, rebase
with `git rebase --onto upstream/Yulon origin/fix/t888-forever-must-fixes feat/wow-forever-unbound`.
New work goes in new files where possible, to keep that rebase small.

**Out of scope (v1)**: a custom server image or any C++ patch. Also out:
- mixing talent trees, and talents taught as spells
- casting across power types (rage or energy characters using mana spells) and mana regeneration for
  non-mana classes
- off-class armor and weapon proficiencies, and off-class skill lines (deleted at login by
  `Player::_LoadSkills`)
- unlocking whole classes (Unbound's class unlocks and milestones); v1 teaches single spells
- prices for Mentor spells (v2, with a C++ Mentor script that checks money before teaching)
- client addons (unless the spellbook test in tasks 1.x shows one is required, which would reopen
  this proposal)
- Gaming Mode (Steam Deck) tiles for the new entry
- multi-class bots
- running both Forever servers at once
- copying any Ascension, Conquest of Azeroth or Wrath Unbound data. Unbound's 3.3.5 spell lists do
  not apply; only its design is followed, credited to DaddyCool.

## Capabilities

### New Capabilities
- `forever-unbound/server-entry`: the WoW Forever Unbound catalog entry. Its identity and
  presentation, its own install footprint beside WoW Forever, and its stack (upstream image plus
  Unbound world SQL).
- `forever-unbound/mentor`: the Mentor NPC and what it teaches. Spawns, the curated spell list, level
  and price rules, eligibility by power type, persistence, and bots left unaffected.
- `forever-shared-login`: how installs of `forevercore` entries share the client's single login path
  (port 1119, the tagged hosts line, per-install CAs). Only one runs at a time, and removing one never
  breaks another's login.

### Modified Capabilities
<!-- none: openspec/specs/ holds no capabilities yet -->

## Impact

- `pylauncher/yulon/catalog/catalog.json`: the new `wow-forever-unbound` entry.
- `pylauncher/catalog/installers/wow-forever-unbound/stack/` (new): base and override compose
  templates, `files/certs-yulon.sh`, and `files/sql/` holding the existing spell-visual hotfix and the
  new Unbound world SQL.
- `pylauncher/yulon/ui/catalog_view.py`: presentation entry and `_SINGLES_ON_THE_WOW_CARD`.
- `pylauncher/main.py` and `pylauncher/yulon/forever_trust.py`: the shared-hosts-line check widened
  from the same game id to every `forevercore` install.
- Stack start path (`stack_controller.py` / `catalog/stack_install.py`): refuse to start while another
  `forevercore` install's containers run.
- Any code that keys Forever behavior on the id `"wow-forever"` (Play, trust, account) must key on
  the family or on `play.forever` instead.
- `pyplan/write-ledger.md`: rows for the new entry's stack files written by `_place_stack_files`.
- Tests: `pylauncher/tests/test_wow_forever_unbound.py` (new), plus updates to `test_wow_forever.py`
  and `test_catalog_view.py`.
- Credits: Karrz (PlayerbotV2, release 0.1.36), advocaite (Forever core), TrinityCore, and DaddyCool
  (the Unbound design).
