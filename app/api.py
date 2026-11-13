"""HTTP routes. The tax logic stays in the engine; this module only translates."""

from typing import NoReturn

from fastapi import APIRouter, HTTPException, Request

from app.engine.calculate import (
    RegimeNotSupportedError,
    UnknownInputError,
    calculate,
    estimates_disclosure,
)
from app.engine.rules import RuleSet
from app.schemas import (
    CalculationRequest,
    CalculationResult,
    CategoryOut,
    ErrorBody,
    HealthOut,
    RegimeOut,
    RulesOut,
    StateOut,
)

router = APIRouter(prefix="/api")


def _rules(request: Request) -> RuleSet:
    return request.app.state.rules


@router.get("/health", response_model=HealthOut)
def health(request: Request) -> HealthOut:
    rules = _rules(request)
    return HealthOut(
        status="ok",
        rules_version=rules.version,
        rules_as_of=rules.manifest.as_of,
    )


@router.get("/rules", response_model=RulesOut)
def read_rules(request: Request) -> RulesOut:
    rules = _rules(request)
    return RulesOut(
        version=rules.version,
        as_of=rules.manifest.as_of,
        estimates=estimates_disclosure(rules),
        categories=[
            CategoryOut(
                id=item.id,
                supply=item.supply,
                name_en=item.name_en,
                name_pt=item.name_pt,
                summary_en=item.summary_en,
                summary_pt=item.summary_pt,
                cbs_ibs_reduction=item.cbs_ibs_reduction,
                selective=item.selective is not None,
                iss_scenario_rate=item.iss_scenario_rate,
            )
            for item in rules.categories.categories
        ],
        states=[
            StateOut(
                uf=item.uf,
                name_en=item.name_en,
                name_pt=item.name_pt,
                internal_rate=item.internal_rate,
                generalized_surcharge=(
                    item.generalized_surcharge.rate
                    if item.generalized_surcharge is not None
                    else 0
                ),
            )
            for item in rules.states.states
        ],
        regimes=[
            RegimeOut(
                id=name,
                supported=item.supported,
                pis=item.pis,
                cofins=item.cofins,
            )
            for name, item in rules.regimes.regimes.items()
        ],
    )


@router.post(
    "/calculate",
    response_model=CalculationResult,
    responses={
        422: {
            "model": ErrorBody,
            "description": (
                "The regime is not supported, or the category or state is unknown."
            ),
        }
    },
)
def calculate_route(body: CalculationRequest, request: Request) -> CalculationResult:
    try:
        return calculate(body, _rules(request))
    except RegimeNotSupportedError:
        _fail(
            "regime_not_supported",
            (
                "Simples Nacional is not in this version. The unified schedule "
                "in Complementary Law 123/2006 needs its own table, and the "
                "2026 CBS and IBS test rates do not apply to Simples taxpayers."
            ),
            (
                "O Simples Nacional fica de fora nesta versão. O regime da "
                "LC nº 123/2006 tem tabela própria, e as alíquotas de teste "
                "de CBS e IBS de 2026 não se aplicam ao optante."
            ),
        )
    except UnknownInputError as exc:
        _fail(exc.code, exc.message_en, exc.message_pt)


def _fail(code: str, message_en: str, message_pt: str) -> NoReturn:
    raise HTTPException(
        status_code=422,
        detail=ErrorBody(
            code=code, message_en=message_en, message_pt=message_pt
        ).model_dump(),
    )
