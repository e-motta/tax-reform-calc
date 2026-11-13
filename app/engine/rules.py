"""Typed view of one versioned rules directory."""

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

Supply = Literal["goods", "services"]
CbsMode = Literal["statutory", "reference_minus_points", "reference"]
IbsMode = Literal["statutory", "reference_fraction"]


class Estimates(BaseModel):
    cbs_reference: Decimal
    ibs_reference: Decimal
    combined_reference: Decimal
    source: str
    source_url: str
    tcu_cbs_reference: Decimal
    tcu_source: str
    tcu_source_url: str
    statutory_review_cap: Decimal
    statutory_review_cap_source: str


class Manifest(BaseModel):
    version: str
    as_of: date
    currency: str
    price_basis: str
    customer: str
    goods_origin: str
    estimates: Estimates


class Regime(BaseModel):
    supported: bool
    cumulative: bool | None
    pis: Decimal | None
    cofins: Decimal | None
    source: str


class RegimesFile(BaseModel):
    icms_excluded_from_pis_cofins_base: bool
    icms_exclusion_source: str
    iss_excluded_from_pis_cofins_base: bool
    iss_exclusion_source: str
    regimes: dict[str, Regime]


class CbsSpec(BaseModel):
    mode: CbsMode
    rate: Decimal | None = None
    points: Decimal | None = None


class IbsSpec(BaseModel):
    mode: IbsMode
    state: Decimal | None = None
    municipal: Decimal | None = None
    fraction: Decimal | None = None


class TransitionYear(BaseModel):
    year: int
    pis_cofins: bool
    ipi: bool
    icms_iss_factor: Decimal
    selective: bool
    offset_test_tax_against_pis_cofins: bool
    cbs: CbsSpec
    ibs: IbsSpec
    source: str
    source_pt: str


class TransitionFile(BaseModel):
    years: list[TransitionYear]


class InterstateRate(BaseModel):
    origin_group: str
    destination_group: str
    rate: Decimal


class InterstateFile(BaseModel):
    source: str
    south_southeast_except_es: list[str]
    rates: list[InterstateRate]


class Surcharge(BaseModel):
    code: str
    rate: Decimal
    source: str


class StateRate(BaseModel):
    uf: str
    name_en: str
    name_pt: str
    region: str
    internal_rate: Decimal
    source: str
    generalized_surcharge: Surcharge | None = None


class StatesFile(BaseModel):
    verified_on: date
    states: list[StateRate]


class SelectiveTax(BaseModel):
    ad_valorem: Decimal | None = None
    ad_valorem_base: Decimal | None = None
    conversion_factor: Decimal | None = None
    source: str

    @property
    def rate(self) -> Decimal:
        if self.ad_valorem is not None:
            return self.ad_valorem
        if self.ad_valorem_base is None or self.conversion_factor is None:
            raise ValueError("selective tax is missing a rate")
        return self.ad_valorem_base * self.conversion_factor


class Category(BaseModel):
    id: str
    supply: Supply
    name_en: str
    name_pt: str
    summary_en: str
    summary_pt: str
    cbs_ibs_reduction: Decimal = Field(ge=0, le=1)
    reduction_source: str
    iss_scenario_rate: Decimal | None = None
    iss_source: str | None = None
    ipi_rate: Decimal | None = None
    ipi_source: str | None = None
    selective: SelectiveTax | None = None


class CategoriesFile(BaseModel):
    categories: list[Category]


class RuleSet(BaseModel):
    manifest: Manifest
    regimes: RegimesFile
    transition: TransitionFile
    interstate: InterstateFile
    states: StatesFile
    categories: CategoriesFile

    @property
    def version(self) -> str:
        return self.manifest.version

    def category(self, category_id: str) -> Category | None:
        for item in self.categories.categories:
            if item.id == category_id:
                return item
        return None

    def state(self, uf: str) -> StateRate | None:
        for item in self.states.states:
            if item.uf == uf:
                return item
        return None

    def regime(self, name: str) -> Regime | None:
        return self.regimes.regimes.get(name)
