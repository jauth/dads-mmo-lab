"""WoW Forever Unbound: its catalog entry, its stack, the Mentor's spell list and its world SQL.

No database and no server: the SQL is checked as text. Whether the core applies it and teaches
from it is proven in game (phase 1's tasks 3.3 and 3.4; forever-unbound-own-image's task 3.4).
"""

from __future__ import annotations

import re
from pathlib import Path

from yulon import forever_unbound_sql as mentor_sql
from yulon.catalog import composegen
from yulon.catalog.catalog import SingleEntry, load_catalog
from yulon.catalog.stack_install import STACK_FILES, StackInstaller, stack_of
from yulon.forever_unbound_catalog import (
    BANDS,
    MANA_CLASSES,
    MENU_LIMIT,
    SPELL_BY_ID,
    SPELLS,
    STARTING_PRICE,
    STARTING_SPELLS,
    WAITING_CLASSES,
    MentorSpell,
    band_of,
    first_rank,
    spells_in,
    spells_of,
    worst_case_visible,
)

SQL = mentor_sql.render()
CATALOG = load_catalog()
FOREVER: SingleEntry = CATALOG.get_single("wow-forever")
UNBOUND: SingleEntry = CATALOG.get_single("wow-forever-unbound")
INSTALLERS = Path(mentor_sql.__file__).resolve().parents[1] / "catalog" / "installers"
FOREVER_STACK = INSTALLERS / stack_of(FOREVER).templates
UNBOUND_STACK = INSTALLERS / stack_of(UNBOUND).templates
MENTOR_TARGET = f"/opt/forever/src/sql/custom/world/{mentor_sql.FILE_NAME}"
MENTOR_MOUNT = f"    - ./sql/{mentor_sql.FILE_NAME}:{MENTOR_TARGET}:ro"


# -- the catalog entry -------------------------------------------------------------------------


def test_it_is_its_own_entry_on_its_own_server_of_the_same_release() -> None:
    """Its own pinned image (D5), and WoW Forever's release, database, client and login."""
    forever, unbound = stack_of(FOREVER), stack_of(UNBOUND)
    assert UNBOUND.name == "WoW Forever Unbound" and UNBOUND.status == "beta"
    assert unbound.family == "forevercore"
    server = unbound.image("server")
    assert server.ref.startswith("ghcr.io/jauth/forever-unbound@sha256:"), server.ref
    assert server.ref != forever.image("server").ref
    release = forever.image("server").label.rsplit(", ", 1)[-1]
    assert server.label.endswith(f", {release}"), "a bump must move both entries"
    others = [i for i in unbound.images if i.role != "server"]
    assert others == [i for i in forever.images if i.role != "server"]
    assert unbound.downloads == forever.downloads
    assert unbound.client_extract == forever.client_extract
    assert UNBOUND.emulator == FOREVER.emulator
    assert UNBOUND.ports == FOREVER.ports, "the client always dials 1119: one runs at a time"
    assert UNBOUND.play is not None and FOREVER.play is not None
    assert UNBOUND.play.forever == FOREVER.play.forever
    assert UNBOUND.shares_the_forever_login()


def test_nothing_of_its_install_is_wow_forevers() -> None:
    assert not set(UNBOUND.containers()) & set(FOREVER.containers())
    assert all(name.startswith("foreverunbound-") for name in UNBOUND.containers())
    assert UNBOUND.install.default_server_dir == "yulon-forever-unbound"
    assert UNBOUND.install.default_server_dir != FOREVER.install.default_server_dir
    assert stack_of(UNBOUND).templates == "wow-forever-unbound/stack"


def test_it_offers_no_gaming_mode_tiles_yet() -> None:
    """The Gaming Mode scripts name wowforever-* containers; per-entry scripts come later."""
    assert UNBOUND.play is not None and UNBOUND.play.gaming_mode is None


def test_its_notes_credit_the_core_the_bots_and_the_design() -> None:
    notes = " ".join(UNBOUND.notes)
    for name in ("advocaite", "TrinityCore", "Karrz", "DaddyCool"):
        assert name in notes


# -- the stack ---------------------------------------------------------------------------------


def test_its_stack_files_are_wow_forevers_plus_the_mentor() -> None:
    forever_files = {
        p.relative_to(FOREVER_STACK / STACK_FILES): p.read_bytes()
        for p in (FOREVER_STACK / STACK_FILES).rglob("*")
        if p.is_file()
    }
    unbound_files = {
        p.relative_to(UNBOUND_STACK / STACK_FILES): p.read_bytes()
        for p in (UNBOUND_STACK / STACK_FILES).rglob("*")
        if p.is_file()
    }
    mentor = Path("sql") / mentor_sql.FILE_NAME
    assert set(unbound_files) == set(forever_files) | {mentor}
    for name, data in forever_files.items():
        assert unbound_files[name] == data, f"{name} must stay a byte copy of WoW Forever's"


