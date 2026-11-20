# Design

## Context

The code here is from `origin/fix/t888-forever-must-fixes` and the ForeverCore v0.1.36 source
(`wow-forever-source-0.1.36.zip`, sha256 `1e92c3d8…`). Paths written `game/…` are under that tree's
`src/server/game/`.

**What gates class in ForeverCore**
- `Player::IsSpellFitByClassAndRace` (`game/Entities/Player/Player.cpp:27167`) and the trainer
  class mask (`game/Entities/Creature/Trainer.cpp:224`, `GetSpellState`) refuse off-class spells at
  trainers.
- `Player::LearnSpell` (:3501) → `Player::AddSpell` (:2975) check only `SpellMgr::IsSpellValid`.
  The same holds for `Spell::EffectLearnSpell` (`game/Spells/SpellEffects.cpp:2170`).
- `Player::_LoadSpells` (:21186) keeps off-class spells at login. `Player::_LoadSkills` (:28685)
  deletes off-class skill lines.
- `Spell::CheckPower` (`game/Spells/Spell.cpp:7726`) needs the class to have the power type. Power
  slots come from ChrClassesXPowerTypes (`DB2Manager::GetPowerIndexByClass`).

**Gossip in this core**
- `WorldSession` calls the creature AI's `OnGossipSelect` first (`Handlers/NPCHandler.cpp:269`).
  `SmartAI::OnGossipSelect` (`game/AI/SmartScripts/SmartAI.cpp:760`) runs `SMART_EVENT_GOSSIP_SELECT`
  (62). Unless that sets the gossip return, `Player::OnGossipSelect` (:15140) runs next.
  - It checks `BoxMoney` with `HasEnoughMoney` and charges it (`ModifyMoney(-cost)`, :15396).
  - Its own `SpellID` column is cast only for item-creating spells, so it is not used here.
- Gossip options can be gated by conditions: `CONDITION_SOURCE_TYPE_GOSSIP_MENU_OPTION` 15, with
  `CONDITION_LEVEL` 27, `CONDITION_CLASS` 15 and `CONDITION_SPELL` (to hide known spells).
- `serverside_spell` and `serverside_spell_effect` are world tables loaded into the spell store
  (`SpellMgr.cpp:2821/2946`). ForeverCore's own custom SQL uses them already.

**The stack**
- The world server's updater applies `sql/custom/{world,hotfixes,…}`: `Updates.EnableDatabases 15`
  and `SourceDirectory /opt/forever/src`, set in the image's `/opt/forever/yulon/configure.sh`.
- `stack/files/` is copied into the install by `_place_stack_files` and mounted read-only. This is
  how the spell-visual hotfix already ships.
- `StackController.start` (`stack_controller.py:112`) refuses while any container not its own holds
  one of its host ports. `Catalog` validation (`catalog.py:6251`) skips the duplicate-port check for
  `forevercore` entries, on purpose ("one realm at a time").
- Removal keeps the hosts line only while another install has the **same game id**
  (`main.py:1434`).

**The precedent**: WoW Unbound (`wow-unbound`) is a separate entry beside WoW WotLK and borrows its
templates. Wrath Unbound's design (Mentor, purchases, bots single-class) is DaddyCool's. Its 3.3.5
data does not apply to Classic 1.60.

## Goals / Non-Goals

**Goals:**
- A second `forevercore` entry that reuses everything WoW Forever already does: image, TDB, client
  extract, certificates, Play, key watch.
- A Mentor NPC built only from world data, that teaches curated mana-cost off-class spells for a
  price and a level.
- Two Forever-family installs that coexist safely: one running at a time, and removal never breaks
  the other.
- A small diff on files `wow-forever` already owns, so the branch rebases cleanly when upstream
  merges Forever.

