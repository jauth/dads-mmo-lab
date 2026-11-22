# Notes

## Task 1.2: inputs (2026-11-20)

- The client's tables were copied from the WoW Forever Unbound data volume
  (`yulon-wow-forever-unbound-…_data`, `/srv/data/dbc/enUS/`) into the session scratchpad, never
  into the repo. In the end the tool reads `SpellName`, `SpellPower`, `SpellShapeshift`,
  `SpellTotems`, `SpellEquippedItems`, `SpellEffect` and `SpellMisc` (see task 1.3).
- `trainers.tsv`: 1,208 rows from the query in `forever_unbound_curate.py`'s docstring, run on the
  Unbound world database (`foreverunbound-database`), read-only. All 30 phase 1 spells are there,
  with phase 1's level and price.

## Task 1.3: the WDC5 reader (2026-11-20)

What the real files showed, beyond the design:
- **`Spell.db2` uses variable-size records** (header flag 1). The reader refuses that format. The tool
  doesn't need `Spell.db2`: ranks come from the trainers' chain, not its rank subtext.
- **Sections keyed "TRINITY"** (`0x5452494E49545900`) are sections the extractor decrypted. They
  hold real rows, such as this realm's own spells. The reader skips a keyed section only when its
  records are all zeros, which means it is still encrypted.
- **A string offset of 0** is an empty string. One SpellName record and its 12 copies have one.
- **`SpellMisc` was added.** Rebirth has a form mask (Tree of Life, Moonkin) but casts with no form,
  through `SPELL_ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED_CASTER_FORM` (`0x80000`, `SpellInfo.cpp:2313`).
  Without that attribute, the form rule would drop Rebirth.
- **Health costs count as no power.** Life Tap's `SpellPower` row has power type -2 (health). It was
  in phase 1 and casts on every class.
- Columns for this client (70707/70888), checked in `_check_columns` on known spells:

  | Table | Column |
  |---|---|
  | SpellPower | parent = spell; column 11 = power type |
  | SpellShapeshift | column 0 = spell; column 3 = form mask |
  | SpellMisc | parent = spell; column 0 = attributes, attribute 2 at index 2 |
  | SpellEffect | parent = spell; column 0 = aura; column 3 = effect; column 28 = implicit targets |
  | SpellTotems | column 0 = spell; column 1 = totem category (low 16 bits) |
  | SpellEquippedItems | column 0 = spell; column 1 = item class; column 3 = subclass mask |

## Task 2.3: the generated list (2026-11-20)

`python -m yulon.forever_unbound_curate`: both self-checks pass (columns, and phase 1's 30 rows
with the same name, level and price). The catalog had **807 rows** at first: 795 generated plus the 12 starting spells (815 after
Seal of Righteousness, below).

| Class | Lines | Rows | Lines left out | Most visible per band (1-15 / 16-30 / 31-60) |
|---|---|---|---|---|
| Paladin | 35 | 124 | 12 | 15 / 12 / 8 |
| Hunter | 28 | 59 | 27 | 15 / 9 / 4 |
| Priest | 30 | 141 | 16 | 12 / 14 / 4 |
| Shaman | 23 | 96 | 30 | 10 / 11 / 2 |
| Mage | 43 | 152 | 6 | 14 / 21 / 8 |
| Warlock | 30 | 124 | 9 | 14 / 14 / 5 |
| Druid | 22 | 111 | 24 | 10 / 10 / 3 |

**Three bands, not two.** With 1-30 and 31-60, the mage's first band could show 35 options, over the
32 limit. Design D5 says to add a band in that case. 1-15 / 16-30 / 31-60 leaves no band empty, and
none passes 21.

**Lines left out (124)**, all listed in `forever_unbound_spells.EXCLUDED`:

| Reason | Lines |
|---|---|
| talent or quest | 58 |
| totem | 17 |
| not in the client's tables | 15 |
| ranged weapon | 9 |
| pet | 6 |
| shared | 4 |
| power | 4 |
| form or stance | 3 |
| armor or weapon skill | 2 |
| above level 60 | 1 |
| deny list | 5 |

- **Talent or quest (58, not the 52 estimated).** The first estimate counted orphan ranks, not
  lines. Examples:
  - talents: Pyroblast, Holy Shock, Mind Flay, Shadowburn
  - the bear spells, whose first rank comes from a quest: Maul, Swipe, Bash
  - this realm's own talent spells: Penance, Lava Burst, Riptide
  - **Priest racial lines**: Desperate Prayer, Touch of Weakness, Hex of Weakness, Starshards,
    Shadowguard, Feedback. Their first rank no trainer teaches, so they are not offered. That
    answers the design's open question. Fear Ward is taught to every priest here and is kept.
