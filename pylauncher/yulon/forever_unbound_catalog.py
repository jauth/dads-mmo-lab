"""The spells the Mentor teaches on WoW Forever Unbound, v1: the data, and nothing else.

A WoW Forever Unbound character keeps its own class and may learn other classes' spells from
the Mentor, an NPC in each capital. In v1 every spell is taught free, and only to classes that
have mana. The server checks power per class (ForeverCore's `Spell::CheckPower`), so a warrior or
rogue cannot cast a mana spell; that was tested on a warrior with "Not enough mana", 2026-11-19.

Every row is a rank-1 spell its class's trainers teach on this realm. `level` is those trainers'
`ReqLevel` in the world database's `trainer_spell` (TDB_full_forever_2026_10_14 with ForeverCore
0.1.36's updates), raised to 1 where it is 0. Each spell's class was confirmed by grouping spells
by the set of trainers that teach them. Left out on purpose:
  * spells a character starts with: no trainer teaches them
  * later ranks
  * stances, forms, pets and totems: they lean on another class's systems
  * shots and stings that need a ranged weapon
  * Aspect of the Hawk: it only raises ranged attack power

`forever_unbound_sql` renders this list into the world SQL the server applies. The design is
Wrath Unbound's (DaddyCool, Dad's MMO Lab), whose 3.3.5 spell lists do not apply here.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    """One spell the Mentor teaches: its id, its name in the menu, its class and its level."""

    spell_id: int
    name: str
    class_id: int
    level: int


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
"""The classes without mana: in v1 the Mentor has nothing for them yet."""

SPELLS: tuple[MentorSpell, ...] = (
    MentorSpell(465, "Devotion Aura", PALADIN.class_id, 1),
    MentorSpell(19740, "Blessing of Might", PALADIN.class_id, 4),
    MentorSpell(498, "Divine Protection", PALADIN.class_id, 6),
    MentorSpell(853, "Hammer of Justice", PALADIN.class_id, 8),
    MentorSpell(1152, "Purify", PALADIN.class_id, 8),
    MentorSpell(1494, "Track Beasts", HUNTER.class_id, 1),
    MentorSpell(13163, "Aspect of the Monkey", HUNTER.class_id, 4),
    MentorSpell(1130, "Hunter's Mark", HUNTER.class_id, 6),
    MentorSpell(1243, "Power Word: Fortitude", PRIEST.class_id, 1),
    MentorSpell(589, "Shadow Word: Pain", PRIEST.class_id, 4),
    MentorSpell(17, "Power Word: Shield", PRIEST.class_id, 6),
    MentorSpell(139, "Renew", PRIEST.class_id, 8),
    MentorSpell(8017, "Rockbiter Weapon", SHAMAN.class_id, 1),
    MentorSpell(8042, "Earth Shock", SHAMAN.class_id, 4),
    MentorSpell(324, "Lightning Shield", SHAMAN.class_id, 8),
    MentorSpell(370, "Purge", SHAMAN.class_id, 12),
    MentorSpell(1459, "Arcane Intellect", MAGE.class_id, 1),
    MentorSpell(116, "Frostbolt", MAGE.class_id, 4),
    MentorSpell(2136, "Fire Blast", MAGE.class_id, 6),
    MentorSpell(5143, "Arcane Missiles", MAGE.class_id, 8),
    MentorSpell(348, "Immolate", WARLOCK.class_id, 1),
    MentorSpell(172, "Corruption", WARLOCK.class_id, 4),
    MentorSpell(702, "Curse of Weakness", WARLOCK.class_id, 4),
    MentorSpell(1454, "Life Tap", WARLOCK.class_id, 6),
    MentorSpell(5782, "Fear", WARLOCK.class_id, 8),
    MentorSpell(1126, "Mark of the Wild", DRUID.class_id, 1),
    MentorSpell(8921, "Moonfire", DRUID.class_id, 4),
    MentorSpell(774, "Rejuvenation", DRUID.class_id, 4),
    MentorSpell(467, "Thorns", DRUID.class_id, 6),
    MentorSpell(339, "Entangling Roots", DRUID.class_id, 8),
)
"""Every spell the Mentor teaches, grouped by class in `MANA_CLASSES` order, then by level."""


def spells_of(mentor_class: MentorClass) -> tuple[MentorSpell, ...]:
    """The spells the Mentor teaches from `mentor_class`, in menu order."""
    return tuple(spell for spell in SPELLS if spell.class_id == mentor_class.class_id)
