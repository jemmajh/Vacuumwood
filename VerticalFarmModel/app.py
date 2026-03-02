# app.py
from __future__ import annotations

import streamlit as st

# MUST be the first Streamlit call
st.set_page_config(
    page_title="VacuumWood Financial Model",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Imports (after page config) ----
from ui.styles import apply_branding, vw_section  # noqa: E402
from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario  # noqa: E402
from core.model import (  # noqa: E402
    compute_areas,
    compute_sales,
    compute_capex,
    compute_opex,
    build_forecast,
)

try:
    import config as cfg  # noqa: E402
except Exception:
    cfg = None


def _cfg_get(name: str, fallback):
    """Safe getter for config values."""
    if cfg is None:
        return fallback
    return getattr(cfg, name, fallback)


def build_default_inputs():
    # Farm defaults
    farm = FarmInputs(
        length_m=float(_cfg_get("DEFAULT_LENGTH_M", 30.0)),
        width_m=float(_cfg_get("DEFAULT_WIDTH_M", 20.0)),
        height_m=float(_cfg_get("DEFAULT_HEIGHT_M", 2.6)),
        insulation_m=float(_cfg_get("DEFAULT_INSULATION_M", 0.30)),
        floor_usage_eff=float(_cfg_get("DEFAULT_FLOOR_USAGE_EFF", 0.75)),
        floors=int(_cfg_get("DEFAULT_FLOORS", 6)),
    )

    # Crop defaults
    default_selected = _cfg_get("DEFAULT_CROPS_SELECTED", ["Lettuce", "Basil"])
    default_shares = _cfg_get("DEFAULT_CROP_SHARES", {"Lettuce": 0.5, "Basil": 0.5})
    default_yields = _cfg_get(
        "DEFAULT_CROP_YIELDS",
        {"Lettuce": 15.0, "Basil": 20.0},  # kg/m²/year placeholders
    )

    crops = CropInputs(
        selected=list(default_selected),
        shares=dict(default_shares),
        yields_kg_m2_yr=dict(default_yields),
    )

    # Finance defaults
    fin = FinanceInputs(
        discount_rate=float(_cfg_get("DEFAULT_DISCOUNT_RATE", 0.08)),
        year1_eff=float(_cfg_get("DEFAULT_YEAR1_EFF", 0.85)),
        eff_gain=float(_cfg_get("DEFAULT_EFF_GAIN", 0.03)),
        years=int(_cfg_get("DEFAULT_FORECAST_YEARS", 15)),
    )

    # Electricity defaults
    scenario = ElectricityScenario(
        base_price_eur_kwh=float(_cfg_get("DEFAULT_BASE_PRICE_EUR_KWH", 0.10)),
        opt_price_eur_kwh=float(_cfg_get("DEFAULT_OPT_PRICE_EUR_KWH", 0.07)),
        selected=str(_cfg_get("DEFAULT_ELEC_SELECTED", "base")),  # "base" or "opt"
    )

    return farm, crops, fin, scenario


def main():
    apply_branding()

    # Small layout polish
    st.markdown(
        """
        <style>
          .block-container { padding-top: 1.0rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Baseline financial outputs for a vertical farm. "
        "Use the **Electricity Optimization** page to explore historical scheduling strategies."
    )

    farm, crops, fin, scenario = build_default_inputs()

    # Optional inputs, but not “big sidebar”
    with st.expander("Assumptions (optional)", expanded=False):
        c1, c2, c3 = st.columns(3)

        with c1:
            length_m = st.number_input("Inner Length (m)", min_value=1.0, value=float(farm.length_m), step=1.0)
            width_m = st.number_input("Inner Width (m)", min_value=1.0, value=float(farm.width_m), step=1.0)
            height_m = st.number_input("Inner Height (m)", min_value=1.0, value=float(farm.height_m), step=0.1)

        with c2:
            insulation_m = st.number_input("Insulation Thickness (m)", min_value=0.0, value=float(farm.insulation_m), step=0.05)
            floor_usage_eff = st.slider("Floor Usage Efficiency", min_value=0.10, max_value=1.00, value=float(farm.floor_usage_eff), step=0.01)
            floors = st.number_input("Number of Floors", min_value=1, value=int(farm.floors), step=1)

        with c3:
            selected_mode = st.radio(
                "Electricity price scenario",
                options=["base", "opt"],
                index=0 if scenario.selected == "base" else 1,
                horizontal=True,
            )
            base_price = st.number_input("Base price (€/kWh)", min_value=0.0, value=float(scenario.base_price_eur_kwh), step=0.01)
            opt_price = st.number_input("Optimised price (€/kWh)", min_value=0.0, value=float(scenario.opt_price_eur_kwh), step=0.01)

        farm = FarmInputs(
            length_m=float(length_m),
            width_m=float(width_m),
            height_m=float(height_m),
            insulation_m=float(insulation_m),
            floor_usage_eff=float(floor_usage_eff),
            floors=int(floors),
        )

        scenario = ElectricityScenario(
            base_price_eur_kwh=float(base_price),
            opt_price_eur_kwh=float(opt_price),
            selected=str(selected_mode),
        )

        # (Keep crops/finance editable later if you want—this keeps it simple for now.)

    # ---- Compute outputs ----
    areas = compute_areas(farm)
    sales_df, total_sales = compute_sales(areas["total_cultivatable"], crops)
    capex = compute_capex(areas["floor_area"], areas["total_cultivatable"])
    opex = compute_opex(areas["total_cultivatable"], scenario)
    forecast_df, payback_year = build_forecast(total_sales, opex["yearly_opex"], capex["net"], fin)

    # ---- Display ----
    tab_overview, tab_opex, tab_forecast = st.tabs(["Overview", "OPEX", "Forecast & Cashflow"])

    with tab_overview:
        vw_section("Farm summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Floor area (m²)", f"{areas['floor_area']:,.0f}")
        m2.metric("Cultivable / floor (m²)", f"{areas['cultivable_per_floor']:,.0f}")
        m3.metric("Total cultivatable (m²)", f"{areas['total_cultivatable']:,.0f}")
        m4.metric("Floors", f"{farm.floors}")

        vw_section("Yearly sales summary")
        st.dataframe(sales_df.style.format({"Area (m²)": "{:,.0f}", "Revenue (€)": "€{:,.0f}"}), use_container_width=True)
        st.metric("Total yearly sales", f"€{total_sales:,.0f}")

        vw_section("CAPEX")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total CAPEX (gross)", f"€{capex['gross']:,.0f}")
        c2.metric("Subsidy", f"€{capex['subsidy']:,.0f}")
        c3.metric("CAPEX (net)", f"€{capex['net']:,.0f}")

        if payback_year is None:
            st.info("Payback was not reached within the forecast horizon.")
        else:
            st.success(f"Estimated payback year: **Year {payback_year}**")

    with tab_opex:
        vw_section("Electricity and operating costs")
        c1, c2, c3 = st.columns(3)
        c1.metric("Electricity use (kWh/year)", f"{opex['elec_use_kwh']:,.0f}")
        c2.metric("Price used (€/kWh)", f"{opex['price_used']:.3f}")
        c3.metric("Electricity cost (€)", f"€{opex['elec_cost']:,.0f}")

        st.divider()
        c4, c5 = st.columns(2)
        c4.metric("Other OPEX (€)", f"€{opex['other_opex']:,.0f}")
        c5.metric("Total yearly OPEX (€)", f"€{opex['yearly_opex']:,.0f}")

        with st.expander("Compare base vs optimised"):
            st.write(
                {
                    "elec_cost_base": opex.get("elec_cost_base"),
                    "elec_cost_opt": opex.get("elec_cost_opt"),
                    "yearly_opex_base": opex.get("yearly_opex_base"),
                    "yearly_opex_opt": opex.get("yearly_opex_opt"),
                }
            )

    with tab_forecast:
        vw_section("Forecast table")
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

        vw_section("NPV - CAPEX over time")
        st.line_chart(forecast_df.set_index("Year")["NPV - CAPEX (€)"])

    st.markdown("---")
    st.caption("VacuumWood • Vertical Farming Financial Model")


if __name__ == "__main__":
    main()