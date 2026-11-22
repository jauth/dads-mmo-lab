"""Build the Mentor's spell list from the realm's trainer data and the client's spell tables.

A developer tool, never run by the app or the tests: it needs a world database export and the
client's tables, which only a running WoW Forever (Unbound) install has. It writes
`forever_unbound_spells.py`, the generated rows `forever_unbound_catalog` reads. Run it again after
a ForeverCore or client update, then re-render the SQL (`python -m yulon.forever_unbound_sql`).

    python -m yulon.forever_unbound_curate --trainers trainers.tsv --db2 <folder> [--out <file>]

`--trainers` is this query's output (`mysql -N -B world`), run on 2026-11-20 against
TDB_full_forever_2026_10_14 with ForeverCore 0.1.36's updates. A class's trainers are the ones that
teach its anchor spell, a level-1 spell only that class's trainers teach:

    SELECT a.class_id, t.SpellId, MIN(t.ReqLevel), MIN(t.MoneyCost), MAX(t.ReqAbility1),
           COUNT(DISTINCT t.TrainerId)
    FROM (SELECT 2 AS class_id, 465 AS anchor UNION ALL SELECT 3, 1494 UNION ALL SELECT 5, 1243
          UNION ALL SELECT 7, 8017 UNION ALL SELECT 8, 1459 UNION ALL SELECT 9, 348
          UNION ALL SELECT 11, 1126) a
    JOIN trainer_spell k ON k.SpellId = a.anchor
    JOIN trainer_spell t ON t.TrainerId = k.TrainerId
    GROUP BY a.class_id, t.SpellId ORDER BY a.class_id, t.SpellId;

`--db2` is a folder holding the client's `SpellName`, `SpellPower`, `SpellShapeshift`,
`SpellTotems`, `SpellEquippedItems`, `SpellEffect` and `SpellMisc` tables, copied out of the
install's data volume (`/srv/data/dbc/enUS/`). They are read where they are and never committed.

The rules, in order. A spell line is a chain of ranks linked by the trainers' `ReqAbility1`:
  1. A line whose first trainer-taught rank needs a rank no trainer of its class teaches is left
     out ("talent or quest"), unless that rank is one of the catalog's `STARTING_SPELLS`.
  2. A line with a spell more than one class's trainers teach is left out ("shared"), and so is a
     line whose rank 1 is above level 60. Ranks above 60 are dropped from the end of a line.
  3. A line is left out if any of its ranks: costs a power other than mana or health ("power"),
     needs a form or stance ("form or stance"), is or needs a totem ("totem"), summons, targets or
     brings back a pet ("pet"), needs a ranged weapon ("ranged weapon"), or teaches a skill
     ("armor or weapon skill").
  4. A line holding a spell in the catalog's `DENIED` list is left out, with that reason.
Health counts as no power: no class lacks it, and Life Tap (health) casts on every class.

The client's tables do not name their columns, so the tool checks the columns it reads against
spells whose values it knows (`_check_columns`), and checks its result against phase 1's 30 rows,
which were read by hand and cast in game (`PHASE1`). It refuses to write if either check fails.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from yulon.forever_unbound_catalog import DENIED, MANA_CLASSES, STARTING_SPELLS
from yulon.wdc5 import Wdc5Table

GENERATED = Path(__file__).resolve().with_name("forever_unbound_spells.py")
MAX_LEVEL = 60

POWER_MANA = 0
POWER_HEALTH = -2
ALLOWED_POWERS = frozenset({POWER_MANA, POWER_HEALTH})

AURA_SHAPESHIFT = 36
ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED = 0x00080000
"""`SPELL_ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED_CASTER_FORM`: a form mask that also allows no form."""
TOTEM_TARGETS = frozenset({41, 42, 43, 44})
"""The four totem slots a totem is summoned into (`TARGET_DEST_CASTER_FRONT_LEFT` and so on)."""
TARGET_UNIT_PET = 5
PET_EFFECTS = frozenset({55, 56, 101, 102, 109})
"""Tame creature, summon pet, feed pet, dismiss pet, resurrect pet."""
SKILL_EFFECTS = frozenset({44, 60, 118})
"""Skill step, proficiency, skill."""
ITEM_CLASS_WEAPON = 2
RANGED_SUBCLASSES = (1 << 2) | (1 << 3) | (1 << 16) | (1 << 18) | (1 << 19)
"""Bow, gun, thrown, crossbow and wand."""

PHASE1: tuple[tuple[int, str, int, int], ...] = (
    (465, "Devotion Aura", 1, 10),
    (19740, "Blessing of Might", 4, 100),
    (498, "Divine Protection", 6, 100),
    (853, "Hammer of Justice", 8, 100),
    (1152, "Purify", 8, 100),
    (1494, "Track Beasts", 1, 10),
    (13163, "Aspect of the Monkey", 4, 100),
    (1130, "Hunter's Mark", 6, 100),
    (1243, "Power Word: Fortitude", 1, 10),
    (589, "Shadow Word: Pain", 4, 100),
    (17, "Power Word: Shield", 6, 100),
    (139, "Renew", 8, 200),
    (8017, "Rockbiter Weapon", 1, 10),
    (8042, "Earth Shock", 4, 100),
    (324, "Lightning Shield", 8, 100),
    (370, "Purge", 12, 700),
    (1459, "Arcane Intellect", 1, 10),
    (116, "Frostbolt", 4, 100),
    (2136, "Fire Blast", 6, 100),
    (5143, "Arcane Missiles", 8, 200),
    (348, "Immolate", 1, 10),
    (172, "Corruption", 4, 100),
    (702, "Curse of Weakness", 4, 100),
    (1454, "Life Tap", 6, 100),
    (5782, "Fear", 8, 200),
    (1126, "Mark of the Wild", 1, 10),
    (8921, "Moonfire", 4, 100),
    (774, "Rejuvenation", 4, 100),
    (467, "Thorns", 6, 100),
    (339, "Entangling Roots", 8, 200),
)
"""Phase 1's rows (spell, name, level, price), read by hand and cast in game on 2026-11-19."""


