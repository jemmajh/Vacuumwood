import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Company-only configuration

# Default crop performance
DEFAULT_YIELD = {'Lettuce': 70.0, 'Basil': 30.0}  # kg per m² per year
DEFAULT_PRICE = {'Lettuce': 7.0, 'Basil': 20.0}   # € per kg (hidden from clients)

# CAPEX model (editable by company)
CAPEX_BUILDING_PER_M2 = 500.0     # €/m² of floor area
CAPEX_EQUIPMENT_PER_M2 = 2000.0   # €/m² of cultivation area
CAPEX_OTHER_FIXED = 50_000.0      # other investments (€)
CAPEX_SUBSIDY_SHARE = 0.3         # 30% of gross capex is subsidised

# OPEX model (electricity + other costs)
ELEC_KWH_PER_M2_YEAR = 350.0      # kWh per m² cultivation per year
ELEC_PRICE_BASE = 0.15            # €/kWh
ELEC_PRICE_OPT = 0.10             # €/kWh (optimised schedule)
OTHER_OPEX_PER_M2_YEAR = 80.0     # €/m² cultivation per year

# Streamlit Configuration
st.set_page_config(
    page_title="Vacuumwood Financial Model",
    layout="wide"
)

# Vacuumwood Logo
st.markdown(
    """
<style>
    .vw-logo {
        font-weight: 700;
        font-size: 42px;
        line-height: 1.1;
        letter-spacing: 4px;
    }
    .vw-black { color: #000000; }
    .vw-green { color: #3CB371; }
    .vw-container {
        text-align: center;
        margin-top: 10px;
        margin-bottom: 4px;
    }
</style>

<div class="vw-container">
    <div class="vw-logo">
        <span class="vw-black">V A C U U M</span><br>
        <span class="vw-black">W O O D.</span><br>
        <span class="vw-green">T E C H</span>
    </div>
</div>
""",
    unsafe_allow_html=True
)

st.markdown(
    """
<p style='text-align:center; font-size:13px; color:#555; margin-top:-5px;'>
    Vertical Farming Financial Model – Powered by Vacuumwood Technology
</p>
""",
    unsafe_allow_html=True
)

# Global CSS: lighter sidebar, green buttons, tables, subtitles
st.markdown(
    """
<style>
/* Buttons */
.stButton > button {
    background-color: #3CB371;
    color: white;
    border-radius: 6px;
    border: none;
    padding: 0.4rem 1rem;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #34a165;
}

/* Light sidebar */
[data-testid="stSidebar"] {
    background-color: #F4F4F4 !important;
}
[data-testid="stSidebar"] * {
    color: #000 !important;
}
[data-testid="stSidebar"] h2 {
    color: #3CB371 !important;
}

/* Subheaders */
h2 {
    font-size: 20px !important;
    font-weight: 600 !important;
}

/* Tables */
thead tr th {
    background-color: #0E1A25 !important;
    color: #fff !important;
    font-weight: 600;
}
tbody tr:nth-child(even) { background-color: #F5F7FA !important; }
tbody tr:nth-child(odd)  { background-color: #FFFFFF !important; }
tbody tr:hover { background-color: #E3F3EB !important; }

.dataframe th {
    background-color: #0E1A25 !important;
    color: #FFFFFF !important;
}
</style>
""",
    unsafe_allow_html=True
)

# section header
def vw_section(title):
    st.markdown(
        f"""
        <div style='font-size:18px; font-weight:700; color:#000000; margin-top:22px; margin-bottom:8px;'>
            • {title}
        </div>
        """,
        unsafe_allow_html=True
    )

