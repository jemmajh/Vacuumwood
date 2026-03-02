import streamlit as st

from ui.styles import apply_branding, vw_section
from core.model import (
    compute_areas,
    compute_sales,
    compute_capex,
    compute_opex,
    build_forecast,
)

# Schemas you already use in model.py
from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario

import config as cfg


# -----------------------------
# Page config (must be first)
# -----------------------------
st.set_page_config(
    page_title="VacuumWood Financial Model",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_branding()

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

vw_section("Financial Model Summary")
st.write(
    "This page shows baseline outputs using default assumptions. "
    "For historical Nordpool scheduling, use the **electricity optimization** page."
)

# -----------------------------
# Build DEFAULT inputs (no UI)
# -----------------------------
# Update these defaults if you want different “baseline” numbers:
farm = FarmInputs(
    length_m=30.0,
    width_m=20.0,
    height_m=2.6,
    insulation_thickness_m=0.30,
    floor_usage_eff=0.75,
    floors=6,
)

# Crop defaults
# These keys must match your cfg.DEFAULT_PRICE keys and crop names used in yields/shares.
selected = ["Lettuce", "Basil"]
crops = CropInputs(
    selected=selected,
    shares={"Lettuce": 0.5, "Basil": 0.5},
    yields_kg_m2_yr={"Lettuce": 20.0, "Basil": 15.0},
)

# Finance defaults
fin = FinanceInputs(
    years=10,
    discount_rate=0.08,
    year1_eff=0.8,
    eff_gain=0.05,
)

# Electricity defaults
scenario = ElectricityScenario(
    selected="base",  # "base" or "opt"
    base_price_eur_kwh=0.12,
    opt_price_eur_kwh=0.09,
)

# -----------------------------
# Run model
# -----------------------------
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

# -----------------------------
# Display
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total yearly sales (€)", f"{total_sales:,.0f}")

with col2:
    st.metric("CAPEX net (€)", f"{capex['net']:,.0f}")

with col3:
    st.metric("Yearly OPEX (€)", f"{opex['yearly_opex']:,.0f}")

with col4:
    st.metric("Payback (year)", str(payback_year) if payback_year is not None else "—")

vw_section("Sales split")
st.dataframe(sales_df, use_container_width=True)

vw_section("Forecast")
st.dataframe(forecast_df, use_container_width=True)

st.markdown("---")
st.caption("VacuumWood • Vertical Farming Financial Model")