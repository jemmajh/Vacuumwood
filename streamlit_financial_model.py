import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------------------
# Company-only configuration (edit here, not in the UI)
# -------------------------------------------------------------

# Default crop performance
DEFAULT_YIELD = {'Lettuce': 70.0, 'Basil': 30.0}  # kg per m² per year
DEFAULT_PRICE = {'Lettuce': 7.0, 'Basil': 20.0}   # € per kg (hidden from clients)

# CAPEX model (simple rule-of-thumb, editable by company)
CAPEX_BUILDING_PER_M2 = 500.0     # €/m² of floor area
CAPEX_EQUIPMENT_PER_M2 = 2000.0   # €/m² of cultivation area
CAPEX_OTHER_FIXED = 50_000.0      # other investments (€)
CAPEX_SUBSIDY_SHARE = 0.3         # 30% of gross capex is subsidised

# OPEX model (electricity + "other" costs)
ELEC_KWH_PER_M2_YEAR = 350.0      # kWh per m² cultivation per year
ELEC_PRICE_BASE = 0.15            # €/kWh, current market
ELEC_PRICE_OPT = 0.10             # €/kWh, "optimised" schedule scenario
OTHER_OPEX_PER_M2_YEAR = 80.0     # €/m² cultivation per year (labour, maintenance, etc.)

st.set_page_config(page_title="Vertical Farming Financial Model", layout="wide")


