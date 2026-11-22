# Design

## Context

See proposal.md (Why). Facts this design rests on, read on 2026-11-20 from the WoW Forever Unbound
world database (TDB_full_forever_2026_10_14 + ForeverCore 0.1.36 updates + phase 2's Mentor SQL)
and the ForeverCore 0.1.36 source:

**Trainer data.** `world.trainer_spell` (`TrainerId, SpellId, MoneyCost, ReqLevel, ReqAbility1..3`).
`trainer.Type` 0 is a class trainer, but nothing in the table names the class, and
`creature_template.unit_class` only covers warrior, paladin, rogue and mage NPCs. A class's trainers
are found from one spell only that class's trainers teach (today's level-1 catalog spell per class).
Across the seven mana classes their trainers teach about 1,200 spell rows: about 265 lines with no
`ReqAbility1`, and about 940 higher ranks. Two spells are taught by trainers of two classes. One
hunter row is level 80 (Call Pet, 83245).

**Lines without a taught first rank.** 64 ranks have a `ReqAbility1` no trainer of their class
teaches. 12 are the starting spells (proposal). The other 52 are taken to be talent or quest lines;
the curation tool lists each one, so this is checked, not assumed.

**The gossip limit.** `GossipMenu::AddMenuItem` asserts `_menuItems.size() <= 32`
(`GossipDef.cpp:47`, `GOSSIP_MAX_MENU_ITEMS`). `Player::PrepareGossipMenu` skips options whose
conditions fail before it adds them (`Player.cpp:14966`), so the limit applies to the options one
character sees. A failed assert stops the world server.

**Phase 2's script** (`npc_yulon_mentor`) reads `SpellID` and `BoxMoney` from the picked option and
keeps no table of its own, so any number of options needs no C++.

**The client's spell tables** are in the install's data volume (`/srv/data/dbc/enUS/*.db2`), format
WDC5: `Spell`, `SpellName`, `SpellPower`, `SpellShapeshift`, `SpellTotems`, `SpellReagents`,
`SpellEquippedItems`, `SpellEffect`, `SpellLevels`. Yu'lon has no DB2 reader.

**Free IDs.** `gossip_menu`, `gossip_menu_option` and type-15 `conditions` hold no rows for menus
3100021–3100099, and no `GossipOptionID` in 310000000–319999999 belongs to another menu (checked
2026-11-20).

## Goals / Non-Goals

**Goals:**
- A list built by a repeatable tool from the realm's own data, so the ~1,000 rows are never typed by
  hand and a ForeverCore bump can regenerate them.
- The 32-option limit guaranteed by the shipped data and a test, not by what players happen to know.
- The SQL renderer stays the one place that turns the catalog into rows.

**Non-Goals:**
- Running the curation tool in the app or in tests. It needs a world database and a client.
- Changing the Mentor script, the image or the compose templates.

## Decisions

### D1. A dev-only curation tool writes a checked-in data module
Two new modules in `pylauncher/yulon/`, each with one job:
- `wdc5.py`: reads a WDC5 file into records by field. It covers only what these nine tables use:
  plain, bitpacked, common-data and pallet fields, the string block, the ID list and copy table.
- `forever_unbound_curate.py`: the rules. `python -m yulon.forever_unbound_curate --trainers <tsv>
  --db2 <folder>` writes `forever_unbound_spells.py`.

The inputs are files, not live connections, so the rules can be tested on small in-memory rows:
- `--trainers` is a TSV export of `trainer_spell` joined to each class's trainers. Its query is in
  the tool's docstring.
- `--db2` is a folder copied out of the data volume. Client files are read where they are and never
  committed.

`forever_unbound_spells.py` starts with a "generated, do not edit" line and holds two tuples:
- `ROWS`: the offered rows, as plain tuples (so it imports nothing from the catalog).
- `EXCLUDED`: spell id, name, class and reason for every line left out (spec: "Excluded spell lines
  are recorded").

It is reviewable in a diff, like the shipped SQL. `mypy yulon` checks the tool. `install_wiring`'s
list of developer `python -m` modules gains it, as phase 1 did for `forever_unbound_sql`.

*Alternatives considered:*
- Hand-typing the rows as phase 1 did: about 1,000 rows, with names and ranks copied by eye.
- Reading names from wago-style CSV exports online: an outside download, and their build may not
  match 70888.
- Asking the running world server (`.lookup spell`): one console line per spell, with no power,
  form or effect data.

### D2. Curation rules, in the order the tool applies them
For each class, from its trainers' rows (lowest `ReqLevel`, lowest `MoneyCost`, `ReqLevel` 0 raised
to 1):
1. A line is a chain linked by `ReqAbility1`. Its rank is its place in the chain, and its name is
   `SpellName`.
2. Drop the whole line, with its reason, if its first rank:
   - has no trainer row and is not one of the 13 starting spells: "talent or quest"
   - is taught by more than one class: "shared"
   - is above level 60