- **Not in the client's tables (15):** trainer rows whose spell this client lacks, for example
  Blessing of Salvation (1038), Curse of Shadow (17862), and the old Curse of the Elements (1490).
  This realm teaches 440892 instead, which is kept.
- **Deny list (5, added after reading the output):**
  - Dual Wield: a weapon skill under another effect number
  - Subjugate Demon: the demon becomes a pet
  - Totemic Recall, Call of the Elements, Totemic Call: they work on shaman totems
- **Branches.** Drain Soul rank 1 is what the trainers require before Create Healthstone, Create
  Soulstone and Create Spellstone, so those three hang off Drain Soul in its band (1-15). Each gets
  its own rank numbers. Entangling Roots also branches once. `worst_case_visible` counts each
  branch.
- **Seal of Righteousness** was first left out as "talent or quest": its rank 1 is the paladin's
  starting seal, which no trainer teaches. On 2026-11-20 the owner added it as a 13th starting spell.
  The catalog teaches **21084**, not 20154 (both are named Seal of Righteousness in the client),
  because the trainers' rank 2 (20287) requires 21084. With it the list has **815 rows in 212
  lines**: Paladin has 36 lines and 130 rows, 11 lines left out, and at most 16 / 12 / 8 visible
  per band. The other classes are unchanged.

## Task 5.1: checks, this branch against the base (2026-11-20)

Windows, `pylauncher\.venv` (Python 3.11). The base is a clean worktree of
`feat/forever-unbound-own-image` (`cf41ef0`).

| | This branch | Base |
|---|---|---|
| `ruff check .` | clean | clean |
| `black --check .` | clean (813 files) | not run |
| `mypy yulon main.py` | clean (283 files) | not run |
| `test_wdc5`, `test_forever_unbound_curate` (new) | 31 passed | (do not exist) |
| `test_wow_forever_unbound`, `test_forever_unbound_image`, `test_install_wiring`, `test_single_catalog`, `test_write_ledger` | all passed | 154 passed |

- **The first run failed once**: `test_write_ledger`, because the curation tool's `write_bytes` had
  no row. The proposal had said none was needed. A row was added beside the SQL renderer's (the
  same developer-tool precedent), and the test then passed.
- Also run: `test_changelog_style`, `test_changelog_released_frozen` and `test_docs_pins` pass.
  `test_checkout_links` fails 7 symlink tests on this Windows machine. They are not touched by this
  change.

## Task 4.1: the new SQL on the running realm (2026-11-21)

- The owner started WoW Forever Unbound from this branch's app. The install folder's
  `sql/2026_11_20_00_world_yulon_forever_unbound_mentor.sql` is byte-identical to the branch's.
- World log: `Reapplying update "2026_11_20_00_world_yulon_forever_unbound_mentor.sql" 'A9D6D5F' ->
  '55F8588' (it changed)`, with no errors naming the Mentor.
- `gossip_menu_option` in menus 3100001–3100099: **844**, which is what the renderer writes (8 at
  the top, 21 band options, 815 spells). There are 21 band menus in `gossip_menu`.

## Task 4.3 setup: rank-1 spells for the test character (2026-11-21)

At the owner's request, the 184 rank-1 spells of the six classes other than Hunter were inserted
into `characters.character_spell` for **Hun** (guid 2893, level 60 Night Elf hunter). Hun was
offline (`online = 0`, checked inside the insert). `INSERT IGNORE`; Hun already had 11 of them.
The list is the catalog's lines with `previous is None`, minus Hunter's. To remove them:
`DELETE FROM characters.character_spell WHERE guid = 2893 AND spell IN (<the 184 ids>)`, with Hun
offline.

## Task 4.3: casting rank 1 on Hun (in progress)

- 2026-11-21, session 1: the owner cast the alphabetical checklist (`casting-checklist.md` in this
  change, "Other classes") from Abolish Disease through **Devouring Plague**: 47 of 184, with no
  failures. Resume at **Dispel Magic** (Priest, 527). Hunter's 28 lines need a non-hunter character.
- 2026-11-21: the owner relaxed the rule for the remaining 137: test by kind (proposal, In-game
  testing). The tool's effect data sorted them:
  - 91 ordinary: 55 buff, debuff or over-time; 13 direct damage; 10 direct heal; 7 damage plus an
    effect; 5 dispel; 1 heal plus an effect
  - 46 unusual

  `casting-checklist-short.md` picks **41**:
  - two of each ordinary kind
  - one or two per family (6 portals, 6 teleports, 4 weapon enchants, 3 resistance auras,
    3 resurrects, 3 ground-targeted channels)
  - every other unusual spell, including this realm's own (Fire Nova, Frost Blast, Frostfire Bolt,
    Revive, Seal of Fury, Shadow Word: Death)
