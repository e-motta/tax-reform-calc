"""The YAML is the source of the rates. These tests keep a citation on every figure."""

from decimal import Decimal

from app.engine.loader import load_rules


def test_shipped_rules_carry_a_source_and_an_as_of_date():
    rules = load_rules()
    assert rules.version == "2026-11-13"
    assert str(rules.manifest.as_of) == "2026-11-13"
    assert rules.manifest.estimates.source.strip()
    assert rules.manifest.estimates.tcu_source_url.startswith("https://")
    assert rules.manifest.estimates.statutory_review_cap == Decimal("0.265")

    for state in rules.states.states:
        assert state.source.strip(), state.uf
        if state.generalized_surcharge is not None:
            assert state.generalized_surcharge.source.strip()

    for category in rules.categories.categories:
        assert category.reduction_source.strip()
        if category.selective is not None:
            assert category.selective.source.strip()
        if category.iss_scenario_rate is not None:
            assert category.iss_source

    for year in rules.transition.years:
        assert year.source.strip()
        assert year.source_pt.strip()
    assert rules.interstate.source.strip()
    assert rules.regimes.icms_exclusion_source.strip()
    assert rules.regimes.iss_exclusion_source.strip()


def test_reference_pair_is_the_comite_gestor_estimate_not_the_tcu_figure():
    estimates = load_rules().manifest.estimates
    assert estimates.cbs_reference == Decimal("0.0921")
    assert estimates.ibs_reference == Decimal("0.1870")
    assert estimates.tcu_cbs_reference == Decimal("0.113")
    assert estimates.cbs_reference != estimates.tcu_cbs_reference