class CurationError(RuntimeError):
    """The inputs are not what the tool expects; nothing is written."""


@dataclass(frozen=True, slots=True)
class TrainerRow:
    """One spell one class's trainers teach: level, price and the rank it needs."""

    class_id: int
    spell_id: int
    level: int
    price: int
    previous: int
    trainers: int


@dataclass(frozen=True, slots=True)
class Effect:
    """One effect of a spell: its kind, its aura and its two implicit targets."""

    effect: int
    aura: int
    targets: tuple[int, int]


@dataclass(slots=True)
class SpellFacts:
    """What the client's tables say about one spell, as far as the rules need it."""

    name: str
    powers: set[int] = field(default_factory=set)
    stance_mask: int = 0
    allows_no_form: bool = False
    effects: list[Effect] = field(default_factory=list)
    totem_category: int = 0
    weapon_mask: int = 0


@dataclass(frozen=True, slots=True)
class Row:
    """A row of the generated list."""

    spell_id: int
    name: str
    class_id: int
    level: int
    price: int
    rank: int
    previous: int


@dataclass(frozen=True, slots=True)
class Excluded:
    """A line left out: its first trainer-taught spell, name, class and why."""

    spell_id: int
    name: str
    class_id: int
    reason: str


@dataclass(frozen=True, slots=True)
class Curation:
    """The rules' result: the rows kept and the lines left out, by class."""

    rows: tuple[Row, ...]
    excluded: tuple[Excluded, ...]


def read_trainers(path: Path) -> list[TrainerRow]:
    """The `--trainers` TSV, one row per class and spell."""
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            TrainerRow(*(int(v) for v in line[:6])) for line in csv.reader(handle, delimiter="\t")
        ]


def _signed(value: int) -> int:
    return value - (1 << 32) if value & 0x80000000 else value


