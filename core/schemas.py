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