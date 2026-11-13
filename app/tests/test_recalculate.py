"""The batch seam calls the same function a future OCI Queue worker would call."""

from decimal import Decimal

import pytest

from app.engine.loader import load_rules
from app.engine.recalculate import RecalculationCommand, RulesVersionMismatch, apply
from app.schemas import CalculationRequest


def test_apply_matches_a_direct_calculation():
    rules = load_rules()
    command = RecalculationCommand(
        request=CalculationRequest(
            category_id="medicines",
            origin_uf="MG",
            destination_uf="MG",
            regime="lucro_presumido",
            price=Decimal("80"),
        ),
        rules_version=rules.version,
    )
    result = apply(command, rules)
    assert result.category_id == "medicines"
    assert result.rules_version == "2026-11-13"
    assert len(result.years) == 8


def test_a_stale_rules_version_is_refused():
    rules = load_rules()
    command = RecalculationCommand(
        request=CalculationRequest(
            category_id="standard_goods",
            origin_uf="SP",
            destination_uf="SP",
            regime="lucro_real",
            price=Decimal("10"),
        ),
        rules_version="1999-01-01",
    )
    with pytest.raises(RulesVersionMismatch):
        apply(command, rules)