# MAIN APPLICATION
def main():
    st.title("")

    # SIDEBAR 
    st.sidebar.header("1. Farm & Building Parameters")
    length = st.sidebar.number_input("Inner Length (m)", value=30.0)
    width = st.sidebar.number_input("Inner Width (m)", value=20.0)
    height = st.sidebar.number_input("Inner Height (m)", value=2.6)
    insulation = st.sidebar.number_input("Insulation Thickness (m)", value=0.3)

    floor_area = length * width
    cultivable_per_floor = floor_area * st.sidebar.slider("Floor Usage Efficiency", 0.0, 1.0, 0.75)
    floors = st.sidebar.number_input("Number of Floors", min_value=1, value=6)
    total_cultivatable = cultivable_per_floor * floors

    st.sidebar.markdown(f"**Total Cultivation Area:** {total_cultivatable:.0f} m²")

    # Products
    st.sidebar.header("2. Products & Yields")
    products = st.sidebar.multiselect("Select Crops", ["Lettuce", "Basil"], default=["Lettuce", "Basil"])
    if len(products) == 0:
        st.sidebar.error("Choose at least one crop.")
        return

    if len(products) == 1:
        shares = {products[0]: 1.0}
    else:
        lettuce_share = st.sidebar.slider("Lettuce %", 0.0, 1.0, 0.5)
        shares = {"Lettuce": lettuce_share, "Basil": 1 - lettuce_share}

    # Build sales dataset
    sales_data = []
    total_sales = 0

    for crop in products:
        yld = st.sidebar.number_input(f"{crop} Yield (kg/m²/yr)", value=DEFAULT_YIELD[crop])
        price = DEFAULT_PRICE[crop]  # company-only
        area = total_cultivatable * shares[crop]
        revenue = area * yld * price
        total_sales += revenue
        sales_data.append({
            "Product": crop,
            "Area (m²)": area,
            "Revenue (€)": revenue
        })

    # CAPEX Auto
    st.sidebar.header("3. CAPEX")
    auto_build = floor_area * CAPEX_BUILDING_PER_M2
    auto_eq = total_cultivatable * CAPEX_EQUIPMENT_PER_M2
    auto_other = CAPEX_OTHER_FIXED
    auto_total = auto_build + auto_eq + auto_other
    auto_subsidy = auto_total * CAPEX_SUBSIDY_SHARE
    total_capex = auto_total - auto_subsidy

    st.sidebar.markdown(f"**Total CAPEX:** €{total_capex:,.0f}")

    # OPEX
    st.sidebar.header("4. Electricity Scenario")
    # Electricity use from area (stays same)
    elec_use_kwh = total_cultivatable * ELEC_KWH_PER_M2_YEAR
    other_opex = total_cultivatable * OTHER_OPEX_PER_M2_YEAR

    # Choose the electricity price
    price_mode = st.sidebar.radio(
        "Electricity price input",
        ["Use average €/kWh", "Upload Nordpool CSV"],
        index=0
    )

    # Defaults (in case CSV not uploaded)
    base_price = ELEC_PRICE_BASE
    opt_price = ELEC_PRICE_OPT

    if price_mode == "Use average €/kWh":
        # Simple manual input mode
        base_price = st.sidebar.number_input(
            "Average electricity price (€/kWh)",
            min_value=0.0,
            value=float(ELEC_PRICE_BASE),
            step=0.01
        )
        opt_price = st.sidebar.number_input(
            "Optimised schedule price (€/kWh)",
            min_value=0.0,
            value=float(ELEC_PRICE_OPT),
            step=0.01
        )

    else:
        # CSV-based effective price mode
        uploaded_csv = st.sidebar.file_uploader(
            "Upload Nordpool CSV (hourly prices)",
            type=["csv"]
        )

        if uploaded_csv is not None:
            prices_df = pd.read_csv(uploaded_csv)

            # Try a couple of common column names
            if "price_eur_per_kwh" in prices_df.columns:
                effective_price = prices_df["price_eur_per_kwh"].mean()
            elif "price_eur_mwh" in prices_df.columns:
                # convert €/MWh -> €/kWh
                effective_price = (prices_df["price_eur_mwh"] / 1000.0).mean()
            else:
                st.sidebar.error(
                    "Could not find price column. Expect 'price_eur_per_kwh' or 'price_eur_mwh'. "
                    "Using default 0.15 €/kWh."
                )
                effective_price = ELEC_PRICE_BASE

            st.sidebar.markdown(
                f"**Effective average price from CSV:** {effective_price:.3f} €/kWh"
            )

            # Let user define how much optimisation improves it
            opt_saving_pct = st.sidebar.slider(
                "Optimisation saving (%)", 0, 50, 20,
                help="How much cheaper the optimised schedule is compared to simple average."
            )
            base_price = effective_price
            opt_price = effective_price * (1 - opt_saving_pct / 100.0)

        else:
            st.sidebar.info("Upload a Nordpool CSV to compute effective prices.")
            # fall back to defaults
            base_price = ELEC_PRICE_BASE
            opt_price = ELEC_PRICE_OPT

    # Now choose which scenario to run the financial model with
    scenario = st.sidebar.radio(
        "Electricity price scenario",
        ["Current price model", "Optimised schedule"]
    )

    if scenario == "Current price model":
        price_used = base_price
    else:
        price_used = opt_price

    # Final yearly OPEX for the chosen scenario
    elec_cost = elec_use_kwh * price_used
    yearly_opex = elec_cost + other_opex



    # Forecast settings
    st.sidebar.header("5. Forecast")
    discount_rate = st.sidebar.number_input("Discount Rate", min_value=0.0, max_value=1.0, value=0.05)
    year1_eff = st.sidebar.number_input("Year 1 Efficiency", 0.0, 1.0, 0.8)
    eff_gain = st.sidebar.number_input("Annual Efficiency Gain", 0.0, 1.0, 0.015)
    years = st.sidebar.number_input("Forecast Years", min_value=1, value=10)

    # TABS LAYOUT
    tab_overview, tab_opex, tab_forecast = st.tabs(
        ["Overview", "OPEX", "Forecast & Cashflow"]
    )

    # OVERVIEW TAB 
    with tab_overview:
        vw_section("Yearly Sales Summary")
        st.table(pd.DataFrame(sales_data).set_index("Product"))
        st.metric("Total Yearly Sales", f"€{total_sales:,.0f}")
        st.metric("Total CAPEX", f"€{total_capex:,.0f}")

    #OPEX TAB 
    with tab_opex:
        vw_section("Operating Costs")
        st.metric("Total OPEX / year", f"€{yearly_opex:,.0f}")
    
        #OPEX comparison
        elec_cost_base = elec_use_kwh * base_price
        elec_cost_opt = elec_use_kwh * opt_price

        total_opex_base = elec_cost_base + other_opex
        total_opex_opt = elec_cost_opt + other_opex

        savings_abs = total_opex_base - total_opex_opt
        savings_pct = (savings_abs / total_opex_base * 100.0) if total_opex_base > 0 else 0.0

        st.markdown("---")
        st.subheader("• OPEX Comparison")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Current electricity price model**")
            st.metric("Electricity price", f"{base_price:.3f} €/kWh")
            st.metric("Yearly electricity cost", f"€{elec_cost_base:,.0f}")
            st.metric("Total yearly OPEX", f"€{total_opex_base:,.0f}")

        with col2:
            st.markdown("**Optimised schedule model**")
            st.metric("Electricity price", f"{opt_price:.3f} €/kWh")
            st.metric("Yearly electricity cost", f"€{elec_cost_opt:,.0f}")
            st.metric("Total yearly OPEX", f"€{total_opex_opt:,.0f}")

        st.subheader("• Savings from optimisation")
        st.metric(
            "Yearly OPEX savings",
            f"€{savings_abs:,.0f}",
            f"{savings_pct:.1f}%"
        )
        st.caption(
            ""    )
    

    # FORECAST TAB
    with tab_forecast:
        # Build forecast
        forecast = []
        cumulative = 0
        payback = None

        for y in range(1, years + 1):
            eff = min(year1_eff + eff_gain * (y - 1), 1.0)
            sales_y = total_sales * eff
            net_cash = sales_y - yearly_opex
            disc_net = net_cash / ((1 + discount_rate) ** y)
            cumulative += disc_net
            npv_minus_capex = cumulative - total_capex
            if payback is None and npv_minus_capex >= 0:
                payback = y

            forecast.append({
                "Year": y,
                "Net Cashflow (€)": net_cash,
                "Discounted (€)": disc_net,
                "Cumulative NPV (€)": cumulative,
                "NPV - CAPEX (€)": npv_minus_capex
            })

        df = pd.DataFrame(forecast)

        vw_section("Payback")
        st.metric("Payback Year", payback if payback else "Not reached")

        #vw_section("Cashflow Charts")
        vw_section("Cashflow & NPV ")

        df["Year"] = df["Year"].astype(int)

        line_source = df.melt(
            id_vars="Year",
            value_vars=["Discounted (€)", "Cumulative NPV (€)", "NPV - CAPEX (€)"],
            var_name="Series",
            value_name="Value"
        )

        line_chart = (
            alt.Chart(line_source)
            .mark_line(point=True)
            .encode(
                x=alt.X(
                "Year:O",
                title="Year",
                axis=alt.Axis(labelAngle=0)   # ← forces horizontal labels
            ),
            y=alt.Y("Value:Q", title="€"),
            color=alt.Color("Series:N", title="Series"),
            tooltip=["Year", "Series", "Value"]
            )
            .properties(height=320)
        )

        st.altair_chart(line_chart, use_container_width=True)

        vw_section("Net Cashflow per Year")

        bar_chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("Year:O", title="Year", axis=alt.Axis(labelAngle=0)),  # labels straight
                y=alt.Y("Net Cashflow (€):Q", title="Net cashflow (€)"),
                tooltip=["Year", "Net Cashflow (€)"]
            )
            .properties(height=260)
        )

        st.altair_chart(bar_chart, use_container_width=True)

        vw_section("Forecast Table")

        df["Year"] = df["Year"].astype(int)
        table_df = df.set_index("Year")

        styled_table = table_df.style.format({
            "Net Cashflow (€)": "€{:,.0f}",
            "Discounted (€)": "€{:,.0f}",
            "Cumulative NPV (€)": "€{:,.0f}",
            "NPV - CAPEX (€)": "€{:,.0f}"
        })

        st.dataframe(styled_table, use_container_width=True)

    # Footer 
    st.markdown(
        """
        <style>
        #custom-footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: #FFFFFF;
            padding: 6px 0;
            text-align: center;
            font-size: 11px;
            color: #888;
            border-top: 1px solid #DDD;
        }
        </style>

        <div id="custom-footer">
            © Vacuumwood Tech
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()