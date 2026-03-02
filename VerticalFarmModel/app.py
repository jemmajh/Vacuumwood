import streamlit as st
import pandas as pd
import altair as alt

import config as cfg
from ui.styles import apply_branding, vw_section
from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario
from core.nordpool import effective_price_from_csv
from core.model import compute_areas, compute_sales, compute_capex, compute_opex, build_forecast
from core.validation import validate_inputs


#errors = validate_inputs(shares, floors, discount_rate, year1_eff, eff_gain, years)
#if errors:
#    for e in errors:
#        st.error(e)
#    st.stop()


def run():
    apply_branding()
    st.title("")

    # --- Sidebar: Farm
    st.sidebar.header("1. Farm & Building Parameters")
    farm = FarmInputs(
        length_m=st.sidebar.number_input("Inner Length (m)", value=30.0),
        width_m=st.sidebar.number_input("Inner Width (m)", value=20.0),
        height_m=st.sidebar.number_input("Inner Height (m)", value=2.6),
        insulation_m=st.sidebar.number_input("Insulation Thickness (m)", value=0.3),
        floor_usage_eff=st.sidebar.slider("Floor Usage Efficiency", 0.0, 1.0, 0.75),
        floors=st.sidebar.number_input("Number of Floors", min_value=1, value=6),
    )
    areas = compute_areas(farm)
    st.sidebar.markdown(f"**Total Cultivation Area:** {areas['total_cultivatable']:.0f} m²")

    # --- Sidebar: Crops
    st.sidebar.header("2. Products & Yields")
    selected = st.sidebar.multiselect("Select Crops", list(cfg.DEFAULT_YIELD.keys()), default=list(cfg.DEFAULT_YIELD.keys()))
    if not selected:
        st.sidebar.error("Choose at least one crop.")
        st.stop()

    if len(selected) == 1:
        shares = {selected[0]: 1.0}
    else:
        lettuce_share = st.sidebar.slider("Lettuce %", 0.0, 1.0, 0.5)
        shares = {"Lettuce": lettuce_share, "Basil": 1 - lettuce_share}

    yields = {crop: st.sidebar.number_input(f"{crop} Yield (kg/m²/yr)", value=float(cfg.DEFAULT_YIELD[crop])) for crop in selected}
    crops = CropInputs(selected=selected, shares=shares, yields_kg_m2_yr=yields)

    sales_df, total_sales = compute_sales(areas["total_cultivatable"], crops)

    # --- Sidebar: CAPEX (auto)
    st.sidebar.header("3. CAPEX")
    capex = compute_capex(areas["floor_area"], areas["total_cultivatable"])
    st.sidebar.markdown(f"**Total CAPEX:** €{capex['net']:,.0f}")

    # --- Sidebar: Electricity
    st.sidebar.header("4. Electricity Scenario")
    price_mode = st.sidebar.radio(
        "Electricity price input",
        ["Use average €/kWh", "Upload Nordpool CSV", "Use Optimization page (historical)"],
        index=0
    )
    if price_mode == "Use Optimization page (historical)":
        base_price = st.session_state.get("base_price_eur_kwh", cfg.ELEC_PRICE_BASE)
        opt_price = st.session_state.get("opt_price_eur_kwh", cfg.ELEC_PRICE_OPT)

        st.sidebar.markdown(f"**Baseline (avg):** {base_price:.4f} €/kWh")
        st.sidebar.markdown(f"**Optimized:** {opt_price:.4f} €/kWh")
    base_price = cfg.ELEC_PRICE_BASE
    opt_price = cfg.ELEC_PRICE_OPT

    if price_mode == "Use average €/kWh":
        base_price = st.session_state.get("base_price_eur_kwh", cfg.ELEC_PRICE_BASE)
        opt_price = st.session_state.get("opt_price_eur_kwh", cfg.ELEC_PRICE_OPT)
    else:
        uploaded = st.sidebar.file_uploader("Upload Nordpool CSV (hourly prices)", type=["csv"])
        if uploaded is not None:
            dfp = pd.read_csv(uploaded)
            try:
                effective = effective_price_from_csv(dfp)
                st.sidebar.markdown(f"**Effective average price from CSV:** {effective:.3f} €/kWh")
                save_pct = st.sidebar.slider("Optimisation saving (%)", 0, 50, 20)
                base_price = effective
                opt_price = effective * (1 - save_pct / 100.0)
            except ValueError as e:
                st.sidebar.error(str(e))

    scenario_label = st.sidebar.radio("Electricity price scenario", ["Current price model", "Optimised schedule"])
    scenario = ElectricityScenario(
        base_price_eur_kwh=base_price,
        opt_price_eur_kwh=opt_price,
        selected="base" if scenario_label.startswith("Current") else "opt",
    )
    opex = compute_opex(areas["total_cultivatable"], scenario)
    st.session_state["elec_use_kwh"] = opex["elec_use_kwh"]
    st.session_state["other_opex"] = opex["other_opex"]
    st.session_state["price_used"] = opex["price_used"]


    # --- Sidebar: Forecast
    st.sidebar.header("5. Forecast")
    fin = FinanceInputs(
        discount_rate=st.sidebar.number_input("Discount Rate", min_value=0.0, max_value=1.0, value=0.05),
        year1_eff=st.sidebar.number_input("Year 1 Efficiency", 0.0, 1.0, 0.8),
        eff_gain=st.sidebar.number_input("Annual Efficiency Gain", 0.0, 1.0, 0.015),
        years=int(st.sidebar.number_input("Forecast Years", min_value=1, value=10)),
    )
    errors = validate_inputs(
        shares=shares,
        floors=farm.floors,
        discount_rate=fin.discount_rate,
        year1_eff=fin.year1_eff,
        eff_gain=fin.eff_gain,
        years=fin.years,
    )

    if errors:
        for e in errors:
            st.error(e)
        st.stop()


    # --- Tabs
    tab_overview, tab_opex, tab_forecast = st.tabs(["Overview", "OPEX", "Forecast & Cashflow"])

    with tab_overview:
        vw_section("Yearly Sales Summary")
        st.table(sales_df)
        st.metric("Total Yearly Sales", f"€{total_sales:,.0f}")
        st.metric("Total CAPEX", f"€{capex['net']:,.0f}")

    with tab_opex:
        vw_section("Operating Costs")
        st.metric("Total OPEX / year", f"€{opex['yearly_opex']:,.0f}")

    with tab_forecast:
        df_forecast, payback = build_forecast(total_sales, opex["yearly_opex"], capex["net"], fin)
        vw_section("Payback")
        st.metric("Payback Year", payback if payback else "Not reached")

        vw_section("Cashflow & NPV")
        melted = df_forecast.melt("Year", ["Discounted (€)", "Cumulative NPV (€)", "NPV - CAPEX (€)"], "Series", "Value")
        chart = alt.Chart(melted).mark_line(point=True).encode(
            x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
            y="Value:Q",
            color="Series:N",
            tooltip=["Year", "Series", "Value"],
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    run()