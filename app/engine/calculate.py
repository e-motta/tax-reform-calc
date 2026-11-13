"""Single-supply comparison of the current consumption taxes and the dual VAT.

The function is pure: the same request and the same rules always return the
same result. A later batch job can call it from an OCI Queue worker without
any change to the tax logic. See app/engine/recalculate.py.

Price basis
    ``price`` is the amount the supplier keeps before consumption taxes.

Legacy taxes
    ICMS, the generalised state surcharge, ISS, PIS and COFINS are inside the
    price ("por dentro"). The invoice value is grossed up so that, after those
    taxes, the supplier is left with ``price``. PIS and COFINS are charged on
    the invoice minus ICMS, the surcharge and ISS.

New taxes
    CBS and IBS do not enter their own base, and from 2026 to 2032 they are
    also charged on a base that excludes ICMS, ISS, PIS and COFINS
    (LC 214/2025, art. 12, § 2º). On this price basis that base is ``price``
    itself, so CBS, IBS and the ad valorem selective tax are ``rate * price``,
    added on top of the invoice.

What this is not
    One taxable supply, with no input credit. It is the tax debited on the
    operation, not the net burden of a firm that credits tax on its purchases.
    Modal ICMS only. No NCM, no municipal ISS table, no Simples schedule.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.engine.rules import Category, Regime, RuleSet, StateRate, TransitionYear
from app.schemas import (
    CalculationRequest,
    CalculationResult,
    EstimateDisclosure,
    TaxLine,
    YearResult,
)

CENT = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")

BASELINE_SOURCE = (
    "Current system, before the CBS and IBS test year: full modal ICMS or the "
    "ISS scenario rate, plus PIS and COFINS. These are the same legacy rates "
    "the 2026 column still carries beside the test taxes."
)
BASELINE_SOURCE_PT = (
    "Sistema vigente, antes do ano de teste da CBS e do IBS: ICMS pela "
    "alíquota interna geral, ou ISS na premissa de 5%, mais PIS e COFINS. "
    "São as mesmas alíquotas que a coluna de 2026 ainda traz, ao lado dos "
    "tributos de teste."
)


class RegimeNotSupportedError(Exception):
    def __init__(self, regime: str) -> None:
        self.regime = regime
        super().__init__(regime)


class UnknownInputError(Exception):
    def __init__(self, code: str, message_en: str, message_pt: str) -> None:
        self.code = code
        self.message_en = message_en
        self.message_pt = message_pt
        super().__init__(message_en)


def calculate(request: CalculationRequest, rules: RuleSet) -> CalculationResult:
    category = rules.category(request.category_id)
    if category is None:
        raise UnknownInputError(
            "unknown_category",
            f"Unknown category: {request.category_id}.",
            f"Categoria desconhecida: {request.category_id}.",
        )
    origin = rules.state(request.origin_uf)
    destination = rules.state(request.destination_uf)
    if origin is None or destination is None:
        missing = request.origin_uf if origin is None else request.destination_uf
        raise UnknownInputError(
            "unknown_state",
            f"Unknown state: {missing}.",
            f"UF desconhecida: {missing}.",
        )
    regime = rules.regime(request.regime)
    if regime is None or not regime.supported:
        raise RegimeNotSupportedError(request.regime)

    net = request.price.quantize(CENT, rounding=ROUND_HALF_UP)
    interstate_rate = _interstate_rate(request.origin_uf, request.destination_uf, rules)
    disclosure = estimates_disclosure(rules)
    baseline = _year(
        net=net,
        category=category,
        origin=origin,
        destination=destination,
        regime=regime,
        interstate_nominal=interstate_rate,
        year=None,
        spec=None,
        rules=rules,
    )
    years = [
        _year(
            net=net,
            category=category,
            origin=origin,
            destination=destination,
            regime=regime,
            interstate_nominal=interstate_rate,
            year=spec.year,
            spec=spec,
            rules=rules,
        )
        for spec in rules.transition.years
    ]
    return CalculationResult(
        rules_version=rules.version,
        as_of=rules.manifest.as_of,
        category_id=category.id,
        supply=category.supply,
        origin_uf=origin.uf,
        destination_uf=destination.uf,
        regime=request.regime,  # type: ignore[arg-type]
        price=net,
        interstate=interstate_rate is not None,
        interstate_rate=interstate_rate,
        estimates=disclosure,
        assumptions=_assumptions(category, rules),
        baseline=baseline,
        years=years,
    )


def estimates_disclosure(rules: RuleSet) -> EstimateDisclosure:
    estimates = rules.manifest.estimates
    return EstimateDisclosure(
        cbs_reference=estimates.cbs_reference,
        ibs_reference=estimates.ibs_reference,
        combined_reference=estimates.combined_reference,
        as_of=rules.manifest.as_of,
        source=estimates.source,
        source_url=estimates.source_url,
        tcu_cbs_reference=estimates.tcu_cbs_reference,
        tcu_source=estimates.tcu_source,
        tcu_source_url=estimates.tcu_source_url,
        tcu_used_in_calculation=False,
        statutory_review_cap=estimates.statutory_review_cap,
        statutory_review_cap_source=estimates.statutory_review_cap_source,
    )


def _assumptions(category: Category, rules: RuleSet) -> list[str]:
    codes = [
        "price_is_net",
        "final_consumer",
        "no_input_credits",
        "domestic_goods",
        "reference_rates_are_estimates",
        "tcu_rate_not_used",
        "ibs_phase_in_is_a_projection",
        "ipi_not_by_ncm",
        "ipi_zfm_not_modelled",
    ]
    if category.supply == "goods":
        codes.extend(["modal_icms", "fcp_only_when_general", "icms_excluded"])
    else:
        codes.extend(
            [
                "iss_scenario",
                "iss_excluded",
                "iss_modulation_open",
                "states_do_not_change_services",
            ]
        )
    if category.id == "basic_food_basket":
        codes.append("basic_basket_keeps_modal_icms")
    if category.selective is not None:
        codes.append("selective_holding_after_2027")
    if category.id == "passenger_cars":
        codes.append("vehicle_adjustments_not_applied")
    if not rules.regimes.icms_excluded_from_pis_cofins_base:
        codes.remove("icms_excluded") if "icms_excluded" in codes else None
    return codes


def _year(
    *,
    net: Decimal,
    category: Category,
    origin: StateRate,
    destination: StateRate,
    regime: Regime,
    interstate_nominal: Decimal | None,
    year: int | None,
    spec: TransitionYear | None,
    rules: RuleSet,
) -> YearResult:
    factor = ONE if spec is None else spec.icms_iss_factor
    charge_pis = spec is None or spec.pis_cofins
    charge_ipi = spec is None or spec.ipi
    pis_rate = regime.pis if charge_pis and regime.pis is not None else ZERO
    cofins_rate = regime.cofins if charge_pis and regime.cofins is not None else ZERO

    lines: list[TaxLine] = []
    if category.supply == "goods":
        invoice, goods_lines = _goods_invoice(
            net=net,
            origin=origin,
            destination=destination,
            interstate_nominal=interstate_nominal,
            factor=factor,
            pis_rate=pis_rate,
            cofins_rate=cofins_rate,
        )
        lines.extend(goods_lines)
    else:
        iss_rate = (category.iss_scenario_rate or ZERO) * factor
        invoice, service_lines = _service_invoice(
            net=net,
            iss_rate=iss_rate,
            pis_rate=pis_rate,
            cofins_rate=cofins_rate,
        )
        lines.extend(service_lines)

    ipi_rate = category.ipi_rate if charge_ipi and category.ipi_rate else ZERO
    ipi_amount = ZERO
    if ipi_rate:
        # IPI is outside the gross-up, on the invoice value (LC 87/1996, art. 13, § 2º,
        # when the IPI is stated separately it stays out of the ICMS base).
        ipi_amount = _money(invoice * ipi_rate)
        lines.append(TaxLine(code="ipi", amount=ipi_amount, rate=ipi_rate))

    keep = ONE - category.cbs_ibs_reduction
    new_lines, nominal, flags = _new_taxes(
        net=net, keep=keep, spec=spec, category=category, rules=rules
    )
    lines.extend(new_lines)

    offset = ZERO
    if spec is not None and spec.offset_test_tax_against_pis_cofins:
        test_tax = sum(
            (line.amount for line in new_lines if line.code.startswith(("cbs", "ibs"))),
            ZERO,
        )
        pis_cofins = sum(
            (line.amount for line in lines if line.code in {"pis", "cofins"}),
            ZERO,
        )
        offset = -min(test_tax, pis_cofins)
        lines.append(
            TaxLine(code="offset_2026", amount=offset, rate=None, estimated=False)
        )
        flags.append("test_tax_offset")

    new_amount = sum((line.amount for line in new_lines), ZERO)
    unoffset = ZERO
    if spec is not None and spec.offset_test_tax_against_pis_cofins:
        # The test tax is removed by the offset. Only a remainder above
        # PIS/COFINS would still be a cost, and only that remainder is passed on.
        unoffset = new_amount + offset
        passed_on = unoffset
    else:
        passed_on = new_amount

    legacy_tax = invoice - net + ipi_amount
    total_tax = legacy_tax + new_amount + offset
    customer_price = invoice + ipi_amount + passed_on
    effective = ZERO if customer_price == 0 else total_tax / customer_price

    return YearResult(
        year=year,
        kind="baseline" if spec is None else "transition",
        customer_price=customer_price,
        total_tax=total_tax,
        net_price=net,
        effective_rate=effective,
        nominal_cbs_ibs_rate=nominal,
        lines=lines,
        source=BASELINE_SOURCE if spec is None else spec.source,
        source_pt=BASELINE_SOURCE_PT if spec is None else spec.source_pt,
        flags=flags,
    )


def _goods_invoice(
    *,
    net: Decimal,
    origin: StateRate,
    destination: StateRate,
    interstate_nominal: Decimal | None,
    factor: Decimal,
    pis_rate: Decimal,
    cofins_rate: Decimal,
) -> tuple[Decimal, list[TaxLine]]:
    taxing = destination if interstate_nominal is not None else origin
    icms_rate = taxing.internal_rate * factor
    fcp_rate = ZERO
    fcp_detail = None
    if taxing.generalized_surcharge is not None:
        fcp_rate = taxing.generalized_surcharge.rate * factor
        fcp_detail = taxing.generalized_surcharge.code.upper()
    interstate_rate = (
        interstate_nominal * factor if interstate_nominal is not None else ZERO
    )
    por_dentro = icms_rate + fcp_rate
    invoice, pis, cofins, fcp_amount, interstate_amount, residual = _gross_up(
        net=net,
        por_dentro=por_dentro,
        fcp_rate=fcp_rate,
        interstate_rate=interstate_rate,
        pis_rate=pis_rate,
        cofins_rate=cofins_rate,
    )
    lines: list[TaxLine] = []
    if interstate_nominal is None:
        lines.append(TaxLine(code="icms", amount=residual, rate=icms_rate))
    else:
        difal_rate = icms_rate - interstate_rate
        lines.append(
            TaxLine(
                code="icms_interstate", amount=interstate_amount, rate=interstate_rate
            )
        )
        lines.append(TaxLine(code="icms_difal", amount=residual, rate=difal_rate))
    if fcp_detail is not None:
        lines.append(
            TaxLine(code="fcp", amount=fcp_amount, rate=fcp_rate, detail=fcp_detail)
        )
    lines.append(TaxLine(code="pis", amount=pis, rate=pis_rate))
    lines.append(TaxLine(code="cofins", amount=cofins, rate=cofins_rate))
    return invoice, lines


def _service_invoice(
    *,
    net: Decimal,
    iss_rate: Decimal,
    pis_rate: Decimal,
    cofins_rate: Decimal,
) -> tuple[Decimal, list[TaxLine]]:
    invoice, pis, cofins, _fcp, _interstate, iss_amount = _gross_up(
        net=net,
        por_dentro=iss_rate,
        fcp_rate=ZERO,
        interstate_rate=ZERO,
        pis_rate=pis_rate,
        cofins_rate=cofins_rate,
    )
    lines = [
        TaxLine(code="iss", amount=iss_amount, rate=iss_rate),
        TaxLine(code="pis", amount=pis, rate=pis_rate),
        TaxLine(code="cofins", amount=cofins, rate=cofins_rate),
    ]
    return invoice, lines


def _gross_up(
    *,
    net: Decimal,
    por_dentro: Decimal,
    fcp_rate: Decimal,
    interstate_rate: Decimal,
    pis_rate: Decimal,
    cofins_rate: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """Return invoice, PIS, COFINS, FCP, interstate ICMS, and the residual inside tax.

    The residual is internal ICMS, DIFAL, or ISS. It absorbs the cent so the
    rounded inside taxes plus the net price equal the rounded invoice.
    """
    pc = pis_rate + cofins_rate
    if por_dentro < 0 or por_dentro >= 1 or pc < 0 or pc >= 1:
        raise UnknownInputError(
            "rate_out_of_range",
            "A rate leaves no positive base to gross up.",
            "Uma alíquota não deixa base positiva para o gross-up.",
        )
    invoice_exact = net / ((ONE - por_dentro) * (ONE - pc))
    invoice = _money(invoice_exact)
    base_exact = invoice_exact * (ONE - por_dentro)
    pis = _money(base_exact * pis_rate)
    cofins = _money(base_exact * cofins_rate)
    fcp_amount = _money(invoice_exact * fcp_rate)
    interstate_amount = _money(invoice_exact * interstate_rate)
    residual = invoice - net - pis - cofins - fcp_amount - interstate_amount
    return invoice, pis, cofins, fcp_amount, interstate_amount, residual


def _new_taxes(
    *,
    net: Decimal,
    keep: Decimal,
    spec: TransitionYear | None,
    category: Category,
    rules: RuleSet,
) -> tuple[list[TaxLine], Decimal, list[str]]:
    if spec is None:
        return [], ZERO, []

    estimates = rules.manifest.estimates
    lines: list[TaxLine] = []
    flags: list[str] = []
    cbs_spec = spec.cbs
    if cbs_spec.mode == "statutory":
        cbs_rate = (cbs_spec.rate or ZERO) * keep
        cbs_estimated = False
    elif cbs_spec.mode == "reference_minus_points":
        cbs_rate = (estimates.cbs_reference - (cbs_spec.points or ZERO)) * keep
        cbs_estimated = True
    else:
        cbs_rate = estimates.cbs_reference * keep
        cbs_estimated = True
    if cbs_estimated and cbs_rate != 0:
        flags.append("cbs_estimated")
    lines.append(
        TaxLine(
            code="cbs",
            amount=_money(net * cbs_rate),
            rate=cbs_rate,
            estimated=cbs_estimated and cbs_rate != 0,
        )
    )

    ibs_spec = spec.ibs
    ibs_nominal = ZERO
    if ibs_spec.mode == "statutory":
        state_rate = (ibs_spec.state or ZERO) * keep
        municipal_rate = (ibs_spec.municipal or ZERO) * keep
        lines.append(
            TaxLine(
                code="ibs_state",
                amount=_money(net * state_rate),
                rate=state_rate,
            )
        )
        lines.append(
            TaxLine(
                code="ibs_municipal",
                amount=_money(net * municipal_rate),
                rate=municipal_rate,
            )
        )
        ibs_nominal = state_rate + municipal_rate
    else:
        ibs_rate = estimates.ibs_reference * (ibs_spec.fraction or ZERO) * keep
        ibs_estimated = ibs_rate != 0
        if ibs_estimated:
            flags.append("ibs_estimated")
        lines.append(
            TaxLine(
                code="ibs",
                amount=_money(net * ibs_rate),
                rate=ibs_rate,
                estimated=ibs_estimated,
            )
        )
        ibs_nominal = ibs_rate

    if spec.selective and category.selective is not None:
        # The selective tax is its own tax. The CBS/IBS reduction does not cut it.
        rate = category.selective.rate
        holding = spec.year > 2027
        if holding:
            flags.append("selective_holding")
        lines.append(
            TaxLine(
                code="selective",
                amount=_money(net * rate),
                rate=rate,
                estimated=holding,
            )
        )

    return lines, cbs_rate + ibs_nominal, flags


def _interstate_rate(origin: str, destination: str, rules: RuleSet) -> Decimal | None:
    if origin == destination:
        return None
    group = set(rules.interstate.south_southeast_except_es)
    origin_group = "south_southeast_except_es" if origin in group else "other"
    destination_group = "south_southeast_except_es" if destination in group else "other"
    for row in rules.interstate.rates:
        origin_matches = row.origin_group == origin_group
        destination_matches = row.destination_group in {destination_group, "any"}
        if origin_matches and destination_matches:
            return row.rate
    raise UnknownInputError(
        "interstate_rate_missing",
        "No interstate rate covers this route.",
        "Não há alíquota interestadual para este percurso.",
    )


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)