**Non-Goals:**
- Any C++, a custom image, client addons, talents, cross-power casting, proficiencies, or Gaming
  Mode tiles (see the proposal's out-of-scope list).
- Changing how `wow-forever` installs or plays.

## Decisions

### D1. A second catalog entry with its own template folder
Add `wow-forever-unbound` to `catalog.single` with `stack.family: forevercore` and
`stack.templates: wow-forever-unbound/stack`:
- Its own `base.yml.tmpl` and `override.yml.tmpl` are copies of Forever's with one extra mount
  block for the Unbound SQL.
- `files/` holds `certs-yulon.sh` and the spell-visual hotfix. These are byte copies, and a test
  asserts they stay identical to Forever's.

*Alternative considered:* point `templates` at `wow-forever/stack` and add an overlay mechanism to
the stack engine (the way `wow-unbound` borrows `wow-wotlk/native`). Rejected for v1. The stack
engine has no overlay concept, and adding one touches `stack_install.py`, the file most likely to
conflict when upstream merges. Copying three small templates costs less, and the identical-copy
test catches drift.

The rest of the entry:
- `images`, `downloads` (TDB) and `client extract` are copied from `wow-forever` unchanged.
- `services[].container` uses `foreverunbound-*`.
- `default_server_dir` is `yulon-forever-unbound`.
- `play` is the same as Forever's, without `gaming_mode`.
- `CA_NAME` comes from `{{PROJECT_NAME}}`, so it already differs.
- A test asserts the `server` image ref equals `wow-forever`'s, so a digest bump cannot leave one
  behind.

### D2. The Mentor is pure world SQL, applied by the core's own updater
One file, `files/sql/2026_11_20_00_world_yulon_forever_unbound_mentor.sql`, mounted at
`/opt/forever/src/sql/custom/world/`. The `2026_11_20` date sorts after every upstream custom file.
It is idempotent: it deletes its own reserved ID ranges, then inserts. It holds:
- `creature_template` (+ `creature_template_model` / difficulty rows as this core needs) for The
  Mentor: gossip flag, `AIName = 'SmartAI'`, a neutral faction, no trainer flag.
- `creature` spawns: six rows, one per capital, near each bank.
- `gossip_menu` / `npc_text` (or `broadcast_text`, whichever this core reads for menu text): a
  greeting, plus a "nothing for you yet" text for Warriors and Rogues.
- `gossip_menu_option`:
  - Root menu: one option per class, opening that class's submenu (`ActionMenuID`).
  - Each submenu: one option per catalog spell, `BoxMoney` 0 (free in v1).
- `conditions`, type 15, on those options:
  - `CONDITION_CLASS` negated: hides the player's own class.
  - `CONDITION_CLASS` mask: the mana classes only.
  - `CONDITION_LEVEL` ≥ required level.
  - `CONDITION_SPELL` negated: hides known spells.
- `serverside_spell` + `serverside_spell_effect`: one "Mentor: teach <spell>" spell per catalog
  row, with effect `SPELL_EFFECT_LEARN_SPELL` (36), `TriggerSpell` = the taught spell, and implicit
  target the caster.
- `smart_scripts`: on `SMART_EVENT_GOSSIP_SELECT` (menu, option),
  - `SMART_ACTION_INVOKER_CAST` (134) with `castFlags` triggered (2) and
    `SMART_TARGET_ACTION_INVOKER` (7): the player casts the teach spell on itself, with no range or
    sight check against the Mentor. The core already uses this pattern 21 times on gossip select.
  - then `SMART_ACTION_CLOSE_GOSSIP` (72).

**No price in v1 (decided 2026-11-19, during apply).** `WorldSession` runs the creature AI's
`OnGossipSelect` *before* `Player::OnGossipSelect` (`Handlers/NPCHandler.cpp:269`). So SmartAI
teaches the spell before the option's `BoxMoney` is checked (`Player.cpp:15166`), and a player who
cannot afford it still learns it. This core has no money condition to hide such options, and no
SmartAI action that takes money. Prices therefore wait for v2's C++ Mentor script, which can check
and take money before teaching.

*Alternatives considered:*
- Mentor-sold spell "tomes": new hotfix items using the recipe "on learn" path. Rejected for v1:
  ItemSparse rows must match the 70888 client exactly.
- Pay in one gossip step and learn in a second. Rejected: closing the window between the steps
  loses the money.
- A C++ `CreatureScript`: needs a custom image (v2).

**The catalog spell list** is chosen in tasks, by these rules:
- the spell is in the 70707/70888 client data
- its `SpellPowerCost` is mana or none
- it is not a stance, form, pet or totem spell (no dependency on other class systems)
- rank 1 only in v1
- the required level is the spell's own `BaseLevel`

The list must also be backed by this realm's own data. Every spell is taught by its class's trainers
in `world.trainer_spell`, which gives the required level. The class comes from grouping spells by
the set of trainers that teach them, and each group matched one class. Starting spells (Fireball,
Smite, Holy Light rank 1 and others) have no trainer row and are left out.

The list is kept in a typed data module (`pylauncher/yulon/forever_unbound_catalog.py`). A second
typed module, `pylauncher/yulon/forever_unbound_sql.py`, renders it to SQL and has a `__main__`
entry that writes the shipped file. It lives in `yulon/` so that `mypy yulon` checks it; the repo
has no `tools/` folder. A test re-renders the file and compares it with the shipped one, so the list
stays reviewable in one place.

### D3. Reserved ID ranges
All Unbound rows use Yu'lon's `31xxxxx` space, which already holds hotfix push 3100001:

| Rows | Range |
|---|---|
| creature entry | 3100001 |
| spawn GUIDs | 3100001–3100006 |
| gossip menus | 3100001–3100020 |
| npc_text | 3100001–3100003 |
| serverside spells | 3100100–3100399 |
| SmartAI | on the entry (`source_type` 0) |

A test asserts the SQL file never touches IDs outside them.

**Checked free on 2026-11-19 (task 1.3).** The check ran against a running WoW Forever world database:
TDB_full_forever_2026_10_14 plus every ForeverCore 0.1.36 custom update the server had applied. All
ten ranges returned 0 rows:

| Range | Rows |
|---|---|
| `creature_template` 3100001 | 0 |
| `creature_template_model` 3100001 | 0 |
| `creature` guid 3100001–3100006 | 0 |
| `gossip_menu` 3100001–3100020 | 0 |
| `gossip_menu_option` 3100001–3100020 | 0 |
| `npc_text` 3100001–3100003 | 0 |
| `serverside_spell` 3100100–3100399 | 0 |
| `serverside_spell_effect` 3100100–3100399 | 0 |
| `smart_scripts` entry 3100001 | 0 |
| `conditions` type 15 on 3100001–3100020 | 0 |
| `hotfixes.spell_name` 3100100–3100399 | 0 |

The ranges sit far below the current maximum in each table:

| Table | Current maximum |
|---|---|
| `creature_template` | 8110005 |
| `creature` guid | 91839271 |
| `gossip_menu` | 92251965 |
| `npc_text` | 20253849 |
| `serverside_spell` | 9970801 |

So a GM's `.npc add` (MAX(guid)+1) can never land in the reserved spawn GUIDs. That was Wrath
Unbound's spawn-ID problem; it does not apply here.

### D4. One Forever-family server at a time: reuse the port refusal, name the server
`StackController.start` already refuses because port 1119 is held by the other install's
`*-bnet`. Change the message: look up which catalog entry owns each holding container (by
`entry.containers()`) and say "WoW Forever is running; stop it first." Fall back to the container
name for a foreign container. Play goes through the same start, so it refuses the same way.

### D5. The hosts line is shared by family, not by id
Change `main.py:1434` so `shared` holds when any other install's entry is a stack with
`family == "forevercore"` and a `play.forever` block. The predicate lives in one place
(`forever_trust.py` or a small `forever_family.py` helper) and both callers use it. CA removal is
already per install (thumbprint in the install record) and does not change.

### D6. No Gaming Mode for the new entry
Omit `play.gaming_mode` from `wow-forever-unbound`. The scripts hard-code `wowforever-*`
container names. Making them per-entry is a follow-up.

### D7. Branch and credits
- Branch `feat/wow-forever-unbound` from `origin/fix/t888-forever-must-fixes`. Add an `upstream`
  remote for `DadsMmoLab/dads-mmo-lab`.
- The entry's `notes` credit Karrz (PlayerbotV2, 0.1.36), advocaite (Forever core), TrinityCore,
  and DaddyCool (the Unbound design).
- `help_places` has the same three rows as Forever's.

## Risks / Trade-offs

- **The spellbook may not show off-class spells** (the client groups spells by skill line).
  → Task 1.1 tests this with `.learn` before any work. If spells are hidden, stop and revise the
  proposal (addon needed).
- **Free spells make v1 easy to exploit.** Accepted: it is a single-player realm with bots, and the
  level gate still holds. Prices come with v2.
- **Some off-class spells may misbehave**: class-scripted spells that read the caster's class, or
  spells needing reagents. → The curation rules exclude stance, form, pet and totem spells, and each
  listed spell is cast once in game before it ships (task 4.x).
- **Copied templates can drift from Forever's.** → A test diffs everything but the expected
  differences (container names, SQL mount).
- **A digest bump on one entry only.** → A test requires equal server refs.
- **Players who also run WoW Forever must stop one to play the other.** Accepted: the client dials
  1119 for any Forever-family realm.
- **No undo for learned spells on this realm.** Accepted: the realm is multi-class by choice, and
  plain WoW Forever is untouched.
