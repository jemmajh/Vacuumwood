from typing import Dict, Tuple, Optional
import pandas as pd

from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario
import config as cfg

# --- MUST be first Streamlit call ---
st.set_page_config(
    page_title="VacuumWood Financial Model",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_branding()

# Optional: tighten top padding
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      /* Hide Streamlit default hamburger footer spacing a bit */
      footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Defaults (edit these to match your preferred baseline demo)
# ---------------------------------------------------------
DEFAULT_FARM = dict(
    length_m=30.0,
    width_m=20.0,
    height_m=2.6,
    insulation_m=0.30,
    floor_usage_eff=0.75,
    floors=6,
)

DEFAULT_CROPS = dict(
    selected=["Lettuce", "Basil"],
    shares={"Lettuce": 0.50, "Basil": 0.50},
    yields_kg_m2_yr={"Lettuce": 25.0, "Basil": 18.0},
)

DEFAULT_FIN = dict(
    years=15,
    discount_rate=0.08,
    year1_eff=0.75,
    eff_gain=0.02,
)

DEFAULT_ELEC = dict(
    selected="base",  # "base" or "opt"
    base_price_eur_kwh=0.12,
    opt_price_eur_kwh=0.08,
)

# ---------------------------------------------------------
# OPTIONAL controls (hidden inside expander so UI is clean)
# ---------------------------------------------------------
with st.sidebar:
    st.caption("Controls are optional and hidden by default.")
    show_controls = st.toggle("Show parameters", value=False)

params = {}

if show_controls:
    with st.sidebar.expander("1) Farm & Building", expanded=True):
        params["length_m"] = st.number_input("Inner Length (m)", value=DEFAULT_FARM["length_m"], step=1.0)
        params["width_m"] = st.number_input("Inner Width (m)", value=DEFAULT_FARM["width_m"], step=1.0)
        params["height_m"] = st.number_input("Inner Height (m)", value=DEFAULT_FARM["height_m"], step=0.1)
        params["insulation_m"] = st.number_input("Insulation Thickness (m)", value=DEFAULT_FARM["insulation_m"], step=0.05)
        params["floor_usage_eff"] = st.slider("Floor Usage Efficiency", 0.1, 1.0, DEFAULT_FARM["floor_usage_eff"], 0.05)
        params["floors"] = st.number_input("Number of Floors", min_value=1, value=int(DEFAULT_FARM["floors"]), step=1)

    with st.sidebar.expander("2) Crops", expanded=False):
        selected = st.multiselect("Selected crops", options=list(cfg.DEFAULT_PRICE.keys()), default=DEFAULT_CROPS["selected"])
        if not selected:
            selected = DEFAULT_CROPS["selected"]

        shares = {}
        yields = {}
        st.caption("Shares should sum to 1.0 (we will normalize if not).")

        total_share = 0.0
        for c in selected:
            shares[c] = st.number_input(f"{c} share", min_value=0.0, max_value=1.0,
                                        value=float(DEFAULT_CROPS["shares"].get(c, 0.0)), step=0.05)
            total_share += shares[c]
            yields[c] = st.number_input(f"{c} yield (kg/m²/year)", min_value=0.0,
                                        value=float(DEFAULT_CROPS["yields_kg_m2_yr"].get(c, 10.0)), step=1.0)

        # Normalize shares if needed
        if total_share <= 0:
            shares = DEFAULT_CROPS["shares"]
        else:
            shares = {k: v / total_share for k, v in shares.items()}

        params["crops_selected"] = selected
        params["crops_shares"] = shares
        params["crops_yields"] = yields

    with st.sidebar.expander("3) Electricity", expanded=False):
        scenario_selected = st.radio("Scenario", options=["base", "opt"], index=0 if DEFAULT_ELEC["selected"] == "base" else 1)
        base_price = st.number_input("Base price (€/kWh)", value=float(DEFAULT_ELEC["base_price_eur_kwh"]), step=0.01)
        opt_price = st.number_input("Optimised price (€/kWh)", value=float(DEFAULT_ELEC["opt_price_eur_kwh"]), step=0.01)

        params["elec_selected"] = scenario_selected
        params["elec_base_price"] = base_price
        params["elec_opt_price"] = opt_price

    with st.sidebar.expander("4) Finance", expanded=False):
        params["years"] = st.number_input("Years", min_value=1, value=int(DEFAULT_FIN["years"]), step=1)
        params["discount_rate"] = st.number_input("Discount rate", min_value=0.0, max_value=1.0,
                                                  value=float(DEFAULT_FIN["discount_rate"]), step=0.01)
        params["year1_eff"] = st.number_input("Year 1 efficiency", min_value=0.0, max_value=1.0,
                                              value=float(DEFAULT_FIN["year1_eff"]), step=0.05)
        params["eff_gain"] = st.number_input("Efficiency gain / year", min_value=0.0, max_value=1.0,
                                             value=float(DEFAULT_FIN["eff_gain"]), step=0.01)

# If controls are hidden, use defaults
farm = FarmInputs(**({
    **DEFAULT_FARM,
    **{k: v for k, v in params.items() if k in DEFAULT_FARM}
}))

crops = CropInputs(**({
    **DEFAULT_CROPS,
    "selected": params.get("crops_selected", DEFAULT_CROPS["selected"]),
    "shares": params.get("crops_shares", DEFAULT_CROPS["shares"]),
    "yields_kg_m2_yr": params.get("crops_yields", DEFAULT_CROPS["yields_kg_m2_yr"]),
}))

scenario = ElectricityScenario(**({
    **DEFAULT_ELEC,
    "selected": params.get("elec_selected", DEFAULT_ELEC["selected"]),
    "base_price_eur_kwh": params.get("elec_base_price", DEFAULT_ELEC["base_price_eur_kwh"]),
    "opt_price_eur_kwh": params.get("elec_opt_price", DEFAULT_ELEC["opt_price_eur_kwh"]),
}))

fin = FinanceInputs(**({
    **DEFAULT_FIN,
    "years": params.get("years", DEFAULT_FIN["years"]),
    "discount_rate": params.get("discount_rate", DEFAULT_FIN["discount_rate"]),
    "year1_eff": params.get("year1_eff", DEFAULT_FIN["year1_eff"]),
    "eff_gain": params.get("eff_gain", DEFAULT_FIN["eff_gain"]),
}))

# ---------------------------------------------------------
# Compute
# ---------------------------------------------------------
areas = compute_areas(farm)
sales_df, total_sales = compute_sales(areas["total_cultivatable"], crops)
capex = compute_capex(areas["floor_area"], areas["total_cultivatable"])
opex = compute_opex(areas["total_cultivatable"], scenario)
forecast_df, payback_year = build_forecast(
    total_sales=total_sales,
    yearly_opex=opex["yearly_opex"],
    capex_net=capex["net"],
    fin=fin
)

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
tab_overview, tab_opex, tab_forecast = st.tabs(["Overview", "OPEX", "Forecast & Cashflow"])

with tab_overview:
    vw_section("Yearly Sales Summary")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Yearly Sales (€)", f"{total_sales:,.0f}")
    c2.metric("Total CAPEX (net, €)", f"{capex['net']:,.0f}")
    c3.metric("Payback (year)", "—" if payback_year is None else str(payback_year))

    st.dataframe(sales_df, use_container_width=True)

    vw_section("Key Areas")
    a1, a2, a3 = st.columns(3)
    a1.metric("Floor Area (m²)", f"{areas['floor_area']:,.0f}")
    a2.metric("Cultivable / floor (m²)", f"{areas['cultivable_per_floor']:,.0f}")
    a3.metric("Total Cultivation (m²)", f"{areas['total_cultivatable']:,.0f}")

with tab_opex:
    vw_section("Electricity & Operating Costs")

    c1, c2, c3 = st.columns(3)
    c1.metric("Electricity use (kWh/year)", f"{opex['elec_use_kwh']:,.0f}")
    c2.metric("Electricity price used (€/kWh)", f"{opex['price_used']:.3f}")
    c3.metric("Yearly OPEX (€)", f"{opex['yearly_opex']:,.0f}")

    st.markdown("**Comparison**")
    compare = {
        "Base": [opex["elec_cost_base"], opex["yearly_opex_base"]],
        "Optimised": [opex["elec_cost_opt"], opex["yearly_opex_opt"]],
    }
    comp_df = pd.DataFrame(compare, index=["Electricity (€)", "Total OPEX (€)"])
    st.dataframe(comp_df, use_container_width=True)

with tab_forecast:
    vw_section("NPV / Cashflow Forecast")

    st.dataframe(forecast_df, use_container_width=True)

    # Optional chart
    st.line_chart(forecast_df.set_index("Year")[["Cumulative NPV (€)", "NPV - CAPEX (€)"]])

# Helpful hint at bottom
st.caption("Tip: open the **electricity optimization** page from the left page menu.")