3. Drop the line if any rank:
   - has a `SpellPower` row whose power type is not mana or health: "power". Health counts as no
     power: every class has it, and phase 1's Life Tap costs it. (Found while building.)
   - has a `SpellShapeshift` form mask without `SpellMisc`'s "allow while not shapeshifted"
     attribute, or a shapeshift aura effect: "form or stance". (Rebirth has a mask and casts with
     no form, found while building, so `SpellMisc` was added to the inputs. `Spell.db2` was
     dropped: its records are variable-size, and ranks come from the trainers' chain.)
   - has a `SpellTotems` row or summons a totem: "totem"
   - summons, targets or needs a pet: "pet"
   - needs a ranged weapon in `SpellEquippedItems`: "ranged weapon"
   - teaches a skill or proficiency: "armor/weapon skill"
4. Drop anything on a short hand-kept deny list in `forever_unbound_catalog.py`, each entry with its
   reason. Aspect of the Hawk is phase 1's case, and spells found misbehaving in game go here.

Rules 3 and 4 drop the whole line, never a single rank, so a chain never has a hole.

### D3. Catalog shape
`MentorSpell` gains `rank: int` and `previous: int | None` (the spell id of the rank before). The
rest stays in `forever_unbound_catalog.py`:
- the classes
- `STARTING_SPELLS`: 13 hand-written rows at level 1, price 10 copper, rank 1
- `STARTING_PRICE = 10`
- the deny list
- `SPELLS`: the starting spells plus the generated rows

A line's band comes from its rank 1's level: 1 to 15, 16 to 30, or 31 to 60 (`BANDS`). Option text
shows "(Rank n)" when the line has another rank of the same name. A rank counts only same-name ranks
before it: Create Soulstone follows Drain Soul rank 1 but is its own rank 1.

### D4. Menus and IDs
```
3100001 root ---- "Teach me Mage spells." ----> 3100002..3100008 class menus (as today)
                                                   |  "Spells first learned at levels 1 to 15."
                                                   |  "... 16 to 30."  (level >= 16)
                                                   |  "... 31 to 60."  (level >= 31)
                                                   v
                                     3100021 + 3*class_index + band   band menus (21)
```
- `LAST_MENU` becomes 3100099. `RESERVED["gossip_menu"]` and the delete header follow it.
- `gossip_option_id` becomes `310000000 + (menu - 3100000) * 1000 + option`. That allows up to 999
  rows per menu, all inside the space checked free. Every option is deleted and inserted by
  `MenuID`, so the old IDs go away when the file is applied.
- Order within a band: by rank-1 level, then name, then depth in the chain (not rank: a branch
  that is rank 1 of its own name must come after the rank it follows).
- Conditions per spell option: level at least the required level; this spell not known; for rank
  above 1, `previous` known (`CONDITION_SPELL`, not negated). Conditions in one `ElseGroup` must all
  hold.

### D5. The 32 limit, by construction
The visible options in a band are at most its number of lines and branches, because every line
shows at most one rank per branch to a character who learned its ranks in order. That count is the
number of spells no other spell follows (`worst_case_visible`). Two tests check it: no band passes
32 by that count, and no menu has more than 32 options with no rank condition. If a band passes 32,
the fix is another band, made in the catalog. The renderer never trims the list silently.

**Applied while building:** with two bands, the mage's 1 to 30 band counted 35. Three bands
(1-15 / 16-30 / 31-60) leave no band empty and none above 21 (notes.md, task 2.3).

## Risks / Trade-offs

- **A reader bug gives wrong names or misses an exclusion.** → The tool checks itself against the 30
  phase 1 rows (names, levels, prices must match) and fails if any differ. In game, rank 1 of every
  line is cast.
- **An off-class spell that misbehaves gets past the rules** (it reads the caster's class, or needs
  a class resource). → The deny list, filled from tonight's casting. The rules lean toward dropping a
  line.
- **About 1,000 options and 3,000 condition rows in one SQL file.** → The updater applies it once
  per change. The file is regenerated, never hand-edited, and a test compares the render.
- **Higher ranks are not each cast** (owner's decision). → Spot checks of two or three chains per
  class. A rank shares its line's mechanics, and the rules run over every rank.
- **A band passes 32 after a data change.** → Caught by a test before anything ships.

## Migration Plan

1. Ship the re-rendered Mentor SQL in the same entry. No image or catalog ref changes.
2. On an existing install, the next Start re-renders the stack files (phase 2). The updater reapplies
   the changed SQL (`Updates.Redundancy`), which clears the reserved ranges and inserts the new
   menus.
3. Spells already learned stay known. A character who knows rank 1 sees rank 2 at once.

**Rollback:** revert the catalog, generated module and SQL together. The next Start re-renders the
old file. Spells learned in the meantime stay known.

## Open Questions

- Whether learning rank N hides rank N-1 in this client's spellbook. It doesn't change the data;
  checked in game.
- Whether priest racial lines appear in the trainer data. If so, they are offered to every race;
  the tool's output shows them for review.
