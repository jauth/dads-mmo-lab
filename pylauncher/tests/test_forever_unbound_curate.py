"""The Mentor's curation rules, on small in-memory trainer rows and spell facts.

The tool itself runs only on a developer's machine (it needs a world database export and the
client's tables); these tests pin what each rule does.
"""

from __future__ import annotations

import pytest

from yulon.forever_unbound_catalog import HUNTER, MAGE, PRIEST
from yulon.forever_unbound_curate import (
    PHASE1,
    CurationError,
    Effect,
    SpellFacts,
    TrainerRow,
    check_phase1,
    curate,
    render,
)

MAGE_ID = MAGE.class_id


def _row(spell_id: int, level: int, previous: int = 0, class_id: int = MAGE_ID) -> TrainerRow:
    return TrainerRow(class_id, spell_id, level, level * 10, previous, 1)


def _facts(**named: SpellFacts) -> dict[int, SpellFacts]:
    return {int(key.removeprefix("s")): value for key, value in named.items()}


def _mana(name: str) -> SpellFacts:
    return SpellFacts(name, powers={0})


def _kept(rows: list[TrainerRow], facts: dict[int, SpellFacts]) -> list[tuple[int, int, int]]:
    return [(r.spell_id, r.rank, r.previous) for r in curate(rows, facts).rows]


def _why(rows: list[TrainerRow], facts: dict[int, SpellFacts]) -> list[tuple[int, str]]:
    return [(e.spell_id, e.reason) for e in curate(rows, facts).excluded]


def test_a_mana_line_is_kept_with_its_ranks() -> None:
    rows = [_row(1001, 4), _row(1002, 10, 1001), _row(1003, 18, 1002)]
    facts = _facts(s1001=_mana("Bolt"), s1002=_mana("Bolt"), s1003=_mana("Bolt"))
    assert _kept(rows, facts) == [(1001, 1, 0), (1002, 2, 1001), (1003, 3, 1002)]
    kept = curate(rows, facts).rows
    assert [(r.level, r.price) for r in kept] == [(4, 40), (10, 100), (18, 180)]


def test_level_zero_becomes_one() -> None:
    rows = [_row(1001, 0)]
    assert curate(rows, _facts(s1001=_mana("Bolt"))).rows[0].level == 1


def test_a_spell_without_power_or_costing_health_is_kept() -> None:
    rows = [_row(1001, 4), _row(1002, 6)]
    facts = _facts(s1001=SpellFacts("Track"), s1002=SpellFacts("Tap", powers={-2}))
    assert [k[0] for k in _kept(rows, facts)] == [1001, 1002]


@pytest.mark.parametrize(
    ("facts", "reason"),
    [
        (SpellFacts("Strike", powers={1}), "power"),
        (SpellFacts("Maul", stance_mask=16), "form or stance"),
        (SpellFacts("Form", effects=[Effect(6, 36, (1, 0))]), "form or stance"),
        (SpellFacts("Totem", totem_category=2), "totem"),
        (SpellFacts("Totem", effects=[Effect(28, 0, (41, 0))]), "totem"),
        (SpellFacts("Call", effects=[Effect(56, 0, (32, 0))]), "pet"),
        (SpellFacts("Mend", effects=[Effect(6, 8, (5, 0))]), "pet"),
        (SpellFacts("Shot", powers={0}, weapon_mask=(1 << 2) | (1 << 18)), "ranged weapon"),
        (SpellFacts("Plate", effects=[Effect(60, 0, (0, 0))]), "armor or weapon skill"),
    ],
)
def test_each_rule_leaves_its_line_out(facts: SpellFacts, reason: str) -> None:
    assert _why([_row(1001, 4)], {1001: facts}) == [(1001, reason)]


def test_a_form_mask_that_also_allows_no_form_is_kept() -> None:
    facts = {1001: SpellFacts("Rebirth", powers={0}, stance_mask=1 << 30, allows_no_form=True)}
    assert _kept([_row(1001, 20)], facts) == [(1001, 1, 0)]


def test_a_melee_or_any_weapon_is_not_a_ranged_weapon() -> None:
    facts = {1001: SpellFacts("Strike", powers={0}, weapon_mask=(1 << 2) | (1 << 7))}
    assert _kept([_row(1001, 4)], facts) == [(1001, 1, 0)]