def read_facts(folder: Path) -> dict[int, SpellFacts]:
    """The rules' facts for every spell the client names, from the tables in `folder`.

    Column numbers are this client's (70707/70888); `_check_columns` proves them on known spells.
    """
    names = Wdc5Table.read(folder / "SpellName.db2")
    facts = {row_id: SpellFacts(row.string(0)) for row_id, row in names.rows.items()}

    def spell(spell_id: int) -> SpellFacts | None:
        return facts.get(spell_id)

    for row in Wdc5Table.read(folder / "SpellPower.db2").rows.values():
        if (found := spell(row.parent)) is not None:
            found.powers.add(_signed(row.value(11)))
    for row in Wdc5Table.read(folder / "SpellShapeshift.db2").rows.values():
        if (found := spell(row.value(0))) is not None:
            found.stance_mask |= row.values(3)[0] | row.values(3)[1]
    for row in Wdc5Table.read(folder / "SpellMisc.db2").rows.values():
        if (found := spell(row.parent)) is not None:
            found.allows_no_form = bool(row.values(0)[2] & ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED)
    for row in Wdc5Table.read(folder / "SpellEffect.db2").rows.values():
        if (found := spell(row.parent)) is not None:
            targets = row.values(28)
            found.effects.append(Effect(row.value(3), row.value(0), (targets[0], targets[1])))
    for row in Wdc5Table.read(folder / "SpellTotems.db2").rows.values():
        if (found := spell(row.value(0))) is not None:
            found.totem_category |= row.values(1)[0] & 0xFFFF
    for row in Wdc5Table.read(folder / "SpellEquippedItems.db2").rows.values():
        if (found := spell(row.value(0))) is not None and row.value(1) == ITEM_CLASS_WEAPON:
            found.weapon_mask |= row.value(3)
    return facts


def _check_columns(facts: Mapping[int, SpellFacts]) -> None:
    """Fail unless the columns `read_facts` used hold what it took them for, on known spells."""
    checks: tuple[tuple[int, str, bool], ...] = (
        (116, "Frostbolt costs mana", facts[116].powers == {POWER_MANA}),
        (78, "Heroic Strike costs rage", facts[78].powers == {1}),
        (1752, "Sinister Strike costs energy", facts[1752].powers == {3}),
        (1454, "Life Tap costs health", facts[1454].powers == {POWER_HEALTH}),
        (6807, "Maul needs bear form", bool(facts[6807].stance_mask)),
        (20484, "Rebirth casts with no form", facts[20484].allows_no_form),
        (
            768,
            "Cat Form is a shapeshift",
            any(e.aura == AURA_SHAPESHIFT for e in facts[768].effects),
        ),
        (3599, "Searing Totem is summoned into a totem slot", _is_totem(facts[3599])),
        (136, "Mend Pet targets the pet", _is_pet(facts[136])),
        (883, "Call Pet summons a pet", _is_pet(facts[883])),
        (750, "Plate Mail teaches a skill", _is_skill(facts[750])),
        (3044, "Arcane Shot needs a ranged weapon", _is_ranged(facts[3044])),
        (116, "Frostbolt needs nothing special", _reason(facts[116]) is None),
    )
    failed = [f"{spell_id}: {what}" for spell_id, what, ok in checks if not ok]
    if failed:
        raise CurationError("the client tables' columns are not as expected: " + "; ".join(failed))


def _is_totem(facts: SpellFacts) -> bool:
    return bool(facts.totem_category) or any(
        t in TOTEM_TARGETS for e in facts.effects for t in e.targets
    )


def _is_pet(facts: SpellFacts) -> bool:
    return any(e.effect in PET_EFFECTS or TARGET_UNIT_PET in e.targets for e in facts.effects)


def _is_skill(facts: SpellFacts) -> bool:
    return any(e.effect in SKILL_EFFECTS for e in facts.effects)


def _is_ranged(facts: SpellFacts) -> bool:
    return bool(facts.weapon_mask) and not facts.weapon_mask & ~RANGED_SUBCLASSES


