from typing import Dict, Tuple, Optional
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as cfg
from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario


def compute_areas(farm: FarmInputs) -> Dict[str, float]:
    floor_area = farm.length_m * farm.width_m
    cultivable_per_floor = floor_area * farm.floor_usage_eff
    total_cultivatable = cultivable_per_floor * farm.floors
    return {"floor_area": floor_area, "cultivable_per_floor": cultivable_per_floor, "total_cultivatable": total_cultivatable}


def compute_sales(total_cultivatable: float, crops: CropInputs) -> Tuple[pd.DataFrame, float]:
    rows, total_sales = [], 0.0
    for crop in crops.selected:
        area = total_cultivatable * crops.shares[crop]
        revenue = area * crops.yields_kg_m2_yr[crop] * cfg.DEFAULT_PRICE[crop]
        total_sales += revenue
        rows.append({"Product": crop, "Area (m²)": area, "Revenue (€)": revenue})
    return pd.DataFrame(rows).set_index("Product"), total_sales


def compute_capex(floor_area: float, total_cultivatable: float) -> Dict[str, float]:
    build = floor_area * cfg.CAPEX_BUILDING_PER_M2
    eq = total_cultivatable * cfg.CAPEX_EQUIPMENT_PER_M2
    other = cfg.CAPEX_OTHER_FIXED
    gross = build + eq + other
    subsidy = gross * cfg.CAPEX_SUBSIDY_SHARE
    return {"gross": gross, "subsidy": subsidy, "net": gross - subsidy, "build": build, "eq": eq, "other": other}


def compute_opex(total_cultivatable: float, scenario: ElectricityScenario) -> Dict[str, float]:
    elec_use_kwh = total_cultivatable * cfg.ELEC_KWH_PER_M2_YEAR
    other_opex = total_cultivatable * cfg.OTHER_OPEX_PER_M2_YEAR
    price_used = scenario.base_price_eur_kwh if scenario.selected == "base" else scenario.opt_price_eur_kwh
    elec_cost = elec_use_kwh * price_used
    return {
        "elec_use_kwh": elec_use_kwh, "other_opex": other_opex, "price_used": price_used,
        "elec_cost": elec_cost, "yearly_opex": elec_cost + other_opex,
        "elec_cost_base": elec_use_kwh * scenario.base_price_eur_kwh,
        "elec_cost_opt": elec_use_kwh * scenario.opt_price_eur_kwh,
        "yearly_opex_base": (elec_use_kwh * scenario.base_price_eur_kwh) + other_opex,
        "yearly_opex_opt": (elec_use_kwh * scenario.opt_price_eur_kwh) + other_opex,
    }


def build_forecast(total_sales: float, yearly_opex: float, capex_net: float, fin: FinanceInputs) -> Tuple[pd.DataFrame, Optional[int]]:
    forecast, cumulative, payback = [], 0.0, None
    for y in range(1, fin.years + 1):
        eff = min(fin.year1_eff + fin.eff_gain * (y - 1), 1.0)
        net_cash = total_sales * eff - yearly_opex
        disc_net = net_cash / ((1 + fin.discount_rate) ** y)
        cumulative += disc_net
        npv_minus_capex = cumulative - capex_net
        if payback is None and npv_minus_capex >= 0:
            payback = y
        forecast.append({"Year": y, "Net Cashflow (€)": net_cash, "Discounted (€)": disc_net, "Cumulative NPV (€)": cumulative, "NPV - CAPEX (€)": npv_minus_capex})
    return pd.DataFrame(forecast), payback


