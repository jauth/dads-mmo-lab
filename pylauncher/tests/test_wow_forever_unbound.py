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
    MANA_CLASSES,
    SPELLS,
    WAITING_CLASSES,
    spells_of,
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
    """Copied from `trainer_spell.MoneyCost` (the catalog's docstring has the query), in copper."""
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


def test_spells_are_listed_by_class_then_level() -> None:
    order = [c.class_id for c in MANA_CLASSES]
    keys = [(order.index(s.class_id), s.level) for s in SPELLS]
    assert keys == sorted(keys)


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


def test_every_id_it_makes_is_in_design_d3s_ranges() -> None:
    assert mentor_sql.ENTRY == 3100001
    assert len(mentor_sql.BANKERS) == 6, "one Mentor per Classic capital"
    last_menu = mentor_sql.class_menu(len(MANA_CLASSES) - 1)
    assert mentor_sql.ROOT_MENU < last_menu <= mentor_sql.LAST_MENU
    option_ids = [int(n) for n in re.findall(r"\(\d{7}, (31000\d{4}),", SQL)]
    assert option_ids and all(310000000 <= n <= 310009999 for n in option_ids)
    assert len(option_ids) == len(set(option_ids)), "GossipOptionID is global, so each once"


def test_each_spell_option_carries_its_price_its_spell_and_its_gates() -> None:
    """The script reads the price (`BoxMoney`) and the spell (`SpellID`) from the option row."""
    for index, mentor_class in enumerate(MANA_CLASSES):
        menu = mentor_sql.class_menu(index)
        for option, spell in enumerate(spells_of(mentor_class)):
            name = spell.name.replace("'", "''")  # SQL quoting: Hunter's Mark
            price = mentor_sql.price_text(spell.price)
            row = (
                f"({menu}, {mentor_sql.gossip_option_id(menu, option)}, {option}, 0, "
                f"'Teach me {name} ({price}).', 0, {spell.price}, 'Learn {name}?', "
                f"{spell.spell_id})"
            )
            assert row in SQL, row
            assert f"25, 0, {spell.spell_id}, 0, 0, '', 1," in SQL, "hidden once known"
            assert f"27, 0, {spell.level}, 3, 0, '', 0," in SQL, "hidden below its level"


def test_the_price_is_shown_in_the_list_the_way_the_game_counts_money() -> None:
    """Each spell's line names its price, so a player sees it before picking the spell."""
    assert mentor_sql.price_text(100) == "1 silver"
    assert mentor_sql.price_text(10) == "10 copper"
    assert mentor_sql.price_text(15005) == "1 gold 50 silver 5 copper"
    assert mentor_sql.price_text(20000) == "2 gold"
    assert "'Teach me Frostbolt (1 silver).'" in SQL
    assert "'Teach me Purge (7 silver).'" in SQL


def test_options_that_teach_nothing_carry_no_price_and_no_spell() -> None:
    """Class lists and "nothing yet": the script leaves submenus to the core, closes the rest."""
    options = SQL.split("INSERT INTO `gossip_menu_option`")[1].split(";\n")[0]
    first = f"({mentor_sql.ROOT_MENU}, "
    root = [line for line in options.splitlines() if line.startswith(first)]
    assert len(root) == len(MANA_CLASSES) + 1
    assert all(line.rstrip(",").endswith(", 0, NULL, NULL)") for line in root)


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
