"""Load the latest versioned YAML ruleset, or the one named in RULES_VERSION."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.engine.rules import (
    CategoriesFile,
    InterstateFile,
    Manifest,
    RegimesFile,
    RuleSet,
    StatesFile,
    TransitionFile,
)

REQUIRED_FILES = {
    "manifest": Manifest,
    "regimes": RegimesFile,
    "transition": TransitionFile,
    "interstate": InterstateFile,
    "states": StatesFile,
    "categories": CategoriesFile,
}


class RulesError(Exception):
    """The rules directory is missing, unreadable, or internally inconsistent."""


def rules_root() -> Path:
    override = os.environ.get("RULES_DIR")
    if override:
        return Path(override)
    candidate = Path.cwd() / "rules"
    if candidate.is_dir():
        return candidate
    raise RulesError(
        "No rules directory. Set RULES_DIR or run the app from the repository root."
    )


def load_rules(version: str | None = None) -> RuleSet:
    root = rules_root()
    chosen = version or os.environ.get("RULES_VERSION")
    if chosen is None:
        versions = sorted(path.name for path in root.iterdir() if path.is_dir())
        if not versions:
            raise RulesError(f"No version directories under {root}")
        chosen = versions[-1]
    directory = root / chosen
    if not directory.is_dir():
        raise RulesError(f"Rules version not found: {chosen}")

    loaded: dict[str, object] = {}
    for name, model in REQUIRED_FILES.items():
        path = directory / f"{name}.yaml"
        if not path.is_file():
            raise RulesError(f"Missing {path}")
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            loaded[name] = model.model_validate(raw)
        except ValidationError as exc:
            raise RulesError(f"{path} failed validation: {exc}") from exc

    rules = RuleSet(
        manifest=loaded["manifest"],  # type: ignore[arg-type]
        regimes=loaded["regimes"],  # type: ignore[arg-type]
        transition=loaded["transition"],  # type: ignore[arg-type]
        interstate=loaded["interstate"],  # type: ignore[arg-type]
        states=loaded["states"],  # type: ignore[arg-type]
        categories=loaded["categories"],  # type: ignore[arg-type]
    )
    _check_consistency(rules, directory.name)
    return rules


def _check_consistency(rules: RuleSet, directory_name: str) -> None:
    if rules.manifest.version != directory_name:
        raise RulesError(
            f"manifest version {rules.manifest.version} does not match "
            f"directory {directory_name}"
        )

    estimates = rules.manifest.estimates
    combined = estimates.cbs_reference + estimates.ibs_reference
    if combined != estimates.combined_reference:
        raise RulesError(
            "estimates.combined_reference must equal cbs_reference + ibs_reference"
        )

    ufs = [state.uf for state in rules.states.states]
    if len(ufs) != len(set(ufs)):
        raise RulesError("duplicate state code")
    if len(ufs) != 27:
        raise RulesError(f"expected 27 states, found {len(ufs)}")

    known = set(ufs)
    group = set(rules.interstate.south_southeast_except_es)
    if not group <= known:
        raise RulesError("interstate group names a state that is not in states.yaml")

    ids = [item.id for item in rules.categories.categories]
    if len(ids) != len(set(ids)):
        raise RulesError("duplicate category id")

    years = [item.year for item in rules.transition.years]
    if years != list(range(2026, 2034)):
        raise RulesError("transition years must be 2026 through 2033 in order")
    for item in rules.transition.years:
        if item.cbs.mode == "statutory" and item.cbs.rate is None:
            raise RulesError(f"{item.year} CBS statutory rate is missing")
        if item.cbs.mode == "reference_minus_points" and item.cbs.points is None:
            raise RulesError(f"{item.year} CBS reduction in points is missing")
        if item.ibs.mode == "statutory" and (
            item.ibs.state is None or item.ibs.municipal is None
        ):
            raise RulesError(f"{item.year} statutory IBS split is missing")
        if item.ibs.mode == "reference_fraction" and item.ibs.fraction is None:
            raise RulesError(f"{item.year} IBS fraction is missing")
        if not item.source.strip() or not item.source_pt.strip():
            raise RulesError(f"{item.year} needs a citation in both languages")

    for category in rules.categories.categories:
        if not category.reduction_source.strip():
            raise RulesError(f"{category.id} is missing reduction_source")
        if category.supply == "services" and category.iss_scenario_rate is None:
            raise RulesError(f"{category.id} is a service without an ISS scenario rate")
        if category.supply == "goods" and category.iss_scenario_rate is not None:
            raise RulesError(f"{category.id} is goods but sets an ISS rate")
        if category.selective is not None:
            rate = category.selective.rate
            if rate < 0 or rate > 1:
                raise RulesError(f"{category.id} selective rate is out of range")

    for state in rules.states.states:
        if not state.source.strip():
            raise RulesError(f"{state.uf} is missing a source")
        if state.internal_rate < 0 or state.internal_rate >= 1:
            raise RulesError(f"{state.uf} internal rate is out of range")

    for regime in rules.regimes.regimes.values():
        if regime.supported and (regime.pis is None or regime.cofins is None):
            raise RulesError("a supported regime is missing PIS or COFINS")

    if not isinstance(estimates.cbs_reference, Decimal):
        raise RulesError("reference rates must be decimals")
