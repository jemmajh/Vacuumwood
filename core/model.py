from typing import Dict, Tuple, Optional
import pandas as pd

from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario
import config as cfg


def compute_areas(farm: FarmInputs) -> Dict[str, float]:
    floor_area = farm.length_m * farm.width_m
    cultivable_per_floor = floor_area * farm.floor_usage_eff
    total_cultivatable = cultivable_per_floor * farm.floors
    return {
        "floor_area": floor_area,
        "cultivable_per_floor": cultivable_per_floor,
        "total_cultivatable": total_cultivatable,
    }


def compute_sales(total_cultivatable: float, crops: CropInputs) -> Tuple[pd.DataFrame, float]:
    rows = []
    total_sales = 0.0
    for crop in crops.selected:
        area = total_cultivatable * crops.shares[crop]
        yld = crops.yields_kg_m2_yr[crop]
        price = cfg.DEFAULT_PRICE[crop]
        revenue = area * yld * price
        total_sales += revenue
        rows.append({"Product": crop, "Area (m²)": area, "Revenue (€)": revenue})
    return pd.DataFrame(rows).set_index("Product"), total_sales


def compute_capex(floor_area: float, total_cultivatable: float) -> Dict[str, float]:
    build = floor_area * cfg.CAPEX_BUILDING_PER_M2
    eq = total_cultivatable * cfg.CAPEX_EQUIPMENT_PER_M2
    other = cfg.CAPEX_OTHER_FIXED
    gross = build + eq + other
    subsidy = gross * cfg.CAPEX_SUBSIDY_SHARE
    net = gross - subsidy
    return {"gross": gross, "subsidy": subsidy, "net": net, "build": build, "eq": eq, "other": other}


def compute_opex(total_cultivatable: float, scenario: ElectricityScenario) -> Dict[str, float]:
    elec_use_kwh = total_cultivatable * cfg.ELEC_KWH_PER_M2_YEAR
    other_opex = total_cultivatable * cfg.OTHER_OPEX_PER_M2_YEAR
    price_used = scenario.base_price_eur_kwh if scenario.selected == "base" else scenario.opt_price_eur_kwh
    elec_cost = elec_use_kwh * price_used
    return {
        "elec_use_kwh": elec_use_kwh,
        "other_opex": other_opex,
        "price_used": price_used,
        "elec_cost": elec_cost,
        "yearly_opex": elec_cost + other_opex,
        "elec_cost_base": elec_use_kwh * scenario.base_price_eur_kwh,
        "elec_cost_opt": elec_use_kwh * scenario.opt_price_eur_kwh,
        "yearly_opex_base": (elec_use_kwh * scenario.base_price_eur_kwh) + other_opex,
        "yearly_opex_opt": (elec_use_kwh * scenario.opt_price_eur_kwh) + other_opex,
    }


def build_forecast(
    total_sales: float,
    yearly_opex: float,
    capex_net: float,
    fin: FinanceInputs
) -> Tuple[pd.DataFrame, Optional[int]]:
    forecast = []
    cumulative = 0.0
    payback = None

    for y in range(1, fin.years + 1):
        eff = min(fin.year1_eff + fin.eff_gain * (y - 1), 1.0)
        sales_y = total_sales * eff
        net_cash = sales_y - yearly_opex
        disc_net = net_cash / ((1 + fin.discount_rate) ** y)
        cumulative += disc_net
        npv_minus_capex = cumulative - capex_net

        if payback is None and npv_minus_capex >= 0:
            payback = y

        forecast.append({
            "Year": y,
            "Net Cashflow (€)": net_cash,
            "Discounted (€)": disc_net,
            "Cumulative NPV (€)": cumulative,
            "NPV - CAPEX (€)": npv_minus_capex,
        })

    return pd.DataFrame(forecast), payback