def _reason(facts: SpellFacts) -> str | None:
    """Rule 3's reason to leave a spell's line out, or None."""
    if facts.powers - ALLOWED_POWERS:
        return "power"
    if (facts.stance_mask and not facts.allows_no_form) or any(
        e.aura == AURA_SHAPESHIFT for e in facts.effects
    ):
        return "form or stance"
    if _is_totem(facts):
        return "totem"
    if _is_pet(facts):
        return "pet"
    if _is_ranged(facts):
        return "ranged weapon"
    if _is_skill(facts):
        return "armor or weapon skill"
    return None


def curate(trainers: Iterable[TrainerRow], facts: Mapping[int, SpellFacts]) -> Curation:
    """Apply the rules to the trainer rows: the rows kept and the lines left out."""
    mana = {c.class_id for c in MANA_CLASSES}
    by_class: dict[int, dict[int, TrainerRow]] = defaultdict(dict)
    teachers: dict[int, set[int]] = defaultdict(set)
    for row in trainers:
        if row.class_id in mana:
            by_class[row.class_id][row.spell_id] = row
            teachers[row.spell_id].add(row.class_id)
    starting = {(s.class_id, s.spell_id): s for s in STARTING_SPELLS}
    rows: list[Row] = []
    excluded: list[Excluded] = []
    for mentor_class in MANA_CLASSES:
        class_id = mentor_class.class_id
        taught = by_class.get(class_id, {})
        children: dict[int, list[int]] = defaultdict(list)
        roots: list[int] = []
        for spell_id, row in sorted(taught.items()):
            if row.previous and (row.previous in taught or (class_id, row.previous) in starting):
                children[row.previous].append(spell_id)
            else:
                roots.append(spell_id)
        for starter in STARTING_SPELLS:
            if starter.class_id == class_id and children.get(starter.spell_id):
                roots.append(starter.spell_id)

        def name(spell_id: int) -> str:
            found = facts.get(spell_id)
            return found.name if found else f"spell {spell_id}"

        for root in roots:
            root_row = taught.get(root)
            if root_row is not None and root_row.previous:
                excluded.append(Excluded(root, name(root), class_id, "talent or quest"))
                continue
            line = _walk(root, children)
            reason = _line_reason(line, root, class_id, taught, teachers, facts)
            if reason is not None:
                excluded.append(Excluded(root, name(root), class_id, reason))
                continue
            rows.extend(_line_rows(line, root, class_id, taught, starting, facts))
    return Curation(tuple(rows), tuple(excluded))


def _walk(root: int, children: Mapping[int, list[int]]) -> list[int]:
    """The line from `root`: every spell that follows it, root first, each after its rank before."""
    line = [root]
    for spell_id in line:
        line.extend(children.get(spell_id, ()))
    return line


def _line_reason(
    line: Sequence[int],
    root: int,
    class_id: int,
    taught: Mapping[int, TrainerRow],
    teachers: Mapping[int, set[int]],
    facts: Mapping[int, SpellFacts],
) -> str | None:
    root_row = taught.get(root)
    if root_row is not None and root_row.level > MAX_LEVEL:
        return "above level 60"
    for spell_id in line:
        if len(teachers.get(spell_id, {class_id})) > 1:
            return "shared"
        if spell_id in DENIED:
            return DENIED[spell_id]
        found = facts.get(spell_id)
        if found is None:
            return "not in the client's tables"
        reason = _reason(found)
        if reason is not None:
            return reason
    return None


def _line_rows(
    line: Sequence[int],
    root: int,
    class_id: int,
    taught: Mapping[int, TrainerRow],
    starting: Mapping[tuple[int, int], object],
    facts: Mapping[int, SpellFacts],
) -> list[Row]:
    previous_of: dict[int, int] = {}
    for spell_id in line:
        if spell_id != root:
            previous_of[spell_id] = taught[spell_id].previous
    kept: list[Row] = []
    dropped: set[int] = set()
    for spell_id in line:
        if (class_id, spell_id) in starting:
            continue
        row = taught[spell_id]
        if row.level > MAX_LEVEL or previous_of.get(spell_id) in dropped:
            dropped.add(spell_id)
            continue
        name = facts[spell_id].name
        rank = 1
        ancestor = previous_of.get(spell_id)
        while ancestor is not None:
            if facts[ancestor].name == name:
                rank += 1
            ancestor = previous_of.get(ancestor)
        kept.append(Row(spell_id, name, class_id, max(1, row.level), row.price, rank, row.previous))
    return kept


