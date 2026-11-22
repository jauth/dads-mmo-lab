# Proposal

## Why

The Mentor teaches 30 spells, all rank 1 and all learned by level 12. A WoW Forever Unbound character
gets nothing from other classes after that, and has no way to raise a borrowed spell past its first
rank. Phase 2's Mentor script reads the spell and price from each menu option, so a full list is now
data only: no C++ and no new image.

## What Changes

- **Every rank the class trainers teach, levels 1 to 60**, for the seven mana classes. The list goes
  from 30 rows to roughly 1,000: about 120 to 180 spell lines and their higher ranks. It is built by
  machine from this realm's `world.trainer_spell` and the client's own spell tables. Hand-typed rows
  stay only for the 13 starting spells (below).
- **Only the next rank is offered.** A rank above 1 is shown only to a character who knows the rank
  before it, the same rule the class trainers apply (`ReqAbility1`). Known spells and spells above the
  character's level stay hidden as today.
- **The 13 starting spells' rank 1 is taught for 10 copper**: Fireball, Frost Armor, Smite, Lesser
  Heal, Holy Light, Seal of Righteousness (added 2026-11-20, during apply), Wrath, Healing Touch,
  Shadow Bolt, Demon Skin, Lightning Bolt, Healing Wave, Raptor Strike. A character of another class never gets these, and no trainer teaches them, so
  without them none of their later ranks could ever be offered. 10 copper is what trainers charge for
  level-1 spells. Every other price stays the spell's own class trainer price.
- **Each class's list is split in three**: spells first learned at levels 1 to 15, 16 to 30, and
  31 to 60. A line's ranks all stay in the band of its rank 1. (Planned as two bands; the data put
  the mage's 1 to 30 band at 35 lines, so design D5's third band was added, 2026-11-20.) No menu can show more than 32 options, because
  ForeverCore asserts that limit and a larger menu would stop the world server.
- **Curation gets wider rules, checked by machine.** Phase 1's rules still apply: mana or no power
  cost, no stance, form, pet or totem spell. New: no armor or weapon skills, no spell that needs a
  ranged weapon, and no talent or quest-only line (its first rank is never taught). Every line left
  out is recorded with its reason.
- **The Mentor's reserved gossip menus widen** from 3100001–3100020 to 3100001–3100099. The range
  was checked free on 2026-11-20. Option IDs change so a menu can hold more than 99 rows.
- **In-game testing**: rank 1 of every new line is cast once. Higher ranks share their line's
  mechanics and are spot-checked. Phase 1's rule of casting every spell once is relaxed for higher
  ranks only (owner's decision, 2026-11-20).
  - **Relaxed again (owner's decision, 2026-11-21)**, after 47 of 184 lines were cast with no
    failures. The rest are tested by kind:
    - two of each ordinary kind (damage, heal, buff or debuff, dispel)
    - one or two of each family that works alike (portals, teleports, weapon enchants, resistance
      auras, resurrects, ground-targeted channels)
    - every unusual spell, and every one of this realm's own spells

    The 41 picks are in `casting-checklist-short.md`.

**Base branch**: `feat/forever-unbound-own-image` (phase 2, archived), on a new branch
`feat/forever-unbound-bigger-spell-list`. Yu'lon is a personal fork: commits and pushes go to
`origin` (`jauth/dads-mmo-lab`) only, and only when asked. No pull requests to DadsMmoLab.

**Out of scope** (each is its own later change):
- Warriors and Rogues, and spells that cost rage or energy (**#2**, cross-power casting).
- Talent spells and talent-gated ranks (**#5**). Off-class armor and weapon skills (**#4**).
- Any C++ change or new image. The pinned `forever-unbound` image stays as it is.
- Levels above 60, and spells no class trainer on this realm teaches, apart from the 12 starting
  spells.
- **#7** Steam Deck tiles, **#8** training dummies.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `forever-unbound/mentor`: the catalog covers every trainer rank to level 60, plus the starting
  spells' rank 1. A higher rank is offered only once the rank before it is known. Class lists are
  split by level band, with a 32-option limit per menu. The starting spells have their own price.

## Impact

- New dev-only modules in `pylauncher/yulon/`: a reader for the client's WDC5 spell tables, and a
  curation tool that writes the generated spell list. They never run in the app; the generated list
  is checked in.
- `pylauncher/yulon/forever_unbound_catalog.py`: classes, the 13 starting spells, and a rank's
  previous spell. The generated rows live in a new data module beside it.
- `pylauncher/yulon/forever_unbound_sql.py`: band menus, the previous-rank condition, the wider
  menu range and option IDs. The shipped Mentor SQL is re-rendered.
- Tests: `test_wow_forever_unbound.py` and a new test for the generated list.
- `docs/games-and-bots/wow-forever-unbound.md`, `CHANGELOG.md`.
- `pyplan/write-ledger.md`: a row for the curation tool's one write (the generated module), like the
  SQL renderer's row. The SQL reaches existing installs at the next Start, through phase 2's
  re-render.
- Credits as before: Karrz, advocaite, TrinityCore, and DaddyCool (the Unbound design).
