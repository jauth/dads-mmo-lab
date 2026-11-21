"""Render the Mentor's world SQL for WoW Forever Unbound from its spell list. One job: data to SQL.

The rendered file ships in the entry's stack (`stack/files/sql/`). The install copies it into the
server folder, compose mounts it read-only into ForeverCore's `sql/custom/world/`, and the world
server's own updater applies it once. This module builds the text only; it never touches a
database. `python -m yulon.forever_unbound_sql` rewrites the shipped file after `SPELLS` changes,
and `test_wow_forever_unbound.py` fails while the shipped file and this rendering differ.

The Mentor's menus and rules are data; what it does when a spell is picked is C++:
  * The Mentor is a creature with a gossip menu: one option per other mana class, each opening
    that class's list.
  * Its `ScriptName` is `npc_yulon_mentor`, the script Yu'lon's server image adds
    (`catalog/installers/wow-forever-unbound/patches/0002-yulon-mentor-script.patch`). A spell
    option carries the spell it teaches (`SpellID`) and its price (`BoxMoney`), which the client
    shows in its confirm box. The script checks the price, takes it, then `Player::LearnSpell`s the
    spell, which has no class check and is saved like any learned spell. It never teaches a bot.
  * Conditions on each option hide the player's own class, every class without mana, spells above
    the player's level and spells already known. The server builds the menu from them, so a hidden
    option cannot be chosen.

Phase 1 taught through server-side spells cast by SmartAI, free, because SmartAI runs before the
core checks a price. Those rows are gone, but their reserved ranges are still cleared, so applying
this file to a phase 1 world removes them.

Every id is in Yu'lon's reserved `31xxxxx` space (design D3), checked free on 2026-11-19. The file
deletes exactly those ranges before it inserts, so applying it twice gives the same rows.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from yulon.forever_unbound_catalog import (
    MANA_CLASSES,
    WAITING_CLASSES,
    MentorClass,
    MentorSpell,
    spells_of,
)

FILE_NAME = "2026_11_20_00_world_yulon_forever_unbound_mentor.sql"
"""Its name in ForeverCore's `sql/custom/world/`. The updater applies files in name order, and this
date sorts after every update ForeverCore 0.1.36 ships."""

SHIPPED = (
    Path(__file__).resolve().parents[1]
    / "catalog"
    / "installers"
    / "wow-forever-unbound"
    / "stack"
    / "files"
    / "sql"
    / FILE_NAME
)
"""The rendered file as the entry ships it."""

ENTRY = 3100001
"""The Mentor's `creature_template` entry (phase 1's SmartAI rows were keyed on it too)."""
SCRIPT_NAME = "npc_yulon_mentor"
"""The C++ script the Mentor runs, from the server image's patch 0002."""
SPAWN_GUID_FIRST = 3100001
ROOT_MENU = 3100001
"""The Mentor's first menu: one option per other mana class."""
CLASS_MENU_FIRST = 3100002
"""The first class list; `MANA_CLASSES[i]`'s list is `CLASS_MENU_FIRST + i`."""
LAST_MENU = 3100020
GOSSIP_OPTION_ID_BASE = 310000000
"""`GossipOptionID` is global: ours are this + (menu - 3100000) * 100 + option."""
TEACH_SPELL_FIRST = 3100100
"""Phase 1's server-side teach spells: still reserved and cleared, none written now."""
TEACH_SPELL_LAST = 3100399

RESERVED: dict[str, tuple[int, int]] = {
    "creature_template": (ENTRY, ENTRY),
    "creature": (SPAWN_GUID_FIRST, SPAWN_GUID_FIRST + 5),
    "gossip_menu": (ROOT_MENU, LAST_MENU),
    "serverside_spell": (TEACH_SPELL_FIRST, TEACH_SPELL_LAST),
}
"""Design D3's ranges, by the table whose key they are."""

GREETING_TEXT = 68
"""`npc_text` 68, the core's default greeting. A menu body names an `npc_text` whose words are
client BroadcastText, so new words would need another hotfix table; option text is free text."""
DISPLAY_ID = 2968
"""The Mentor's model: Archmage Malin's (entry 2708), a robed human."""
CONTENT_TUNING_ID = 864
"""Archmage Malin's level and health tuning, copied with his `HealthModifier` and `StaticFlags1`."""
FACTION_FRIENDLY_TO_ALL = 35
NPCFLAG_GOSSIP = 1
UNIT_FLAGS_IMMUNE = 0x100 | 0x200
"""Immune to players and to creatures: no one can fight the Mentor."""

CONDITION_SOURCE_GOSSIP_OPTION = 15
CONDITION_CLASS = 15
CONDITION_SPELL = 25
CONDITION_LEVEL = 27
COMP_TYPE_HIGH_EQ = 3

