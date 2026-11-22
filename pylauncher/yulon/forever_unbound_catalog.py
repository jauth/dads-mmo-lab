"""The spells the Mentor teaches on WoW Forever Unbound: the data, and nothing else.

A WoW Forever Unbound character keeps its own class and may learn other classes' spells from
the Mentor, an NPC in each capital, for the price the spell's own class trainers charge. Only
classes that have mana are taught. The server checks power per class (ForeverCore's
`Spell::CheckPower`), so a warrior or rogue cannot cast a mana spell; that was tested on a warrior
with "Not enough mana", 2026-11-19.

The list is every rank the class trainers teach up to level 60, for every spell line that passes
the curation rules. `forever_unbound_curate` builds it from this realm's `world.trainer_spell` and
the client's own spell tables, and writes it to `forever_unbound_spells`; its docstring has the
rules, the query and the date. The rows hold:
  * `level`: the trainers' `ReqLevel`, raised to 1 where it is 0.
  * `price`: the trainers' `MoneyCost` in copper, the lowest where a spell's trainers disagree
    (Purge costs 700 or 800, Track Beasts 10 or 93).
  * `rank` and `previous`: the spell's place in its line, and the rank before it, from the
    trainers' `ReqAbility1`. The Mentor offers a rank above 1 only once the rank before it is known.

Two kinds of rows are kept here by hand:
  * `STARTING_SPELLS`: rank 1 of the starting spells later ranks build on. A character of another
    class never has them, and no trainer teaches them, so the Mentor teaches them at level 1 for
    `STARTING_PRICE`, what trainers charge for level-1 spells.
  * `DENIED`: spell lines the rules let through that must not be taught, each with its reason.

Each class's list is split in `BANDS` by the level of a line's rank 1, so no menu shows more than
32 options (ForeverCore asserts that limit; `worst_case_visible` counts it).

`forever_unbound_sql` renders this list into the world SQL the server applies. The design is
Wrath Unbound's (DaddyCool, Dad's MMO Lab), whose 3.3.5 spell lists do not apply here.
"""

from __future__ import annotations

from dataclasses import dataclass

from yulon.forever_unbound_spells import ROWS


@dataclass(frozen=True, slots=True)
class MentorClass:
    """One class as the Mentor names it, by the game's class id (`ChrClasses`)."""

    class_id: int
    name: str

    @property
    def mask(self) -> int:
        """The class's bit in a class mask, as `CONDITION_CLASS` reads it."""
        return 1 << (self.class_id - 1)


@dataclass(frozen=True, slots=True)
class MentorSpell:
    """One spell the Mentor teaches: its id, name, class, level, price and place in its line.

    `price` is in copper: what the spell's own class trainers charge for it on this realm.
    `previous` is the spell id of the rank before this one, or None for a line's rank 1.
    """

    spell_id: int
    name: str
    class_id: int
    level: int
    price: int
    rank: int = 1
    previous: int | None = None


PALADIN = MentorClass(2, "Paladin")
HUNTER = MentorClass(3, "Hunter")
PRIEST = MentorClass(5, "Priest")
SHAMAN = MentorClass(7, "Shaman")
MAGE = MentorClass(8, "Mage")
WARLOCK = MentorClass(9, "Warlock")
DRUID = MentorClass(11, "Druid")
WARRIOR = MentorClass(1, "Warrior")
ROGUE = MentorClass(4, "Rogue")

MANA_CLASSES: tuple[MentorClass, ...] = (PALADIN, HUNTER, PRIEST, SHAMAN, MAGE, WARLOCK, DRUID)
"""The classes the Mentor teaches, and whose spells it teaches, in menu order."""

WAITING_CLASSES: tuple[MentorClass, ...] = (WARRIOR, ROGUE)
"""The classes without mana: the Mentor has nothing for them yet."""

STARTING_PRICE = 10
"""A starting spell's price in copper: what class trainers charge for their level-1 spells."""

STARTING_SPELLS: tuple[MentorSpell, ...] = (
    MentorSpell(635, "Holy Light", PALADIN.class_id, 1, STARTING_PRICE),
    # 21084, not 20154: the trainers' rank 2 (20287) requires 21084. Added 2026-11-20.
    MentorSpell(21084, "Seal of Righteousness", PALADIN.class_id, 1, STARTING_PRICE),
    MentorSpell(2973, "Raptor Strike", HUNTER.class_id, 1, STARTING_PRICE),
    MentorSpell(585, "Smite", PRIEST.class_id, 1, STARTING_PRICE),
    MentorSpell(2050, "Lesser Heal", PRIEST.class_id, 1, STARTING_PRICE),
    MentorSpell(403, "Lightning Bolt", SHAMAN.class_id, 1, STARTING_PRICE),
    MentorSpell(331, "Healing Wave", SHAMAN.class_id, 1, STARTING_PRICE),
    MentorSpell(133, "Fireball", MAGE.class_id, 1, STARTING_PRICE),
    MentorSpell(168, "Frost Armor", MAGE.class_id, 1, STARTING_PRICE),
    MentorSpell(686, "Shadow Bolt", WARLOCK.class_id, 1, STARTING_PRICE),
    MentorSpell(687, "Demon Skin", WARLOCK.class_id, 1, STARTING_PRICE),
    MentorSpell(5176, "Wrath", DRUID.class_id, 1, STARTING_PRICE),
    MentorSpell(5185, "Healing Touch", DRUID.class_id, 1, STARTING_PRICE),
)
"""Rank 1 of the starting spells whose later ranks the trainers teach, by class."""

