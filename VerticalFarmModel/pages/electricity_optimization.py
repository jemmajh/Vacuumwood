import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]   # -> VerticalFarmModel/
REPORT_DIR = BASE_DIR / "data" / "optimization_reports"

@st.cache_data
def load_yearly_summary(photoperiod: int) -> pd.DataFrame:
    path = REPORT_DIR / f"thesis_yearly_summary_{photoperiod}h.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data
def load_daily_report(hours_needed: int) -> pd.DataFrame:
    path = REPORT_DIR / f"thesis_daily_report_{hours_needed}h.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=["date"])

st.title("Electricity Optimization (Photoperiod Scheduling)")

colA, colB, colC = st.columns([1, 1, 2])
with colA:
    photoperiod = st.selectbox("Photoperiod (hours/day)", [14, 16, 18], index=1)
with colB:
    fixed_start_hour = st.selectbox("Fixed schedule start hour", list(range(0, 24)), index=6)
with colC:
    st.caption("Continuous = cheapest consecutive hours (wraps across midnight). Sparse = cheapest individual hours (upper bound).")

yearly = load_yearly_summary(photoperiod)
if yearly.empty:
    st.error(
        f"Missing yearly summary CSV for {photoperiod}h.\n\n"
        f"Expected file:\n{(REPORT_DIR / f'thesis_yearly_summary_{photoperiod}h.csv').as_posix()}\n\n"
        "Fix: commit the file into the repo (data/optimization_reports/) and redeploy."
    )
    st.stop()

# year selector (safe)
years = sorted(yearly["year"].unique())
year = st.selectbox("Select year (for example scenario)", years, index=len(years) - 1)

row = yearly[yearly["year"] == year].iloc[0]

# Read kWh from session (if available)
kwh_year = st.session_state.get("elec_use_kwh")

baseline_price = float(row["avg_price_year_eur_kwh"])
fixed_price = float(row["fixed_price_year_eur_kwh"]) if "fixed_price_year_eur_kwh" in yearly.columns else None
cont_price = float(row["continuous_price_year_eur_kwh"])
sparse_price = float(row["sparse_price_year_eur_kwh"])

if kwh_year is None:
    st.info("Electricity use (kWh/year) not found from main model yet — enter it manually:")
    kwh_year = st.number_input(
        "Electricity use (kWh/year)",
        min_value=0.0,
        value=1_000_000.0,
        step=10_000.0,
    )

kwh_year = float(kwh_year)

baseline_cost = kwh_year * baseline_price
cont_cost = kwh_year * cont_price
sparse_cost = kwh_year * sparse_price
fixed_cost = (kwh_year * fixed_price) if fixed_price is not None else None

# Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Baseline (avg) €/kWh", f"{baseline_price:.4f}")
m2.metric("Continuous optimized €/kWh", f"{cont_price:.4f}")
m3.metric("Sparse optimized €/kWh", f"{sparse_price:.4f}")
m4.metric("Fixed schedule €/kWh", f"{fixed_price:.4f}" if fixed_price is not None else "—")

st.divider()

# Money impact
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("Annual cost comparison")
    cost_rows = [
        {"Mode": "Do nothing (avg)", "€/year": baseline_cost},
        {"Mode": "Continuous optimized", "€/year": cont_cost},
        {"Mode": "Sparse optimized (upper bound)", "€/year": sparse_cost},
    ]
    if fixed_cost is not None:
        cost_rows.insert(1, {"Mode": f"Fixed schedule (start {fixed_start_hour:02d}:00)", "€/year": fixed_cost})

    st.dataframe(pd.DataFrame(cost_rows), use_container_width=True)

with col2:
    st.subheader("Historical yearly summary")
    st.dataframe(yearly, use_container_width=True)

st.divider()

daily = load_daily_report(photoperiod)
if not daily.empty:
    st.subheader("Daily recommended hours (from historical data)")
    date_choice = st.date_input(
        "Pick a date",
        value=daily["date"].min().date(),
        min_value=daily["date"].min().date(),
        max_value=daily["date"].max().date(),
    )
    day_row = daily[daily["date"].dt.date == date_choice]
    if not day_row.empty:
        r = day_row.iloc[0]
        st.write(f"**Average day price:** {r['avg_day_price_eur_kwh']:.4f} €/kWh")
        st.write(f"**Continuous window start:** {int(r['continuous_start_hour']):02d}:00")
        st.write(f"**Continuous hours:** {r['continuous_hours']}")
        st.write(f"**Sparse hours:** {r['sparse_hours']}")
    else:
        st.info("No row for that date.")
else:
    st.info("Daily report file not found. Add thesis_daily_report_XXh.csv to enable day-by-day viewing.")