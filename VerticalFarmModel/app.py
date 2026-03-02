# VerticalFarmModel/app.py
from __future__ import annotations

import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------
# Make imports work reliably on Streamlit Cloud
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent  # VerticalFarmModel/
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Now project imports
from ui.styles import apply_branding, vw_section

# Core model + schemas
from core.model import (
    compute_areas,
    compute_sales,
    compute_capex,
    compute_opex,
    build_forecast,
)
from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario

import config as cfg


# ---------------------------------------------------------------------
# Page config MUST be the first Streamlit call
# ---------------------------------------------------------------------
st.set_page_config(page_title="VacuumWood Financial Model", layout="wide")


# ---------------------------------------------------------------------
# Helper: safe formatting
# ---------------------------------------------------------------------
def eur(x: float) -> str:
    return f"€{x:,.0f}"


def kwh(x: float) -> str:
    return f"{x:,.0f} kWh"


# ---------------------------------------------------------------------
# Default inputs (NO big UI by default)
# You can tune these to your preferred “baseline”.
# ---------------------------------------------------------------------
def default_inputs():
    farm = FarmInputs(
        length_m=30.0,
        width_m=20.0,
        height_m=2.6,
        insulation_m=0.30,
        floor_usage_eff=0.75,
        floors=6,
    )

    # Pick crops that exist in cfg.DEFAULT_PRICE
    # Shares must sum to 1.0
    crops = CropInputs(
        selected=["Lettuce", "Basil"],
        shares={"Lettuce": 0.5, "Basil": 0.5},
        yields_kg_m2_yr={
            "Lettuce": 25.0,
            "Basil": 18.0,
        },
    )

    scenario = ElectricityScenario(
        selected="base",               # "base" or "opt"
        base_price_eur_kwh=0.12,
        opt_price_eur_kwh=0.08,
    )

    fin = FinanceInputs(
        years=15,
        discount_rate=0.08,
        year1_eff=0.85,
        eff_gain=0.03,
    )

    return farm, crops, scenario, fin


