# Tasks

## 1. Inputs and the WDC5 reader

- [x] 1.1 Check branch `feat/forever-unbound-bigger-spell-list` was made from `feat/forever-unbound-own-image` (done when this change was proposed). Verify: `git merge-base --is-ancestor feat/forever-unbound-own-image HEAD` succeeds.
- [x] 1.2 Copy the nine spell tables (design Context) out of the Unbound install's data volume into the session scratchpad, never the repo, and export the class trainers' `trainer_spell` rows to a TSV there. Use the query that 2.1 puts in the tool's docstring: each class found by its anchor spell, with `ReqLevel`, `MoneyCost` and `ReqAbility1`. Verify: the TSV has a row for each of the 30 phase 1 spells, with phase 1's level and price.
- [x] 1.3 Write `pylauncher/yulon/wdc5.py` (design D1): a typed reader for the field kinds, string block, ID list and copy table these tables use. Add `tests/test_wdc5.py` with a small WDC5 file built in the test, covering a plain int, a bitpacked int, a pallet field, a common-data default and a string. Verify: the test passes; reading the real `SpellName` gives "Frostbolt" for 116 and "Moonfire" for 8921; and `mypy yulon` is clean.

## 2. The curation tool and the generated list

- [x] 2.1 Write `pylauncher/yulon/forever_unbound_curate.py` (D1, D2): it reads the TSV and the DB2 folder, applies the rules in D2's order, and writes `forever_unbound_spells.py` (`SPELLS`, `EXCLUDED`, a "generated, do not edit" header). The query and the date go in its docstring. Add the module to `install_wiring`'s developer `python -m` list. Verify: `tests/test_forever_unbound_curate.py` checks each rule on small in-memory rows:
  - a mana line kept with its ranks
  - non-mana power, form or stance, totem, pet, ranged weapon, skill, shared, above 60, and no taught first rank: each dropped with its reason
  - a starting spell accepted as a line's first rank
  - one bad rank drops the whole line
  - a deny-list entry is dropped
  - ranks numbered by chain order
- [x] 2.2 In `forever_unbound_catalog.py` (D3): `MentorSpell` gains `rank` and `previous`; add `STARTING_SPELLS` (13 rows, level 1, `STARTING_PRICE` 10), the deny list with Aspect of the Hawk, and the band of a line. `SPELLS` becomes the starting spells plus the generated rows. Update the docstring's curation and price text. Verify: `mypy yulon` is clean.
- [x] 2.3 Run the tool and commit its output. The tool must fail if any phase 1 row's name, level or price differs from the generated row. Verify:
  - the run succeeds
  - `EXCLUDED` lists the 52 lines without a taught first rank, each with a reason (spot-read: Pyroblast is "talent or quest")
  - the counts of kept lines and rows per class go in this change's notes.md, with any priest racial lines named
- [x] 2.4 Add tests on the shipped list to `tests/test_wow_forever_unbound.py`:
  - every rank's `previous` is in the list, of the same class, at the same or a lower level
  - no band holds more than 32 lines
  - the 13 starting spells cost 10 copper; every other price is positive
  - no spell id appears twice
  - every level is from 1 to 60

  Verify: `pytest tests/test_wow_forever_unbound.py` passes, and fails when a test copy of the list has 33 lines in one band.

## 3. Menus and SQL

- [x] 3.1 Change `forever_unbound_sql.py` as D4 says:
  - class menus hold one option per band (three, see D5); a band needs its first level
  - 21 band menus from 3100021
  - `LAST_MENU` 3100099, with `RESERVED` and the delete header following it
  - the new `gossip_option_id`
  - option text with "(Rank n)" for lines with more than one rank
  - for ranks above 1, a previous-rank-known condition

  Re-render the shipped SQL with `python -m yulon.forever_unbound_sql`. Verify: `pytest tests/test_wow_forever_unbound.py` passes, including the re-render byte-compare and the reserved-range test, and new tests show:
  - each rank-2+ option has exactly one previous-rank condition
  - no menu has more than 32 options without a rank condition
  - option IDs are unique and inside 310000000–310099999
  - each band option above 1 has its level condition
- [x] 3.2 Update `docs/games-and-bots/wow-forever-unbound.md`:
  - the bands and the next-rank rule
  - the 13 starting spells at 10 copper
  - troubleshooting: "I cannot see rank 3": learn rank 2 first; "the 31 to 60 range is missing": it opens at level 31
  - the credits stay as they are

  Add one plain player line to `CHANGELOG.md` under `## Unreleased`. Verify: the guide's links resolve, and the docs tests (`pytest tests -k "docs or guide"`) pass.

## 4. In game (owner plays; record results in notes.md)

- [x] 4.1 Start WoW Forever Unbound from this branch's app (Start re-renders the SQL, as phase 2 does). Verify: the world log shows the Mentor SQL reapplied with no errors, and `SELECT COUNT(*) FROM gossip_menu_option WHERE MenuID BETWEEN 3100001 AND 3100099` equals the renderer's count.
- [ ] 4.2 The 32-limit check: a level 60 character of a mana class (`.levelup`), having learned nothing from the Mentor, opens both bands of every other class. Verify: every band opens, none shows more than 32 options, and the world server keeps running.
- [ ] 4.3 Cast rank 1 of every kept line (relaxed 2026-11-21 by the owner: after the first 47, by kind, per `casting-checklist-short.md`; see the proposal's In-game testing). Per class, use a GM `.learn` batch (the tool prints the ids) on a character of another mana class, then cast each spell once. Verify: each spell casts using mana with its effect. Any that fails goes on the deny list with its reason; then re-run 2.3 and 3.1, and record it.
- [ ] 4.4 The Mentor's own flow:
  - (a) a priest buys Fireball rank 1 for 10 copper, sees rank 2 offered at level 6, buys it, and the price matches
  - (b) a rank above 1 is hidden until the rank before it is known
  - (c) two or three chains per class are bought to a high rank and cast
  - (d) the 16 to 30 band appears at level 16 and the 31 to 60 band at level 31
  - (e) warriors, rogues and a bot party behave as before
  - (f) record whether learning rank N hides rank N-1 in the spellbook (design Open Questions)

  Verify: results are in notes.md.

## 5. Integration checks

- [x] 5.1 From `pylauncher/`, run ruff, black --check and `mypy yulon main.py`, then the test files this change touches, on this branch and on a clean worktree of `feat/forever-unbound-own-image`:
  - `test_wdc5.py`
  - `test_forever_unbound_curate.py`
  - `test_wow_forever_unbound.py`
  - `test_install_wiring.py`
  - `test_single_catalog.py`
  - `test_write_ledger.py`

  Verify: the new failures here are none, and both sides' results are in notes.md.

## Workflow follow-up

- Ask the owner before committing; commit and push to `origin` only, when asked.
- Archive with a spec sync once the in-game checks pass, and update the
  `forever-unbound-bigger-spell-list` memory note.