def test_its_templates_differ_from_wow_forevers_only_by_the_mentor_mount() -> None:
    forever_override = (FOREVER_STACK / "override.yml.tmpl").read_text(encoding="utf-8")
    assert (UNBOUND_STACK / "override.yml.tmpl").read_text(encoding="utf-8") == forever_override
    forever_base = (FOREVER_STACK / "base.yml.tmpl").read_text(encoding="utf-8").splitlines()
    unbound_base = (UNBOUND_STACK / "base.yml.tmpl").read_text(encoding="utf-8").splitlines()
    added = [line for line in unbound_base if line not in forever_base]
    assert [line for line in unbound_base if line in added] == unbound_base[
        unbound_base.index(added[0]) : unbound_base.index(added[0]) + 2
    ]
    assert len(added) == 2 and added[0].lstrip().startswith("# ") and added[1] == MENTOR_MOUNT
    assert [line for line in unbound_base if line not in added] == forever_base


def test_an_install_renders_the_mentor_mount_and_places_the_mentor_sql(tmp_path: Path) -> None:
    server_dir = tmp_path / "unbound"
    server_dir.mkdir()
    StackInstaller(UNBOUND).write_compose(server_dir)
    base = (server_dir / composegen.BASE_FILE).read_text(encoding="utf-8")
    assert MENTOR_MOUNT.strip() in base
    assert "foreverunbound-world" in base and "wowforever-" not in base
    placed = server_dir / "sql" / mentor_sql.FILE_NAME
    assert placed.read_bytes() == mentor_sql.SHIPPED.read_bytes()


# -- the spell list --------------------------------------------------------------------------


def test_every_spell_belongs_to_a_class_with_mana_and_is_taught_once() -> None:
    mana_ids = {c.class_id for c in MANA_CLASSES}
    assert all(spell.class_id in mana_ids for spell in SPELLS)
    assert len({spell.spell_id for spell in SPELLS}) == len(SPELLS), "each spell once"
    assert all(spell.name.strip() for spell in SPELLS)


def test_every_level_is_one_a_character_can_reach() -> None:
    assert all(1 <= spell.level <= 60 for spell in SPELLS)


def test_every_spell_has_its_trainers_price() -> None:
    """Copied from `trainer_spell.MoneyCost` (the curation tool has the query), in copper."""
    assert all(isinstance(spell.price, int) and spell.price > 0 for spell in SPELLS)
    prices = {spell.spell_id: spell.price for spell in SPELLS}
    assert prices[116] == 100, "Frostbolt: 1 silver at every mage trainer"
    assert prices[370] == 700 and prices[1494] == 10, "trainers disagree: the lowest price"


def test_every_mana_class_teaches_and_the_rest_wait() -> None:
    """Each mana class has spells to offer the other six; warriors and rogues get none yet."""
    for mentor_class in MANA_CLASSES:
        assert spells_of(mentor_class), f"{mentor_class.name} has nothing to teach"
    waiting = {c.class_id for c in WAITING_CLASSES}
    assert not waiting & {c.class_id for c in MANA_CLASSES}
    assert not any(spell.class_id in waiting for spell in SPELLS)


def test_spells_are_listed_by_class_then_band_and_each_rank_after_the_one_before() -> None:
    order = [c.class_id for c in MANA_CLASSES]
    keys = [(order.index(s.class_id), band_of(s)) for s in SPELLS]
    assert keys == sorted(keys)
    place = {spell.spell_id: i for i, spell in enumerate(SPELLS)}
    for spell in SPELLS:
        if spell.previous is not None:
            assert place[spell.previous] < place[spell.spell_id], spell


def test_every_rank_follows_a_rank_of_its_own_class_in_the_list() -> None:
    """A rank shows once the rank before is known, so that rank must be teachable here too."""
    for spell in SPELLS:
        if spell.previous is None:
            assert spell.rank == 1, spell
            continue
        before = SPELL_BY_ID.get(spell.previous)
        assert before is not None, f"{spell.name} ({spell.spell_id}) follows a spell not taught"
        assert before.class_id == spell.class_id, spell
        assert before.level <= spell.level, spell
        expected = before.rank + 1 if before.name == spell.name else 1
        assert spell.rank == expected, spell