FRONT_YARDS = 4.0
"""How far in front of its banker each Mentor stands, on the customers' side."""


@dataclass(frozen=True, slots=True)
class Banker:
    """One capital's banker, read from the world database, beside whom a Mentor stands.

    `spot` is an exact place read in game with `.gps` (x, y, z, orientation), with nothing
    targeted: `.gps` reports the target's place when there is one. It wins over the place in
    front of the banker where that one is wrong: walked on 2026-11-19, Ironforge's fell through
    the floor and Thunder Bluff's faced into the bank's drum. Thunder Bluff's first `.gps` was
    read with the banker Atepa targeted, so that Mentor stood inside her; its spot is the one
    read after, 5 yards from every banker.
    """

    capital: str
    name: str
    map_id: int
    x: float
    y: float
    z: float
    orientation: float
    spot: tuple[float, float, float, float] | None = None


BANKERS: tuple[Banker, ...] = (
    Banker("Stormwind", "Olivia Burnside", 0, -8931.23, 605.80, 99.61, 0.49),
    Banker(
        "Ironforge",
        "the Vault of Ironforge",
        0,
        -4809.03,
        -1186.13,
        512.56,
        3.26,
        spot=(-4890.86, -995.10, 503.94, 2.27),
    ),
    Banker("Darnassus", "Idriana", 1, 9938.84, 2521.53, 1317.66, 4.38),
    Banker("Orgrimmar", "Karus", 1, 1627.32, -4376.07, 11.81, 3.44),
    Banker("Undercity", "Randolph Montague", 0, 1599.96, 240.65, -52.06, 0.09),
    Banker(
        "Thunder Bluff",
        "Chesmu",
        1,
        -1252.82,
        24.74,
        128.27,
        3.18,
        spot=(-1258.21, 26.73, 128.19, 1.62),
    ),
)
"""The six Classic capitals' bankers (TDB_full_forever_2026_10_14), in spawn-guid order."""


def _q(text: str) -> str:
    """`text` as a SQL string literal."""
    return "'" + text.replace("\\", "\\\\").replace("'", "''") + "'"


def _rows(rows: Iterable[Sequence[object]]) -> str:
    """Rows as a VALUES list, one row per line."""
    lines = []
    for row in rows:
        cells = ["NULL" if c is None else _q(c) if isinstance(c, str) else str(c) for c in row]
        lines.append("(" + ", ".join(cells) + ")")
    return ",\n".join(lines) + ";\n"


