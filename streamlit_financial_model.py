import streamlit as st
import pandas as pd
import numpy as np

DEFAULT_YIELD = {'Lettuce': 70.0, 'Basil': 30.0}  # kg per m² per year
DEFAULT_PRICE = {'Lettuce': 7.0, 'Basil': 20.0}   # € per kg


st.set_page_config(page_title="Vertical Farming Model", layout="wide")

def main():
    st.title("Vertical Farming Financial Model")

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

    st.sidebar.header("2. Products & Yields")
    products = st.sidebar.multiselect(
        "Select Crops to Grow", options=list(DEFAULT_YIELD.keys()), default=list(DEFAULT_YIELD.keys())
    )
    if len(products) == 0:
        st.sidebar.error("Select at least one crop.")
        return
    elif len(products) == 1:
        shares = {products[0]: 1.0}
    else:
        lettuce_share = st.sidebar.slider("Lettuce % of Cultivation Area", 0.0, 1.0, 0.5, step=0.05)
        shares = {'Lettuce': lettuce_share, 'Basil': 1.0 - lettuce_share}

    data = []
    total_sales = 0.0
    for crop in products:
        yld = st.sidebar.number_input(f"{crop} Yield (kg/m²/yr)", min_value=0.0, value=DEFAULT_YIELD[crop])
        price = st.sidebar.number_input(f"{crop} Price (€ / kg)", min_value=0.0, value=DEFAULT_PRICE[crop])
        area = total_cultivable * shares.get(crop, 0)
        revenue = area * yld * price
        total_sales += revenue
        data.append({'Product': crop, 'Area (m²)': area, 'Yield (kg)': area * yld, 'Revenue (€)': revenue})

    st.subheader("Yearly Sales Summary")
    sales_df = pd.DataFrame(data)
    st.table(sales_df.set_index('Product'))
    st.metric("Total Yearly Sales", f"€{total_sales:,.0f}")

    st.sidebar.header("3. Initial Investment Costs")
    building_cost = st.sidebar.number_input("Building Cost (€)", min_value=0.0, value=466980.0)
    equipment_cost = st.sidebar.number_input("Equipment Cost (€)", min_value=0.0, value=2565000.0)
    other_cost = st.sidebar.number_input("Other Cost (€)", min_value=0.0, value=50000.0)
    subsidy = st.sidebar.number_input("Subsidies (€)", min_value=0.0, value=909594.0)
    total_investment = building_cost + equipment_cost + other_cost - subsidy
    st.metric("Total Initial Investment", f"€{total_investment:,.0f}")

    st.sidebar.header("4. Forecast & Payback")
    discount_rate = st.sidebar.number_input("Discount Rate", min_value=0.0, max_value=1.0, value=0.05, format="%.2f")
    year1_eff = st.sidebar.number_input("Year 1 Operational Efficiency", min_value=0.0, max_value=1.0, value=0.8)
    eff_gain = st.sidebar.number_input("Annual Efficiency Gain", min_value=0.0, value=0.015)
    years = st.sidebar.number_input("Forecast Years", min_value=1, value=10)

    forecast = []
    cumulative = 0.0
    for y in range(1, int(years) + 1):
        eff = min(year1_eff + (y - 1) * eff_gain, 1.0)
        sales = total_sales * eff
        discounted = sales / ((1 + discount_rate) ** y)
        cumulative += discounted
        net = cumulative - total_investment
        forecast.append({
            'Year': y,
            'Efficiency': eff,
            'Discounted Sales (€)': discounted,
            'Cumulative (€)': cumulative,
            'Net (€)': net
        })
    fc_df = pd.DataFrame(forecast)

    st.subheader("Forecast & Payback Chart")
    st.line_chart(fc_df.set_index('Year')[['Discounted Sales (€)', 'Cumulative (€)', 'Net (€)']])
    st.dataframe(fc_df.style.format({
        'Efficiency': '{:.0%}',
        'Discounted Sales (€)': '€{:.0f}',
        'Cumulative (€)': '€{:.0f}',
        'Net (€)': '€{:.0f}'
    }))

if __name__ == '__main__':
    main()