def test_the_starting_spells_cost_ten_copper_and_start_their_lines() -> None:
    assert STARTING_PRICE == 10
    assert len(STARTING_SPELLS) == 13
    for spell in STARTING_SPELLS:
        assert (spell.level, spell.price, spell.rank, spell.previous) == (1, 10, 1, None)
        assert any(s.previous == spell.spell_id for s in SPELLS), f"{spell.name} has no rank 2"
    names = {s.name for s in STARTING_SPELLS}
    assert {
        "Fireball",
        "Smite",
        "Holy Light",
        "Seal of Righteousness",
        "Shadow Bolt",
        "Raptor Strike",
    } <= names


def test_no_band_can_show_more_options_than_the_core_allows() -> None:
    """ForeverCore asserts at 32 options; a band shows at most one rank of each line at a time."""
    assert MENU_LIMIT == 32
    for mentor_class in MANA_CLASSES:
        for band in range(len(BANDS)):
            visible = worst_case_visible(spells_in(mentor_class, band))
            assert visible <= MENU_LIMIT, f"{mentor_class.name} {BANDS[band]}: {visible}"


def test_the_limit_check_counts_lines_not_rows() -> None:
    """33 lines fail it; one line of 40 ranks, or a line that branches once, does not."""
    lines = tuple(MentorSpell(900000 + i, f"Line {i}", 8, 1, 10) for i in range(33))
    assert worst_case_visible(lines) == 33 > MENU_LIMIT
    ranks = [MentorSpell(800000, "Bolt", 8, 1, 10)]
    for i in range(1, 40):
        ranks.append(MentorSpell(800000 + i, "Bolt", 8, 1 + i, 10, i + 1, 800000 + i - 1))
    assert worst_case_visible(tuple(ranks)) == 1
    branch = MentorSpell(700000, "Stone", 8, 10, 10, 1, 800000)
    assert worst_case_visible(tuple(ranks) + (branch,)) == 2


def test_a_lines_ranks_stay_in_the_band_of_its_rank_1() -> None:
    for spell in SPELLS:
        assert band_of(spell) == band_of(first_rank(spell))
        low, high = BANDS[band_of(spell)]
        assert low <= first_rank(spell).level <= high


# -- the rendered SQL --------------------------------------------------------------------------


def test_the_shipped_file_is_the_rendering() -> None:
    """After a change to the list, `python -m yulon.forever_unbound_sql` rewrites the file."""
    assert mentor_sql.SHIPPED.is_file(), "render it: python -m yulon.forever_unbound_sql"
    assert mentor_sql.SHIPPED.read_bytes() == SQL.encode("utf-8")


def test_the_file_sorts_after_every_forevercore_update_and_has_lf_endings() -> None:
    assert mentor_sql.FILE_NAME.startswith("2026_11_20_00_world_")
    assert "\r" not in SQL


def test_every_table_it_fills_it_first_clears_in_the_reserved_ranges_only() -> None:
    inserted = set(re.findall(r"^INSERT INTO `(\w+)`", SQL, re.M))
    deleted = set(re.findall(r"^DELETE FROM `(\w+)`", SQL, re.M))
    phase_1_only = {"smart_scripts", "serverside_spell", "serverside_spell_effect"}
    assert inserted == {
        "creature",
        "creature_template",
        "creature_template_model",
        "creature_template_difficulty",
        "gossip_menu",
        "gossip_menu_option",
        "conditions",
        "creature_template_gossip",
    }
    assert deleted == inserted | phase_1_only, "phase 1's teach spells and SmartAI rows are cleared"
    for line in re.findall(r"^DELETE FROM .*$", SQL, re.M):
        numbers = [int(n) for n in re.findall(r"\b\d{7}\b", line)]
        assert numbers, f"a delete without a reserved id: {line}"
        assert all(3100001 <= n <= 3100399 for n in numbers), line
    assert "UPDATE " not in SQL, "it changes no row it does not own"


def test_the_mentor_opens_its_first_menu() -> None:
    """Found in game, 2026-11-19: with no creature_template_gossip row the Mentor only greeted.

    In this core a creature's menu is linked by `creature_template_gossip`, not by its template.
    """
    link = SQL.split("INSERT INTO `creature_template_gossip`")[1].split(";\n")[0]
    assert f"({mentor_sql.ENTRY}, {mentor_sql.ROOT_MENU}, 0)" in link
    assert SQL.index("INSERT INTO `creature_template_gossip`") > SQL.index(
        "DELETE FROM `creature_template_gossip`"
    )