DENIED: dict[int, str] = {
    13165: "it only raises ranged attack power",
    674: "armor or weapon skill",
    1098: "pet: the demon becomes the caster's pet",
    36936: "totem: it works on placed totems, and only shamans place them",
    66842: "totem: it places totems, and only shamans have them",
    437009: "totem: it works on placed totems, and only shamans place them",
}
"""Spell lines never taught, by any spell id in the line, with the reason."""

BANDS: tuple[tuple[int, int], ...] = ((1, 15), (16, 30), (31, 60))
"""Each class's list is split by the level of a line's rank 1: these are the bands, inclusive.

Two bands (1-30, 31-60) left the mage's first band at 35 lines, over `MENU_LIMIT`. With these three
no band of any class passes 21, and none is empty (2026-11-20)."""

MENU_LIMIT = 32
"""ForeverCore's `GOSSIP_MAX_MENU_ITEMS`: a menu with more visible options stops the server."""


def _generated() -> tuple[MentorSpell, ...]:
    return tuple(
        MentorSpell(spell_id, name, class_id, level, price, rank, previous or None)
        for spell_id, name, class_id, level, price, rank, previous in ROWS
    )


def _menu_order(spells: tuple[MentorSpell, ...]) -> tuple[MentorSpell, ...]:
    by_id = {spell.spell_id: spell for spell in spells}

    def chain(spell: MentorSpell) -> list[MentorSpell]:
        """`spell` and every rank before it, back to its line's rank 1."""
        found = [spell]
        while found[-1].previous is not None:
            found.append(by_id[found[-1].previous])
        return found

    order = [c.class_id for c in MANA_CLASSES]

    def key(spell: MentorSpell) -> tuple[int, int, str, int, int, int, int]:
        ranks = chain(spell)
        first = ranks[-1]
        # By depth, not rank: a spell that branches off (Greater Blessing of Might, rank 1 of its
        # name, follows Blessing of Might rank 6) must come after the rank it follows.
        return (
            order.index(spell.class_id),
            first.level,
            first.name,
            first.spell_id,
            len(ranks),
            spell.level,
            spell.spell_id,
        )

    return tuple(sorted(spells, key=key))


SPELLS: tuple[MentorSpell, ...] = _menu_order(STARTING_SPELLS + _generated())
"""Every spell the Mentor teaches, by class in `MANA_CLASSES` order, then by line, then by rank."""

SPELL_BY_ID: dict[int, MentorSpell] = {spell.spell_id: spell for spell in SPELLS}


def spells_of(mentor_class: MentorClass) -> tuple[MentorSpell, ...]:
    """The spells the Mentor teaches from `mentor_class`, in menu order."""
    return tuple(spell for spell in SPELLS if spell.class_id == mentor_class.class_id)


def first_rank(spell: MentorSpell) -> MentorSpell:
    """The rank 1 of `spell`'s line."""
    while spell.previous is not None:
        spell = SPELL_BY_ID[spell.previous]
    return spell


def band_of(spell: MentorSpell) -> int:
    """The index in `BANDS` of the band that holds `spell`'s line."""
    level = first_rank(spell).level
    for index, (low, high) in enumerate(BANDS):
        if low <= level <= high:
            return index
    raise ValueError(f"{spell.name} ({spell.spell_id}) starts at level {level}, outside every band")


def spells_in(mentor_class: MentorClass, band: int) -> tuple[MentorSpell, ...]:
    """The spells in one band of `mentor_class`'s list, in menu order."""
    return tuple(spell for spell in spells_of(mentor_class) if band_of(spell) == band)


def has_ranks(spell: MentorSpell) -> bool:
    """Whether `spell`'s line holds another rank of the same name, so its menu text names a rank."""
    if spell.rank > 1:
        return True
    return any(s.previous == spell.spell_id and s.name == spell.name for s in SPELLS)


def worst_case_visible(spells: tuple[MentorSpell, ...]) -> int:
    """The most options of `spells` one character can see at once, learning in rank order.

    A rank shows only once the rank before it is known, so each line shows at most one rank at a
    time, or one per branch where two spells follow the same rank. That is the number of spells
    that no other spell in the list follows.
    """
    followed = {spell.previous for spell in spells}
    return sum(1 for spell in spells if spell.spell_id not in followed)