def _insert(table: str, columns: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    names = ", ".join(f"`{c}`" for c in columns)
    return f"INSERT INTO `{table}` ({names}) VALUES\n" + _rows(rows)


def class_menu(index: int) -> int:
    """The menu of `MANA_CLASSES[index]`'s spells."""
    return CLASS_MENU_FIRST + index


def gossip_option_id(menu: int, option: int) -> int:
    """The global `GossipOptionID` of option `option` in `menu`."""
    return GOSSIP_OPTION_ID_BASE + (menu - 3100000) * 100 + option


def price_text(copper: int) -> str:
    """`copper` the way the game counts money: "1 gold 50 silver", "7 silver", "10 copper"."""
    gold, rest = divmod(copper, 10000)
    silver, copper = divmod(rest, 100)
    coins = ((gold, "gold"), (silver, "silver"), (copper, "copper"))
    return " ".join(f"{n} {coin}" for n, coin in coins if n) or "free"


def option_text(spell: MentorSpell) -> str:
    """The line in a class's spell list, with the price shown before the player picks it."""
    return f"Teach me {spell.name} ({price_text(spell.price)})."


def box_text(spell: MentorSpell) -> str:
    """The question the client's confirm box asks, above the price, before `spell` is taught."""
    return f"Learn {spell.name}?"


def _mask(classes: Iterable[MentorClass]) -> int:
    mask = 0
    for mentor_class in classes:
        mask |= mentor_class.mask
    return mask


def spawn_position(banker: Banker) -> tuple[float, float, float, float]:
    """Where the Mentor stands: its checked `spot`, else `FRONT_YARDS` in front of `banker`."""
    if banker.spot is not None:
        return banker.spot
    x = banker.x + FRONT_YARDS * math.cos(banker.orientation)
    y = banker.y + FRONT_YARDS * math.sin(banker.orientation)
    return (round(x, 2), round(y, 2), banker.z, banker.orientation)


def _deletes() -> str:
    first_spawn, last_spawn = RESERVED["creature"]
    return (
        f"DELETE FROM `creature` WHERE `guid` BETWEEN {first_spawn} AND {last_spawn};\n"
        f"DELETE FROM `creature_template` WHERE `entry` = {ENTRY};\n"
        f"DELETE FROM `creature_template_model` WHERE `CreatureID` = {ENTRY};\n"
        f"DELETE FROM `creature_template_difficulty` WHERE `Entry` = {ENTRY};\n"
        f"DELETE FROM `creature_template_gossip` WHERE `CreatureID` = {ENTRY};\n"
        f"DELETE FROM `gossip_menu` WHERE `MenuID` BETWEEN {ROOT_MENU} AND {LAST_MENU};\n"
        f"DELETE FROM `gossip_menu_option` WHERE `MenuID` BETWEEN {ROOT_MENU} AND {LAST_MENU};\n"
        f"DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = "
        f"{CONDITION_SOURCE_GOSSIP_OPTION} AND `SourceGroup` BETWEEN {ROOT_MENU} AND {LAST_MENU};\n"
        f"DELETE FROM `smart_scripts` WHERE `entryorguid` = {ENTRY} AND `source_type` = 0;\n"
        f"DELETE FROM `serverside_spell` WHERE `Id` BETWEEN {TEACH_SPELL_FIRST} AND "
        f"{TEACH_SPELL_LAST};\n"
        f"DELETE FROM `serverside_spell_effect` WHERE `SpellID` BETWEEN {TEACH_SPELL_FIRST} AND "
        f"{TEACH_SPELL_LAST};\n"
    )


def _creature() -> str:
    template = _insert(
        "creature_template",
        (
            "entry",
            "name",
            "subname",
            "faction",
            "npcflag",
            "speed_walk",
            "speed_run",
            "scale",
            "unit_class",
            "unit_flags",
            "type",
            "AIName",
            "ScriptName",
            "RegenHealth",
            "VerifiedBuild",
        ),
        [
            (
                ENTRY,
                "The Mentor",
                "Forever Unbound",
                FACTION_FRIENDLY_TO_ALL,
                NPCFLAG_GOSSIP,
                1,
                1.14286,
                1,
                1,
                UNIT_FLAGS_IMMUNE,
                7,
                "",
                SCRIPT_NAME,
                1,
                0,
            )
        ],
    )
    model = _insert(
        "creature_template_model",
        ("CreatureID", "Idx", "CreatureDisplayID", "DisplayScale", "Probability", "VerifiedBuild"),
        [(ENTRY, 0, DISPLAY_ID, 1, 1, 0)],
    )
    difficulty = _insert(
        "creature_template_difficulty",
        (
            "Entry",
            "DifficultyID",
            "ContentTuningID",
            "HealthModifier",
            "ManaModifier",
            "ArmorModifier",
            "DamageModifier",
            "StaticFlags1",
            "VerifiedBuild",
        ),
        [(ENTRY, 0, CONTENT_TUNING_ID, 1.15, 1, 1, 1, 524288, 0)],
    )
    spawns = []
    for index, banker in enumerate(BANKERS):
        x, y, z, o = spawn_position(banker)
        spawns.append(
            (SPAWN_GUID_FIRST + index, ENTRY, banker.map_id, "0", x, y, z, o, 60, 0, 0, 0)
        )
    creature = _insert(
        "creature",
        (
            "guid",
            "id",
            "map",
            "spawnDifficulties",
            "position_x",
            "position_y",
            "position_z",
            "orientation",
            "spawntimesecs",
            "wander_distance",
            "MovementType",
            "VerifiedBuild",
        ),
        spawns,
    )
    places = ", ".join(f"{b.capital} (beside {b.name})" for b in BANKERS)
    return f"-- The Mentor, in {places}\n" + template + model + difficulty + creature


def _menus() -> str:
    menus = [(ROOT_MENU, GREETING_TEXT, 0)]
    menus += [(class_menu(i), GREETING_TEXT, 0) for i in range(len(MANA_CLASSES))]
    option_columns = (
        "MenuID",
        "GossipOptionID",
        "OptionID",
        "OptionNpc",
        "OptionText",
        "ActionMenuID",
        "BoxMoney",
        "BoxText",
        "SpellID",
    )
    options: list[tuple[object, ...]] = []
    for index, mentor_class in enumerate(MANA_CLASSES):
        text = f"Teach me {mentor_class.name} spells."
        option_id = gossip_option_id(ROOT_MENU, index)
        options.append((ROOT_MENU, option_id, index, 0, text, class_menu(index), 0, None, None))
    waiting = len(MANA_CLASSES)
    waiting_names = " and ".join(c.name.lower() + "s" for c in WAITING_CLASSES)
    text = f"I have nothing to teach {waiting_names} yet."
    options.append(
        (ROOT_MENU, gossip_option_id(ROOT_MENU, waiting), waiting, 0, text, 0, 0, None, None)
    )
    for index, mentor_class in enumerate(MANA_CLASSES):
        menu = class_menu(index)
        for option, spell in enumerate(spells_of(mentor_class)):
            options.append(
                (
                    menu,
                    gossip_option_id(menu, option),
                    option,
                    0,
                    option_text(spell),
                    0,
                    spell.price,
                    box_text(spell),
                    spell.spell_id,
                )
            )
    return (
        "-- Its menus: the classes, then each class's spells (the body is the default greeting).\n"
        "-- creature_template_gossip opens the first one: without it the core plays the greeting\n"
        "-- and shows no menu.\n"
        + _insert(
            "creature_template_gossip",
            ("CreatureID", "MenuID", "VerifiedBuild"),
            [(ENTRY, ROOT_MENU, 0)],
        )
        + _insert("gossip_menu", ("MenuID", "TextID", "VerifiedBuild"), menus)
        + _insert("gossip_menu_option", option_columns, options)
    )


def _condition(
    menu: int, option: int, kind: int, value1: int, value2: int, negative: bool, comment: str
) -> tuple[object, ...]:
    return (
        CONDITION_SOURCE_GOSSIP_OPTION,
        menu,
        option,
        0,
        0,
        kind,
        0,
        value1,
        value2,
        0,
        "",
        1 if negative else 0,
        0,
        0,
        "",
        comment,
    )


def _conditions() -> str:
    rows: list[tuple[object, ...]] = []
    mana = _mask(MANA_CLASSES)
    for index, mentor_class in enumerate(MANA_CLASSES):
        name = mentor_class.name
        rows.append(
            _condition(
                ROOT_MENU,
                index,
                CONDITION_CLASS,
                mana,
                0,
                False,
                f"The Mentor - {name} spells - only for a class with mana",
            )
        )
        rows.append(
            _condition(
                ROOT_MENU,
                index,
                CONDITION_CLASS,
                mentor_class.mask,
                0,
                True,
                f"The Mentor - {name} spells - not for a {name.lower()}",
            )
        )
    rows.append(
        _condition(
            ROOT_MENU,
            len(MANA_CLASSES),
            CONDITION_CLASS,
            _mask(WAITING_CLASSES),
            0,
            False,
            "The Mentor - nothing yet - only for a class without mana",
        )
    )
    for index, mentor_class in enumerate(MANA_CLASSES):
        for option, spell in enumerate(spells_of(mentor_class)):
            menu = class_menu(index)
            rows.append(
                _condition(
                    menu,
                    option,
                    CONDITION_LEVEL,
                    spell.level,
                    COMP_TYPE_HIGH_EQ,
                    False,
                    f"The Mentor - {spell.name} - from level {spell.level}",
                )
            )
            rows.append(
                _condition(
                    menu,
                    option,
                    CONDITION_SPELL,
                    spell.spell_id,
                    0,
                    True,
                    f"The Mentor - {spell.name} - not once known",
                )
            )
    columns = (
        "SourceTypeOrReferenceId",
        "SourceGroup",
        "SourceEntry",
        "SourceId",
        "ElseGroup",
        "ConditionTypeOrReference",
        "ConditionTarget",
        "ConditionValue1",
        "ConditionValue2",
        "ConditionValue3",
        "ConditionStringValue1",
        "NegativeCondition",
        "ErrorType",
        "ErrorTextId",
        "ScriptName",
        "Comment",
    )
    return "-- Who sees which option\n" + _insert("conditions", columns, rows)


HEADER = """\
-- Yu'lon: WoW Forever Unbound's Mentor. Generated by `python -m yulon.forever_unbound_sql`
-- from yulon/forever_unbound_catalog.py; do not edit by hand.
--
-- The Mentor teaches a character spells of other classes, to every class with mana, for the price
-- the spell's own class trainers charge. Its script (npc_yulon_mentor, in Yu'lon's server image)
-- takes the option's BoxMoney, then teaches the option's SpellID. Only Yu'lon's reserved ids are
-- touched (3100001-3100020 and 3100100-3100399), deleted first, so the file can be applied again;
-- that also removes phase 1's server-side teach spells and SmartAI rows.
--
-- The multi-class design is Wrath Unbound's (DaddyCool, Dad's MMO Lab). ForeverCore is advocaite's
-- Forever core on TrinityCore, with Karrz's PlayerbotV2 bots.

"""


def render() -> str:
    """The whole SQL file, with LF line endings."""
    return HEADER + "\n".join((_deletes(), _creature(), _menus(), _conditions()))


def main(argv: Sequence[str]) -> int:
    """Write the rendering to the shipped file, or to the one path given."""
    target = Path(argv[0]) if argv else SHIPPED
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(render().encode("utf-8"))
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