def build_advanced_forecast(
        total_sales: float,
        yearly_opex_base: float,
        elec_cost_base: float,
        other_opex: float,
        capex_net: float,
        equipment_capex: float,
        fin: FinanceInputs,
        adv,  # AdvancedFinanceInputs
        elec_price_multiplier: float = 1.0,  # 1.0 = base, 1.25 = shock scenario
) -> Tuple[pd.DataFrame, Optional[int]]:
    """
    Advanced 10-year forecast incorporating:

    1. CROP REVENUE GROWTH (crop_price_growth %/yr)
       Revenue grows above general inflation because:
       - Premium positioning of vertically farmed produce allows price increases
       - Assumed: 2% general inflation + 2% real premium growth = 4%/yr default
       Formula: revenue_y = total_sales * efficiency * (1 + crop_price_growth)^(y-1)

    2. ELECTRICITY COST ESCALATION (elec_price_growth %/yr)
       Nordic spot prices have been volatile; a conservative 3%/yr long-run growth
       is applied to the electricity component of OpEx only.
       Formula: elec_cost_y = elec_cost_base * multiplier * (1 + elec_price_growth)^(y-1)
       The multiplier handles the +25% shock scenario.

    3. OTHER OPEX INFLATION (general_inflation %/yr)
       Labour, packaging, nutrients etc. grow with general inflation (2%/yr default).
       Formula: other_opex_y = other_opex * (1 + general_inflation)^(y-1)

    4. LED REPLACEMENT CAPEX (at years defined in led_replacement_years)
       LED grow lights have a ~50,000h lifespan ≈ 5 years at 18h/day operation.
       Replacement cost = equipment_capex * LED_SHARE_OF_EQUIPMENT (default 60%).
       LED hardware prices also deflate ~5%/yr (technology learning curve), so:
       replacement_cost_y = led_cost * (0.95)^(y-1)
       Source: Excel model Replace Invest. column; industry LED lifespan data.

    5. ANNUAL MAINTENANCE RESERVE (annual_maintenance_pct of equipment CapEx/yr)
       2.5% of equipment CapEx reserved annually for repairs and spares.
       Grows with general inflation.
       Formula: maintenance_y = equipment_capex * pct * (1 + inflation)^(y-1)
    """
    from core.schemas import AdvancedFinanceInputs
    adv: AdvancedFinanceInputs = adv

    led_replacement_base = equipment_capex * cfg.LED_SHARE_OF_EQUIPMENT
    forecast, cumulative, payback = [], 0.0, None

    for y in range(1, fin.years + 1):
        # 1. efficiency ramp-up
        eff = min(fin.year1_eff + fin.eff_gain * (y - 1), 1.0)

        # 2. revenue with crop price growth
        revenue_y = total_sales * eff * ((1 + adv.crop_price_growth) ** (y - 1))

        # 3. electricity cost with price growth + optional shock
        elec_y = elec_cost_base * elec_price_multiplier * ((1 + adv.elec_price_growth) ** (y - 1))

        # 4. other opex with general inflation
        other_y = other_opex * ((1 + adv.general_inflation) ** (y - 1))

        # 5. annual maintenance reserve (grows with inflation)
        maintenance_y = equipment_capex * adv.annual_maintenance_pct * ((1 + adv.general_inflation) ** (y - 1))

        # 6. LED replacement — cost deflates 5%/yr due to technology learning curve
        led_replacement_y = 0.0
        if y in adv.led_replacement_years:
            led_replacement_y = led_replacement_base * (0.95 ** (y - 1))

        total_opex_y = elec_y + other_y + maintenance_y
        net_cash = revenue_y - total_opex_y - led_replacement_y
        disc_net = net_cash / ((1 + fin.discount_rate) ** y)
        cumulative += disc_net
        npv_minus_capex = cumulative - capex_net

        if payback is None and npv_minus_capex >= 0:
            payback = y

        forecast.append({
            "Year": y,
            "Revenue (€)": revenue_y,
            "Elec Cost (€)": elec_y,
            "Other OpEx (€)": other_y,
            "Maintenance (€)": maintenance_y,
            "LED Replacement (€)": led_replacement_y,
            "Net Cashflow (€)": net_cash,
            "Discounted (€)": disc_net,
            "Cumulative NPV (€)": cumulative,
            "NPV - CAPEX (€)": npv_minus_capex,
        })

    return pd.DataFrame(forecast), payback