def test_ironforge_and_thunder_bluff_stand_where_they_were_checked_in_game() -> None:
    """Walked 2026-11-19: in front of the banker, Ironforge's fell through the floor and
    Thunder Bluff's faced the drum, so both stand on a spot read in game with `.gps`."""
    spawns = {b.capital: mentor_sql.spawn_position(b) for b in mentor_sql.BANKERS}
    assert spawns["Ironforge"] == (-4890.86, -995.10, 503.94, 2.27)
    assert spawns["Thunder Bluff"] == (-1258.21, 26.73, 128.19, 1.62)
    for banker in mentor_sql.BANKERS:
        x, y, _z, _o = mentor_sql.spawn_position(banker)
        yards = ((x - banker.x) ** 2 + (y - banker.y) ** 2) ** 0.5
        assert yards >= 2.0, f"{banker.capital}'s Mentor stands inside its banker"
    assert (-1262.78, 24.01) not in {s[:2] for s in spawns.values()}, "Atepa's own spawn"
    for capital, (x, y, z, o) in spawns.items():
        row = f", '0', {x}, {y}, {z}, {o}, 60, 0, 0, 0)"
        assert row in SQL, f"{capital}'s Mentor is spawned where spawn_position says"


def test_every_id_it_makes_is_in_the_reserved_ranges() -> None:
    assert mentor_sql.ENTRY == 3100001
    assert len(mentor_sql.BANKERS) == 6, "one Mentor per Classic capital"
    assert mentor_sql.LAST_MENU == 3100099, "3100021-3100099 checked free on 2026-11-20"
    last_class = mentor_sql.class_menu(len(MANA_CLASSES) - 1)
    assert mentor_sql.ROOT_MENU < last_class < mentor_sql.BAND_MENU_FIRST
    last_band = mentor_sql.band_menu(len(MANA_CLASSES) - 1, len(BANDS) - 1)
    assert last_band <= mentor_sql.LAST_MENU
    menus = [int(n) for n in re.findall(r"^\((\d{7}), 3100\d{5}, ", SQL, re.M)]
    assert menus and all(mentor_sql.ROOT_MENU <= n <= mentor_sql.LAST_MENU for n in menus)
    option_ids = [int(n) for n in re.findall(r"^\(\d{7}, (3100\d{5}),", SQL, re.M)]
    assert option_ids and all(310000000 <= n <= 310099999 for n in option_ids)
    assert len(option_ids) == len(set(option_ids)), "GossipOptionID is global, so each once"
    assert len(option_ids) == len(MANA_CLASSES) + 1 + len(SPELLS) + sum(
        1 for c in MANA_CLASSES for b in range(len(BANDS)) if spells_in(c, b)
    )


def _spell_conditions(menu: int, option: int) -> list[str]:
    return re.findall(rf"^\(15, {menu}, {option}, 0, 0, (.*)\)[,;]$", SQL, re.M)


def test_each_spell_option_carries_its_price_its_spell_and_its_gates() -> None:
    """The script reads the price (`BoxMoney`) and the spell (`SpellID`) from the option row."""
    for index, mentor_class in enumerate(MANA_CLASSES):
        for band in range(len(BANDS)):
            menu = mentor_sql.band_menu(index, band)
            for option, spell in enumerate(spells_in(mentor_class, band)):
                title = mentor_sql.spell_title(spell).replace("'", "''")  # Hunter's Mark
                price = mentor_sql.price_text(spell.price)
                row = (
                    f"({menu}, {mentor_sql.gossip_option_id(menu, option)}, {option}, 0, "
                    f"'Teach me {title} ({price}).', 0, {spell.price}, 'Learn {title}?', "
                    f"{spell.spell_id})"
                )
                assert row in SQL, row
                gates = _spell_conditions(menu, option)
                assert any(g.startswith(f"25, 0, {spell.spell_id}, 0, 0, '', 1,") for g in gates)
                assert any(g.startswith(f"27, 0, {spell.level}, 3, 0, '', 0,") for g in gates)
                after = [g for g in gates if re.match(r"25, 0, \d+, 0, 0, '', 0,", g)]
                if spell.previous is None:
                    assert not after, f"{spell.name} rank 1 needs no rank before it"
                else:
                    assert after == [g for g in after if g.startswith(f"25, 0, {spell.previous},")]
                    assert len(after) == 1, f"{title}: exactly one rank-before condition"