def test_one_bad_rank_drops_the_whole_line() -> None:
    rows = [_row(1001, 4), _row(1002, 10, 1001), _row(1003, 18, 1002)]
    facts = _facts(s1001=_mana("Bolt"), s1002=SpellFacts("Bolt", powers={3}), s1003=_mana("Bolt"))
    assert _kept(rows, facts) == []
    assert _why(rows, facts) == [(1001, "power")]


def test_a_first_rank_no_trainer_teaches_is_a_talent_or_quest() -> None:
    rows = [_row(1002, 20, 9999), _row(1003, 30, 1002)]
    facts = _facts(s1002=_mana("Pyro"), s1003=_mana("Pyro"))
    assert _kept(rows, facts) == []
    assert _why(rows, facts) == [(1002, "talent or quest")]


def test_a_starting_spell_starts_its_line() -> None:
    """Fireball rank 1 (133) is no trainer's, but the catalog's starting spells include it."""
    rows = [_row(143, 6, 133), _row(145, 12, 143)]
    facts = _facts(s133=_mana("Fireball"), s143=_mana("Fireball"), s145=_mana("Fireball"))
    assert _kept(rows, facts) == [(143, 2, 133), (145, 3, 143)]


def test_a_starting_spell_of_another_class_does_not_start_a_line() -> None:
    rows = [_row(143, 6, 133, class_id=PRIEST.class_id)]
    facts = _facts(s133=_mana("Fireball"), s143=_mana("Fireball"))
    assert _why(rows, facts) == [(143, "talent or quest")]


def test_a_shared_spell_drops_its_line_for_every_class() -> None:
    rows = [_row(1001, 20), _row(1001, 20, class_id=HUNTER.class_id)]
    assert _why(rows, {1001: _mana("Mail")}) == [(1001, "shared"), (1001, "shared")]


def test_above_level_60() -> None:
    rows = [_row(1001, 62), _row(1002, 40), _row(1003, 58, 1002), _row(1004, 70, 1003)]
    facts = _facts(s1001=_mana("A"), s1002=_mana("B"), s1003=_mana("B"), s1004=_mana("B"))
    result = curate(rows, facts)
    assert [(e.spell_id, e.reason) for e in result.excluded] == [(1001, "above level 60")]
    assert [r.spell_id for r in result.rows] == [1002, 1003], "ranks above 60 drop off the end"


def test_a_denied_spell_drops_its_line() -> None:
    """Aspect of the Hawk is on the catalog's deny list."""
    rows = [_row(13165, 10, class_id=HUNTER.class_id)]
    reasons = _why(rows, {13165: SpellFacts("Aspect of the Hawk")})
    assert reasons == [(13165, "it only raises ranged attack power")]


def test_a_spell_the_client_does_not_know_drops_its_line() -> None:
    assert _why([_row(1001, 4)], {}) == [(1001, "not in the client's tables")]


def test_ranks_count_only_the_same_name() -> None:
    """Create Soulstone follows Drain Soul rank 1 but is its own rank 1."""
    rows = [_row(1120, 10), _row(693, 18, 1120), _row(8288, 24, 1120), _row(20752, 30, 693)]
    facts = _facts(
        s1120=_mana("Drain Soul"),
        s693=_mana("Create Soulstone"),
        s8288=_mana("Drain Soul"),
        s20752=_mana("Create Soulstone"),
    )
    ranks = {r.spell_id: r.rank for r in curate(rows, facts).rows}
    assert ranks == {1120: 1, 693: 1, 8288: 2, 20752: 2}


def test_phase1_rows_must_come_out_the_same() -> None:
    spell_id, name, level, price = PHASE1[0]
    facts = {spell_id: _mana(name)}
    result = curate([TrainerRow(2, spell_id, level, price + 1, 0, 1)], facts)
    with pytest.raises(CurationError, match=name):
        check_phase1(result, facts)


def test_the_rendering_is_a_module_with_both_lists() -> None:
    rows = [_row(1001, 4), _row(1002, 10, 1001), _row(1004, 4)]
    facts = _facts(s1001=_mana('Hunter\'s "Mark"'), s1002=_mana('Hunter\'s "Mark"'))
    namespace: dict[str, object] = {}
    exec(render(curate(rows, facts)), namespace)  # noqa: S102 - our own generated text
    assert namespace["ROWS"] == (
        (1001, 'Hunter\'s "Mark"', MAGE_ID, 4, 40, 1, 0),
        (1002, 'Hunter\'s "Mark"', MAGE_ID, 10, 100, 2, 1001),
    )
    assert namespace["EXCLUDED"] == ((1004, "spell 1004", MAGE_ID, "not in the client's tables"),)
