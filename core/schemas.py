from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass(frozen=True)
class FarmInputs:
    length_m: float
    width_m: float
    height_m: float
    insulation_m: float
    floor_usage_eff: float
    floors: int

@dataclass(frozen=True)
class CropInputs:
    selected: List[str]
    shares: Dict[str, float]          # crop -> share (0..1)
    yields_kg_m2_yr: Dict[str, float] # crop -> yield

@dataclass(frozen=True)
class FinanceInputs:
    discount_rate: float
    year1_eff: float
    eff_gain: float
    years: int

@dataclass(frozen=True)
class ElectricityScenario:
    base_price_eur_kwh: float
    opt_price_eur_kwh: float
    selected: str  # "base" or "opt"


@dataclass(frozen=True)
class AdvancedFinanceInputs:
    general_inflation: float  # e.g. 0.02 = 2%/yr applied to opex
    crop_price_growth: float  # e.g. 0.04 = 4%/yr on crop revenue (inflation + premium)
    elec_price_growth: float  # e.g. 0.03 = 3%/yr on electricity cost

    # LED replacement cycle (from Excel Replace Invest. column)
    led_replacement_years: List[int]  # years when full LED replacement happens, e.g. [5, 10]
    led_replacement_cost: float  # cost per replacement event (€)

    # Annual maintenance reserve
    annual_maintenance_pct: float  # % of equipment CapEx reserved each year, e.g. 0.025