def test_no_menu_has_more_options_without_a_rank_gate_than_the_core_allows() -> None:
    """Options with no rank-before condition can all show at once to a character who knows none."""
    options = re.findall(r"^\((\d{7}), \d{9}, (\d+), ", SQL, re.M)
    ungated: dict[int, int] = {}
    for menu, option in options:
        gates = _spell_conditions(int(menu), int(option))
        if not any(re.match(r"25, 0, \d+, 0, 0, '', 0,", g) for g in gates):
            ungated[int(menu)] = ungated.get(int(menu), 0) + 1
    assert ungated and max(ungated.values()) <= MENU_LIMIT, ungated


def test_each_class_menu_offers_its_bands_from_their_first_level() -> None:
    for index, mentor_class in enumerate(MANA_CLASSES):
        menu = mentor_sql.class_menu(index)
        for option, band in enumerate(b for b in range(len(BANDS)) if spells_in(mentor_class, b)):
            low, high = BANDS[band]
            target = mentor_sql.band_menu(index, band)
            row = (
                f"({menu}, {mentor_sql.gossip_option_id(menu, option)}, {option}, 0, "
                f"'Spells first learned at levels {low} to {high}.', {target}, 0, NULL, NULL)"
            )
            assert row in SQL, row
            gates = _spell_conditions(menu, option)
            if low == 1:
                assert not gates, "the first band is open to every level"
            else:
                assert gates == [
                    f"27, 0, {low}, 3, 0, '', 0, 0, 0, '', "
                    f"'The Mentor - {mentor_class.name} {low}-{high} - from level {low}'"
                ]


def test_the_price_is_shown_in_the_list_the_way_the_game_counts_money() -> None:
    """Each spell's line names its price, so a player sees it before picking the spell."""
    assert mentor_sql.price_text(100) == "1 silver"
    assert mentor_sql.price_text(10) == "10 copper"
    assert mentor_sql.price_text(15005) == "1 gold 50 silver 5 copper"
    assert mentor_sql.price_text(20000) == "2 gold"
    assert "'Teach me Frostbolt (Rank 1) (1 silver).'" in SQL
    assert "'Teach me Purge (Rank 1) (7 silver).'" in SQL
    assert "'Teach me Blink (" in SQL and "'Teach me Blink (Rank" not in SQL, "one rank: no rank"


def test_options_that_teach_nothing_carry_no_price_and_no_spell() -> None:
    """Classes, bands and "nothing yet": the script leaves submenus to the core, closes the rest."""
    options = SQL.split("INSERT INTO `gossip_menu_option`")[1].split(";\n")[0]
    first = f"({mentor_sql.ROOT_MENU}, "
    root = [line for line in options.splitlines() if line.startswith(first)]
    assert len(root) == len(MANA_CLASSES) + 1
    assert all(line.rstrip(",").endswith(", 0, NULL, NULL)") for line in root)
    for index in range(len(MANA_CLASSES)):
        lines = [
            line
            for line in options.splitlines()
            if line.startswith(f"({mentor_sql.class_menu(index)}, ")
        ]
        assert lines and all(line.rstrip(",").endswith(", 0, NULL, NULL)") for line in lines)


def test_each_class_list_is_hidden_from_its_own_class_and_from_classes_without_mana() -> None:
    mana = 0
    for mentor_class in MANA_CLASSES:
        mana |= mentor_class.mask
    for index, mentor_class in enumerate(MANA_CLASSES):
        root = f"(15, {mentor_sql.ROOT_MENU}, {index}, 0, 0, 15, 0, "
        assert f"{root}{mana}, 0, 0, '', 0," in SQL
        assert f"{root}{mentor_class.mask}, 0, 0, '', 1," in SQL
    waiting = f"(15, {mentor_sql.ROOT_MENU}, {len(MANA_CLASSES)}, 0, 0, 15, 0, "
    assert f"{waiting}{1 | 8}, 0, 0, '', 0," in SQL, "warriors and rogues see 'nothing yet'"


def test_the_mentor_runs_its_script_and_no_smartai() -> None:
    """Phase 1 taught through SmartAI, which runs before the core checks a price."""
    assert mentor_sql.SCRIPT_NAME == "npc_yulon_mentor"
    assert f", 7, '', '{mentor_sql.SCRIPT_NAME}', 1, 0)" in SQL
    assert "SmartAI'" not in SQL
    assert "INSERT INTO `smart_scripts`" not in SQL
    assert "INSERT INTO `serverside_spell" not in SQL


def test_the_mentor_cannot_be_fought_and_is_friendly_to_everyone() -> None:
    assert "'The Mentor', 'Forever Unbound', 35, 1," in SQL
    assert f", {0x100 | 0x200}, 7, '', 'npc_yulon_mentor'," in SQL