# ---------------------------------------------------------------------
# Branding + small layout tweaks
# ---------------------------------------------------------------------
apply_branding()

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
      /* Optional: slightly calmer sidebar */
      section[data-testid="stSidebar"] { width: 320px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Sidebar (hidden-ish): only advanced controls
# ---------------------------------------------------------------------
farm, crops, scenario, fin = default_inputs()

with st.sidebar:
    st.title("Settings")

    with st.expander("Advanced settings", expanded=False):
        st.subheader("Farm")
        farm.length_m = st.number_input("Inner Length (m)", 1.0, 500.0, float(farm.length_m), 0.5)
        farm.width_m = st.number_input("Inner Width (m)", 1.0, 500.0, float(farm.width_m), 0.5)
        farm.height_m = st.number_input("Inner Height (m)", 1.0, 20.0, float(farm.height_m), 0.1)
        farm.insulation_m = st.number_input("Insulation Thickness (m)", 0.0, 2.0, float(farm.insulation_m), 0.05)
        farm.floor_usage_eff = st.slider("Floor Usage Efficiency", 0.10, 1.00, float(farm.floor_usage_eff), 0.01)
        farm.floors = st.number_input("Number of Floors", 1, 60, int(farm.floors), 1)

        st.subheader("Electricity")
        scenario.base_price_eur_kwh = st.number_input("Base price €/kWh", 0.0, 2.0, float(scenario.base_price_eur_kwh), 0.01)
        scenario.opt_price_eur_kwh = st.number_input("Optimised price €/kWh", 0.0, 2.0, float(scenario.opt_price_eur_kwh), 0.01)
        scenario.selected = st.radio(
            "Electricity scenario used in totals",
            options=["base", "opt"],
            index=0 if scenario.selected == "base" else 1,
            horizontal=True,
        )

        st.subheader("Finance")
        fin.years = st.number_input("Forecast years", 1, 40, int(fin.years), 1)
        fin.discount_rate = st.number_input("Discount rate", 0.0, 0.50, float(fin.discount_rate), 0.01)
        fin.year1_eff = st.number_input("Year 1 efficiency", 0.0, 1.0, float(fin.year1_eff), 0.01)
        fin.eff_gain = st.number_input("Efficiency gain / year", 0.0, 0.20, float(fin.eff_gain), 0.01)

    st.caption("Tip: the electricity optimisation page is in the left menu (multi-page app).")


# ---------------------------------------------------------------------
# Compute model
# ---------------------------------------------------------------------
try:
    areas = compute_areas(farm)
    sales_df, total_sales = compute_sales(areas["total_cultivatable"], crops)
    capex = compute_capex(areas["floor_area"], areas["total_cultivatable"])
    opex = compute_opex(areas["total_cultivatable"], scenario)
    forecast_df, payback_year = build_forecast(
        total_sales=total_sales,
        yearly_opex=opex["yearly_opex"],
        capex_net=capex["net"],
        fin=fin,
    )
except Exception as e:
    st.error("The app couldn’t compute the model. This is usually an import/schema mismatch.")
    st.exception(e)
    st.stop()


# ---------------------------------------------------------------------
# Main page UI
# ---------------------------------------------------------------------
vw_section("Overview")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total cultivatable area", f"{areas['total_cultivatable']:,.0f} m²")
m2.metric("Total yearly sales", eur(total_sales))
m3.metric("Total CAPEX (net)", eur(capex["net"]))
m4.metric("Payback year", str(payback_year) if payback_year is not None else "—")

tabs = st.tabs(["Overview", "OPEX", "Forecast & Cashflow"])

# -------------------------
# TAB: Overview
# -------------------------
with tabs[0]:
    colA, colB = st.columns([1.2, 1.0], gap="large")

    with colA:
        vw_section("Yearly Sales Summary")
        # show sales table nicely
        df_show = sales_df.copy()
        st.dataframe(df_show.style.format({"Area (m²)": "{:,.0f}", "Revenue (€)": "€{:,.0f}"}), use_container_width=True)

    with colB:
        vw_section("CAPEX Breakdown")
        capex_break = pd.DataFrame(
            [
                ("Building", capex["build"]),
                ("Equipment", capex["eq"]),
                ("Other fixed", capex["other"]),
                ("Subsidy (estimate)", -capex["subsidy"]),
                ("Net CAPEX", capex["net"]),
            ],
            columns=["Item", "€"],
        )
        st.dataframe(capex_break.style.format({"€": "€{:,.0f}"}), use_container_width=True)

        st.caption(
            "CAPEX subsidy and unit costs come from your `config.py` values "
            "(kept ‘hidden’ from the UI, as intended)."
        )

# -------------------------
# TAB: OPEX
# -------------------------
with tabs[1]:
    vw_section("Operating Expenses (Yearly)")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.metric("Electricity usage", kwh(opex["elec_use_kwh"]))
        st.metric("Electricity price used", f"€{opex['price_used']:.3f} / kWh")
        st.metric("Electricity cost", eur(opex["elec_cost"]))

    with col2:
        st.metric("Other OPEX", eur(opex["other_opex"]))
        st.metric("Total yearly OPEX", eur(opex["yearly_opex"]))

    st.markdown("---")
    vw_section("Scenario comparison")

    compare = pd.DataFrame(
        [
            ("Base", opex["elec_cost_base"], opex["yearly_opex_base"]),
            ("Optimised", opex["elec_cost_opt"], opex["yearly_opex_opt"]),
        ],
        columns=["Scenario", "Electricity (€)", "Total OPEX (€)"],
    )
    st.dataframe(compare.style.format({"Electricity (€)": "€{:,.0f}", "Total OPEX (€)": "€{:,.0f}"}), use_container_width=True)

# -------------------------
# TAB: Forecast
# -------------------------
with tabs[2]:
    vw_section("Forecast (Discounted Cashflow)")

    st.dataframe(
        forecast_df.style.format(
            {
                "Net Cashflow (€)": "€{:,.0f}",
                "Discounted (€)": "€{:,.0f}",
                "Cumulative NPV (€)": "€{:,.0f}",
                "NPV - CAPEX (€)": "€{:,.0f}",
            }
        ),
        use_container_width=True,
    )

    # Optional: quick line chart
    vw_section("NPV trajectory")
    chart_df = forecast_df.set_index("Year")[["NPV - CAPEX (€)"]]
    st.line_chart(chart_df)

    if payback_year is not None:
        st.success(f"Payback occurs in year {payback_year} (discounted).")
    else:
        st.info("Payback not reached within the forecast horizon.")


st.markdown("---")
st.caption("VacuumWood • Vertical Farming Financial Model")