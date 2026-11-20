# Notes

## Task 1.1: Spellbook spike (2026-11-19)

Realm: an existing WoW Forever install (ForeverCore 0.1.36, pinned `forever-bots` image), Windows.
GM level set from the world console with
`docker exec wowforever-world /opt/forever/yulon/console.sh "<command>"`; the replies go to
`docker logs wowforever-world`. `console.sh` types one line into the console; it does not open a
prompt.

| Character | Command | Spellbook | Action bar / macro | Casts | Survives relog |
|---|---|---|---|---|---|
| Paladin | `.learn 116` (Frostbolt) | yes, **General** tab | yes / yes (`/cast Frostbolt`) | yes, uses the paladin's mana | yes |
| Paladin | `.learn 8921` (Moonfire) | yes, General tab | yes / yes | yes, uses mana | yes |
| Warrior | `.learn 116` (Frostbolt) | (not checked) | n/a | **no**: "Not enough mana" | n/a |

What this settles:
- The 1.60.1 client shows off-class spells on the General tab and lets them go on action bars. **v1
  needs no addon.**
- Learning without a class gate (`Player::LearnSpell` / `AddSpell`) and keeping spells at login
  (`Player::_LoadSpells`) work the way the code reading predicted.
- Power is per class (`Spell::CheckPower`, ChrClassesXPowerTypes). Mana spells work on mana classes
  and fail on a warrior, which confirms the v1 limit to mana classes and leaving out Warriors and
  Rogues.

## Tasks 3.4 and 5.1: in game on WoW Forever Unbound (2026-11-19)

Install: `python -m yulon.install_wiring wow-forever-unbound` into `F:\yulon-forever-unbound`, client build
70938. Adopted into the app from this branch with **Use existing…**.

| Check | Result |
|---|---|
| Paladin at the Mentor: six classes offered, no Paladin, no warrior/rogue line | pass |
| Mage list at level 4: Arcane Intellect + Frostbolt only; learned free; on General tab; gone once known; casts with mana | pass |
| Warrior: only "I have nothing to teach warriors and rogues yet." | pass |
| Every paladin spell cast on a druid; spells kept across relog | pass |
| Bots grouped with a multi-class player: no Mentor spells, normal play | pass |
| Start WoW Forever while Unbound runs: refused, "…WoW Forever Unbound is running on one of them. Stop it first." | pass |
| Mentor in Stormwind, Darnassus, Orgrimmar, Undercity | pass |

Found and fixed in game:
- **No menu, only the greeting.** This core links a creature to its gossip menu through
  `creature_template_gossip`; the SQL had no row there. Added (`3100001 → 3100001`) with a test
  (`test_the_mentor_opens_its_first_menu`). Re-applied by the updater on a world restart
  (`Updates.Redundancy = 1`: "Reapplying update … (it changed)").
- **Ironforge Mentor fell through the world** ("in front of" banker Gimble Thistlefuzz is off the
  walkable floor) and **Thunder Bluff's faced into the bank's drum**. Both now stand on spots read
  in game with `.gps`: Ironforge (-4890.86, -995.10, 503.94, 2.27), Thunder Bluff (-1262.78, 24.01,
  128.27, 0.10); `test_ironforge_and_thunder_bluff_stand_where_they_were_checked_in_game`.

Not ours, seen while testing: the `Dummy` (176443) and `Boss Dummy` (177469) outside Stormwind and
Orgrimmar move and fight back. ForeverCore 0.1.36's `2026_11_05_99_world_forever_restore_forever_quest_data.sql`
spawns them with no `ScriptName` (the core's `npc_training_dummy` exists). It affects WoW Forever
too; to be reported upstream and/or fixed in a separate change.

## Task 5.1 (rest) and 5.2 (2026-11-20)

- Ironforge Mentor on its `.gps` spot: good. Thunder Bluff: the first `.gps` was read with the banker
  Atepa targeted (`.gps` reports the target's place), so the Mentor stood inside her; re-read with no
  target at (-1258.21, 26.73, 128.19, 1.62), 5 yards from every banker: good. All six Mentors checked.
- Removal of WoW Forever Unbound with WoW Forever installed: Unbound's CA (D2E1850B…) left
  `LocalMachine\Root` (NTE_NOT_FOUND), WoW Forever's CA (C8A83103…) stayed, the tagged hosts line
  stayed, the install record went. WoW Forever then started (`(worldserver-daemon) ready`) and Play
  logged in to its characters.

## Tasks 2.3 and 5.3: the full suite (2026-11-20)

Full non-integration suite in a Linux container (python 3.11, `-n 8`, checkout mounted from Windows):
22254 passed, 56 failed, 1 error. Two failures were this change's, both fixed:
- `test_single_catalog`: the shipped single list now ends with `wow-forever-unbound`.
- `test_install_wiring`: `yulon.forever_unbound_sql` is a new `python -m` module; it is listed as a
  developer tool, like `yulon.manifest`.

The other 52 fail the same way on a clean worktree of the base commit (`fb9d083`) in the same
container: hashes of files checked out with Windows line endings, root ignoring folder permissions,
git and `sg` assumptions. `test_the_header_check_button_is_never_cut_off` timed out under load in the
full run and passes alone on this branch. ruff, black and mypy (linux, win32, darwin) are clean.
