"""The rule engine: identities, statutory rates, and the labelled estimates."""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from app.engine.calculate import (
    RegimeNotSupportedError,
    UnknownInputError,
    calculate,
)
from app.engine.loader import load_rules
from app.schemas import CalculationRequest

NET = Decimal("1000.00")


@pytest.fixture(scope="module")
def rules():
    return load_rules()


def _run(rules, **overrides):
    payload = {
        "category_id": "standard_goods",
        "origin_uf": "SP",
        "destination_uf": "SP",
        "regime": "lucro_real",
        "price": NET,
    }
    payload.update(overrides)
    return calculate(CalculationRequest(**payload), rules)


def _line(year, code):
    for line in year.lines:
        if line.code == code:
            return line
    raise AssertionError(f"{code} missing in {year.year}")


def _year(result, year):
    found = [item for item in result.years if item.year == year]
    assert len(found) == 1
    return found[0]


def test_supplier_keeps_the_net_price_in_every_year(rules):
    result = _run(rules, destination_uf="BA", category_id="beer")
    for year in [result.baseline, *result.years]:
        assert year.customer_price - year.total_tax == NET


def test_lucro_real_internal_sao_paulo_gross_up(rules):
    result = _run(rules)
    baseline = result.baseline
    # V = net / ((1 - 0.18) * (1 - 0.0925)), then rounded half up to the cent.
    invoice = (NET / (Decimal("0.82") * Decimal("0.9075"))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert baseline.customer_price == invoice
    assert _line(baseline, "icms").rate == Decimal("0.18")
    assert _line(baseline, "pis").rate == Decimal("0.0165")
    assert _line(baseline, "cofins").rate == Decimal("0.076")
    assert (
        _line(baseline, "icms").amount
        + _line(baseline, "pis").amount
        + _line(baseline, "cofins").amount
        == invoice - NET
    )


def test_lucro_presumido_uses_the_cumulative_rates(rules):
    result = _run(rules, regime="lucro_presumido")
    assert _line(result.baseline, "pis").rate == Decimal("0.0065")
    assert _line(result.baseline, "cofins").rate == Decimal("0.03")
    # A lower PIS/COFINS rate grosses up to a smaller invoice.
    real = _run(rules)
    assert result.baseline.customer_price < real.baseline.customer_price


def test_interstate_split_to_a_final_consumer(rules):
    # São Paulo into Bahia: 7% (Senate Resolution 22/1989). Bahia modal is 20.5%.
    north = _run(rules, destination_uf="BA")
    assert north.interstate_rate == Decimal("0.07")
    assert _line(north.baseline, "icms_interstate").rate == Decimal("0.07")
    assert _line(north.baseline, "icms_difal").rate == Decimal("0.135")

    # São Paulo into Rio de Janeiro: 12%, plus the generalised FECP of 2 points.
    rio = _run(rules, destination_uf="RJ")
    assert rio.interstate_rate == Decimal("0.12")
    assert _line(rio.baseline, "icms_interstate").rate == Decimal("0.12")
    assert _line(rio.baseline, "icms_difal").rate == Decimal("0.08")
    fecp = _line(rio.baseline, "fcp")
    assert fecp.rate == Decimal("0.02")
    assert fecp.detail == "FECP"

    # Bahia into São Paulo: origin is outside the South/Southeast group, so 12%.
    back = _run(rules, origin_uf="BA", destination_uf="SP")
    assert back.interstate_rate == Decimal("0.12")


def test_2026_test_tax_does_not_raise_the_burden(rules):
    result = _run(rules)
    year = _year(result, 2026)
    assert _line(year, "cbs").rate == Decimal("0.009")
    assert _line(year, "ibs_state").rate == Decimal("0.001")
    assert _line(year, "ibs_municipal").rate == Decimal("0")
    assert _line(year, "offset_2026").amount == -(
        _line(year, "cbs").amount + _line(year, "ibs_state").amount
    )
    assert year.total_tax == result.baseline.total_tax
    assert year.customer_price == result.baseline.customer_price
    assert "test_tax_offset" in year.flags
    assert "cbs_estimated" not in year.flags


def test_2027_replaces_pis_cofins_and_cuts_the_cbs_reference(rules):
    result = _run(rules)
    year = _year(result, 2027)
    assert _line(year, "pis").amount == 0
    assert _line(year, "cofins").amount == 0
    # 9.21% minus the statutory 0.1 percentage point.
    assert _line(year, "cbs").rate == Decimal("0.0911")
    assert _line(year, "cbs").estimated is True
    assert _line(year, "ibs_state").rate == Decimal("0.0005")
    assert _line(year, "ibs_municipal").rate == Decimal("0.0005")
    assert _line(year, "ibs_state").estimated is False
    # ICMS is still fully inside the invoice, so the invoice is 1000 / 0.82.
    assert year.customer_price > Decimal("1000")
    assert "cbs_estimated" in year.flags


def test_phase_out_and_full_rate_in_2033(rules):
    result = _run(rules)
    year_2029 = _year(result, 2029)
    assert _line(year_2029, "icms").rate == Decimal("0.162")  # 18% * 90%
    assert _line(year_2029, "ibs").rate == Decimal("0.0187")  # 18.70% * 10%
    assert _line(year_2029, "cbs").rate == Decimal("0.0921")

    year_2032 = _year(result, 2032)
    assert _line(year_2032, "icms").rate == Decimal("0.108")  # 18% * 60%
    assert _line(year_2032, "ibs").rate == Decimal("0.0748")  # 18.70% * 40%

    year_2033 = _year(result, 2033)
    assert _line(year_2033, "icms").amount == 0
    assert _line(year_2033, "pis").amount == 0
    assert _line(year_2033, "cbs").amount == Decimal("92.10")
    assert _line(year_2033, "ibs").amount == Decimal("187.00")
    assert year_2033.customer_price == Decimal("1279.10")
    assert year_2033.nominal_cbs_ibs_rate == Decimal("0.2791")


def test_reductions_apply_to_the_reference_and_to_the_test_rates(rules):
    food = _run(rules, category_id="food_reduced")
    # 60% reduction leaves 40% of the rate.
    assert _line(_year(food, 2033), "cbs").rate == Decimal("0.03684")
    assert _line(_year(food, 2033), "ibs").rate == Decimal("0.0748")
    # 2027: (9.21% - 0.1pp) * 40%.
    assert _line(_year(food, 2027), "cbs").rate == Decimal("0.03644")
    assert _line(_year(food, 2026), "cbs").rate == Decimal("0.0036")

    basket = _run(rules, category_id="basic_food_basket")
    assert _line(_year(basket, 2033), "cbs").amount == 0
    assert _line(_year(basket, 2033), "ibs").amount == 0
    # The zero rate does not wipe today's ICMS. That benefit is product-specific.
    assert _line(basket.baseline, "icms").rate == Decimal("0.18")

    education = _run(rules, category_id="education_services")
    assert _line(_year(education, 2033), "cbs").rate == Decimal("0.03684")
    assert _line(education.baseline, "iss").rate == Decimal("0.05")

    lawyer = _run(rules, category_id="professional_services")
    assert _line(_year(lawyer, 2033), "cbs").rate == Decimal("0.06447")


def test_selective_tax_uses_the_2027_provisional_measure(rules):
    beer = _run(rules, category_id="beer")
    assert "selective" not in {line.code for line in _year(beer, 2026).lines}
    taxed = _line(_year(beer, 2027), "selective")
    assert taxed.rate == Decimal("0.042")
    assert taxed.amount == Decimal("42.00")
    assert taxed.estimated is False
    held = _line(_year(beer, 2033), "selective")
    assert held.rate == Decimal("0.042")
    assert held.estimated is True

    car = _run(rules, category_id="passenger_cars")
    # 6.3% * 1.21, before the per-vehicle adjustments.
    assert _line(_year(car, 2027), "selective").rate == Decimal("0.07623")
    assert _line(_year(car, 2027), "selective").amount == Decimal("76.23")

    spirits = _run(rules, category_id="spirits")
    assert _line(_year(spirits, 2027), "selective").rate == Decimal("0.24")


def test_ipi_is_added_outside_the_gross_up_when_a_ruleset_sets_it(rules):
    items = rules.categories.categories
    index = next(i for i, item in enumerate(items) if item.id == "standard_goods")
    category = items[index]
    items[index] = category.model_copy(
        update={"ipi_rate": Decimal("0.10"), "ipi_source": "test fixture"}
    )
    try:
        result = _run(rules)
    finally:
        items[index] = category
    baseline = result.baseline
    ipi = _line(baseline, "ipi")
    invoice = baseline.customer_price - ipi.amount
    assert ipi.rate == Decimal("0.10")
    assert ipi.amount == (invoice * Decimal("0.10")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    # Gone with the IPI in 2027, apart from the Manaus residue this version skips.
    assert "ipi" not in {line.code for line in _year(result, 2027).lines}
    assert result.baseline.customer_price - result.baseline.total_tax == NET


def test_simples_and_unknown_inputs_are_rejected(rules):
    with pytest.raises(RegimeNotSupportedError):
        _run(rules, regime="simples")
    with pytest.raises(UnknownInputError) as unknown:
        _run(rules, category_id="ncm-0101")
    assert unknown.value.code == "unknown_category"
    with pytest.raises(UnknownInputError) as state:
        _run(rules, origin_uf="XX")
    assert state.value.code == "unknown_state"


def test_sergipe_surcharge_is_part_of_the_general_rule(rules):
    result = _run(rules, origin_uf="SE", destination_uf="SE")
    assert _line(result.baseline, "fcp").detail == "FECOEP"
    assert _line(result.baseline, "fcp").rate == Decimal("0.01")
    assert _line(result.baseline, "icms").rate == Decimal("0.19")