def main():
    st.title("Vertical Farming Financial Model")

    # =========================================================
    # 1. Farm & Building Parameters
    # =========================================================
    st.sidebar.header("1. Farm & Building Parameters")
    length = st.sidebar.number_input("Inner Length (m)", min_value=0.0, value=30.0)
    width = st.sidebar.number_input("Inner Width (m)", min_value=0.0, value=20.0)
    height = st.sidebar.number_input("Inner Height (m)", min_value=0.0, value=2.6)
    insulation = st.sidebar.number_input("Insulation Thickness (m)", min_value=0.0, value=0.3)

    floor_area = length * width
    roof_area = floor_area
    wall_area_long = 2 * length * height  # two long walls
    wall_area_short = 2 * (width - 2 * insulation) * height
    envelope_area = roof_area + wall_area_long + wall_area_short

    st.sidebar.markdown(f"**Floor Area:** {floor_area:.0f} m²")
    st.sidebar.markdown(f"**Building Envelope Area:** {envelope_area:.0f} m²")

    floor_eff = st.sidebar.slider("Floor Usage Efficiency", 0.0, 1.0, 0.75, step=0.05)
    floors = st.sidebar.number_input("Number of Floors", min_value=1, value=6)
    cultivable_per_floor = floor_area * floor_eff
    total_cultivable = cultivable_per_floor * floors
    st.sidebar.markdown(f"**Cultivation Area per Floor:** {cultivable_per_floor:.0f} m²")
    st.sidebar.markdown(f"**Total Cultivation Area:** {total_cultivable:.0f} m²")

    # =========================================================
    # 2. Products & Yields
    # =========================================================
    st.sidebar.header("2. Products & Yields")
    products = st.sidebar.multiselect(
        "Select Crops to Grow",
        options=list(DEFAULT_YIELD.keys()),
        default=list(DEFAULT_YIELD.keys())
    )
    if len(products) == 0:
        st.sidebar.error("Select at least one crop.")
        return
    elif len(products) == 1:
        shares = {products[0]: 1.0}
    else:
        lettuce_share = st.sidebar.slider(
            "Lettuce % of Cultivation Area", 0.0, 1.0, 0.5, step=0.05
        )
        # Simple 2-crop split: lettuce + basil
        shares = {'Lettuce': lettuce_share, 'Basil': 1.0 - lettuce_share}

    data = []
    total_sales = 0.0
    for crop in products:
        # Yield is adjustable in the UI
        yld = st.sidebar.number_input(
            f"{crop} Yield (kg/m²/yr)",
            min_value=0.0,
            value=DEFAULT_YIELD[crop]
        )
        # Price is fixed from DEFAULT_PRICE (company can change in code)
        price = DEFAULT_PRICE[crop]
        area = total_cultivable * shares.get(crop, 0.0)
        revenue = area * yld * price
        total_sales += revenue
        data.append({
            'Product': crop,
            'Area (m²)': area,
            'Yield (kg)': area * yld,
            'Revenue (€)': revenue
        })

    st.subheader("Yearly Sales Summary")
    sales_df = pd.DataFrame(data)
    st.table(sales_df.set_index('Product'))
    st.metric("Total Yearly Sales", f"€{total_sales:,.0f}")

    # =========================================================
    # 3. CAPEX – Initial Investment Costs (auto + optional override)
    # =========================================================
    st.sidebar.header("3. Initial Investment Costs (CAPEX)")

    # Auto-calculated CAPEX based on area
    auto_building_cost = floor_area * CAPEX_BUILDING_PER_M2
    auto_equipment_cost = total_cultivable * CAPEX_EQUIPMENT_PER_M2
    auto_other_cost = CAPEX_OTHER_FIXED
    auto_gross_capex = auto_building_cost + auto_equipment_cost + auto_other_cost
    auto_subsidy = auto_gross_capex * CAPEX_SUBSIDY_SHARE
    auto_total_investment = auto_gross_capex - auto_subsidy

    use_manual_capex = st.sidebar.checkbox("Override CAPEX manually", value=False)

    if use_manual_capex:
        building_cost = st.sidebar.number_input(
            "Building Cost (€)", min_value=0.0, value=float(auto_building_cost)
        )
        equipment_cost = st.sidebar.number_input(
            "Equipment Cost (€)", min_value=0.0, value=float(auto_equipment_cost)
        )
        other_cost = st.sidebar.number_input(
            "Other Cost (€)", min_value=0.0, value=float(auto_other_cost)
        )
        subsidy = st.sidebar.number_input(
            "Subsidies (€)", min_value=0.0, value=float(auto_subsidy)
        )
    else:
        # Show auto-calculation as read-only summary in sidebar
        st.sidebar.markdown(
            f"*Building CAPEX (auto):* €{auto_building_cost:,.0f}<br>"
            f"*Equipment CAPEX (auto):* €{auto_equipment_cost:,.0f}<br>"
            f"*Other CAPEX:* €{auto_other_cost:,.0f}<br>"
            f"*Subsidy (auto):* €{auto_subsidy:,.0f}",
            unsafe_allow_html=True
        )
        building_cost = auto_building_cost
        equipment_cost = auto_equipment_cost
        other_cost = auto_other_cost
        subsidy = auto_subsidy

    total_investment = building_cost + equipment_cost + other_cost - subsidy
    st.metric("Total Initial Investment (CAPEX)", f"€{total_investment:,.0f}")

    # =========================================================
    # 4. OPEX & Electricity Price Scenarios
    # =========================================================
    st.sidebar.header("4. Electricity Scenario & OPEX")

    # Electricity use and costs for base and optimised cases
    electricity_use_kwh = total_cultivable * ELEC_KWH_PER_M2_YEAR
    elec_cost_base = electricity_use_kwh * ELEC_PRICE_BASE
    elec_cost_opt = electricity_use_kwh * ELEC_PRICE_OPT

    other_opex = total_cultivable * OTHER_OPEX_PER_M2_YEAR

    total_opex_base = elec_cost_base + other_opex
    total_opex_opt = elec_cost_opt + other_opex

    scenario = st.sidebar.radio(
        "Electricity price scenario",
        options=["Current price", "Optimised price schedule"],
        index=0
    )

    if scenario == "Current price":
        elec_price_used = ELEC_PRICE_BASE
        yearly_elec_cost = elec_cost_base
        total_opex = total_opex_base
        savings_vs_base = 0.0
    else:
        elec_price_used = ELEC_PRICE_OPT
        yearly_elec_cost = elec_cost_opt
        total_opex = total_opex_opt
        savings_vs_base = total_opex_base - total_opex

    st.subheader("Operating Costs (OPEX)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Yearly electricity cost", f"€{yearly_elec_cost:,.0f}")
    col2.metric("Other yearly OPEX", f"€{other_opex:,.0f}")
    col3.metric("Total yearly OPEX", f"€{total_opex:,.0f}")

    if scenario == "Optimised price schedule":
        st.caption(
            f"Electricity optimisation reduces yearly OPEX by "
            f"€{savings_vs_base:,.0f} compared to current price."
        )
    st.caption(
        f"Electricity price used in this scenario: {elec_price_used:.2f} €/kWh."
    )

    # =========================================================
    # 5. Forecast & Payback (using net cash flow = Sales – OPEX)
    # =========================================================
    st.sidebar.header("5. Forecast & Payback")
    discount_rate = st.sidebar.number_input(
        "Discount Rate", min_value=0.0, max_value=1.0, value=0.05, format="%.2f"
    )
    year1_eff = st.sidebar.number_input(
        "Year 1 Operational Efficiency",
        min_value=0.0, max_value=1.0, value=0.8
    )
    eff_gain = st.sidebar.number_input(
        "Annual Efficiency Gain", min_value=0.0, value=0.015
    )
    years = st.sidebar.number_input(
        "Forecast Years", min_value=1, value=10
    )

    forecast = []
    cumulative_npv = 0.0
    payback_year = None

    for y in range(1, int(years) + 1):
        eff = min(year1_eff + (y - 1) * eff_gain, 1.0)
        # sales at that efficiency
        sales = total_sales * eff
        # net cash flow after OPEX
        net_cash = sales - total_opex
        # discounted net cash flow
        disc_net = net_cash / ((1 + discount_rate) ** y)
        cumulative_npv += disc_net
        npv_minus_investment = cumulative_npv - total_investment

        if payback_year is None and npv_minus_investment >= 0:
            payback_year = y

        forecast.append({
            'Year': y,
            'Efficiency': eff,
            'Sales (€)': sales,
            'Net cash flow (€)': net_cash,
            'Discounted net (€)': disc_net,
            'Cumulative NPV (€)': cumulative_npv,
            'NPV minus investment (€)': npv_minus_investment
        })

    fc_df = pd.DataFrame(forecast)

    # Payback summary
    st.subheader("Payback Summary")
    if payback_year is not None:
        st.metric("Payback year", f"Year {payback_year}")
    else:
        st.metric("Payback year", "Not reached within forecast")

    # =========================================================
    # 6. Profitability / Cashflow Visualisations
    # =========================================================
    st.subheader("Profitability & Cash Flow")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Discounted NPV curves**")
        st.line_chart(
            fc_df.set_index('Year')[[
                'Discounted net (€)',
                'Cumulative NPV (€)',
                'NPV minus investment (€)'
            ]]
        )

    with c2:
        st.markdown("**Yearly net cash flow**")
        st.bar_chart(
            fc_df.set_index('Year')[['Net cash flow (€)']]
        )

    st.subheader("10-year Forecast Table")
    st.dataframe(
        fc_df.style.format({
            'Efficiency': '{:.0%}',
            'Sales (€)': '€{:.0f}',
            'Net cash flow (€)': '€{:.0f}',
            'Discounted net (€)': '€{:.0f}',
            'Cumulative NPV (€)': '€{:.0f}',
            'NPV minus investment (€)': '€{:.0f}'
        }),
        use_container_width=True
    )


if __name__ == '__main__':
    main()