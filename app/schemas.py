"""API and engine contracts.

Decimal fields are serialised as strings so a rate such as 9.21% does not
pick up a binary floating-point error on the way to the browser.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Supply = Literal["goods", "services"]
RegimeName = Literal["lucro_real", "lucro_presumido", "simples"]
YearKind = Literal["baseline", "transition"]


ISS_MIN = Decimal("0.02")
ISS_MAX = Decimal("0.05")


class CalculationRequest(BaseModel):
    category_id: str = Field(min_length=1, max_length=64)
    origin_uf: str = Field(min_length=2, max_length=2)
    destination_uf: str = Field(min_length=2, max_length=2)
    regime: RegimeName
    price: Decimal = Field(gt=0, le=Decimal("1000000000"))
    iss_rate: Decimal | None = Field(default=None, ge=ISS_MIN, le=ISS_MAX)

    @field_validator("origin_uf", "destination_uf", mode="before")
    @classmethod
    def _upper_uf(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("category_id", mode="before")
    @classmethod
    def _strip_category(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TaxLine(BaseModel):
    code: str
    amount: Decimal
    rate: Decimal | None = None
    estimated: bool = False
    detail: str | None = None


class YearResult(BaseModel):
    year: int | None
    kind: YearKind
    customer_price: Decimal
    total_tax: Decimal
    net_price: Decimal
    effective_rate: Decimal
    nominal_cbs_ibs_rate: Decimal
    lines: list[TaxLine]
    source: str
    source_pt: str
    flags: list[str]


class EstimateDisclosure(BaseModel):
    cbs_reference: Decimal
    ibs_reference: Decimal
    combined_reference: Decimal
    as_of: date
    source: str
    source_url: str
    tcu_cbs_reference: Decimal
    tcu_source: str
    tcu_source_url: str
    tcu_used_in_calculation: bool
    statutory_review_cap: Decimal
    statutory_review_cap_source: str


class CalculationResult(BaseModel):
    rules_version: str
    as_of: date
    category_id: str
    supply: Supply
    origin_uf: str
    destination_uf: str
    regime: RegimeName
    price: Decimal
    interstate: bool
    interstate_rate: Decimal | None
    estimates: EstimateDisclosure
    assumptions: list[str]
    baseline: YearResult
    years: list[YearResult]


class CategoryOut(BaseModel):
    id: str
    supply: Supply
    name_en: str
    name_pt: str
    summary_en: str
    summary_pt: str
    cbs_ibs_reduction: Decimal
    selective: bool


class StateOut(BaseModel):
    uf: str
    name_en: str
    name_pt: str
    internal_rate: Decimal
    generalized_surcharge: Decimal


class RegimeOut(BaseModel):
    id: str
    supported: bool
    pis: Decimal | None
    cofins: Decimal | None


class RulesOut(BaseModel):
    version: str
    as_of: date
    estimates: EstimateDisclosure
    categories: list[CategoryOut]
    states: list[StateOut]
    regimes: list[RegimeOut]


class HealthOut(BaseModel):
    status: Literal["ok"]
    rules_version: str
    rules_as_of: date


class ErrorBody(BaseModel):
    code: str
    message_en: str
    message_pt: str