def check_phase1(curation: Curation, facts: Mapping[int, SpellFacts]) -> None:
    """Fail unless every phase 1 row comes out with the same name, level and price."""
    kept = {row.spell_id: row for row in curation.rows}
    problems: list[str] = []
    for spell_id, name, level, price in PHASE1:
        row = kept.get(spell_id)
        if row is None:
            why = next((e.reason for e in curation.excluded if e.spell_id == spell_id), "missing")
            problems.append(f"{name} ({spell_id}) is not kept: {why}")
        elif (row.name, row.level, row.price) != (name, level, price):
            problems.append(f"{name} ({spell_id}) came out as {row}")
    for starter in STARTING_SPELLS:
        found = facts.get(starter.spell_id)
        if found is None or found.name != starter.name:
            problems.append(
                f"starting spell {starter.spell_id} is not {starter.name} in the client"
            )
    if problems:
        raise CurationError("phase 1's rows do not come out the same: " + "; ".join(problems))


def render(curation: Curation) -> str:
    """The generated module's text."""
    lines = [
        '"""The Mentor\'s generated spell rows. Do not edit by hand: regenerate them with',
        "`python -m yulon.forever_unbound_curate`, which holds the rules.",
        "`forever_unbound_catalog` reads them.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "ROWS: tuple[tuple[int, str, int, int, int, int, int], ...] = (",
    ]
    for r in curation.rows:
        values = (r.spell_id, json.dumps(r.name), r.class_id, r.level, r.price, r.rank, r.previous)
        lines += _tuple_lines(values)
    lines += [
        ")",
        '"""(spell id, name, class id, level, price in copper, rank, previous rank or 0)."""',
        "",
        "EXCLUDED: tuple[tuple[int, str, int, str], ...] = (",
    ]
    for e in curation.excluded:
        lines += _tuple_lines((e.spell_id, json.dumps(e.name), e.class_id, json.dumps(e.reason)))
    lines += [
        ")",
        '"""Lines left out: (first trainer-taught spell id, name, class id, reason)."""',
        "",
    ]
    return "\n".join(lines)


LINE_LIMIT = 100
"""The repo's line length (black and ruff): a longer tuple is split one value per line, as black
would, so the generated file passes `black --check` unchanged."""


def _tuple_lines(values: Sequence[object]) -> list[str]:
    one = f"    ({', '.join(str(v) for v in values)}),"
    if len(one) <= LINE_LIMIT:
        return [one]
    return ["    ("] + [f"        {v}," for v in values] + ["    ),"]


def main(argv: Sequence[str]) -> int:
    """Curate, check, write the generated module, and print a summary and `.learn` batches."""
    parser = argparse.ArgumentParser(prog="python -m yulon.forever_unbound_curate")
    parser.add_argument("--trainers", type=Path, required=True)
    parser.add_argument("--db2", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=GENERATED)
    args = parser.parse_args(argv)
    facts = read_facts(args.db2)
    _check_columns(facts)
    curation = curate(read_trainers(args.trainers), facts)
    check_phase1(curation, facts)
    args.out.write_bytes(render(curation).encode("utf-8"))
    print(f"wrote {args.out}")
    for mentor_class in MANA_CLASSES:
        mine = [r for r in curation.rows if r.class_id == mentor_class.class_id]
        firsts = [s.spell_id for s in STARTING_SPELLS if s.class_id == mentor_class.class_id]
        firsts += [r.spell_id for r in mine if r.previous == 0]
        left_out = sum(1 for e in curation.excluded if e.class_id == mentor_class.class_id)
        print(
            f"{mentor_class.name}: {len(firsts)} lines, {len(mine)} trainer rows, "
            f"{left_out} left out"
        )
        print("  .learn " + " | .learn ".join(str(spell_id) for spell_id in firsts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
