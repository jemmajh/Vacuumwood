import streamlit as st
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]   # -> VerticalFarmModel/
REPORT_DIR = BASE_DIR / "data" / "optimization_reports"

@st.cache_data
def load_yearly_summary(photoperiod: int) -> pd.DataFrame:
    path = REPORT_DIR / f"thesis_yearly_summary_{photoperiod}h.csv"
    if not path.exists():
        st.error(f"Missing file: {path.name}. Make sure it is committed to GitHub.")
        return pd.DataFrame()
    return pd.read_csv(path)

@st.cache_data
def load_daily_report(hours_needed: int) -> pd.DataFrame:
    path = REPORT_DIR / f"thesis_daily_report_{hours_needed}h.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    return pd.DataFrame()

st.title("Electricity Optimization (Photoperiod Scheduling)")

# --- Controls
colA, colB, colC = st.columns([1, 1, 2])
with colA:
    photoperiod = st.selectbox("Photoperiod (hours/day)", [14, 16, 18], index=1)
with colB:
    fixed_start_hour = st.selectbox("Fixed schedule start hour", list(range(0, 24)), index=6)
with colC:
    st.caption("Continuous = cheapest consecutive hours (wraps across midnight). Sparse = cheapest individual hours (upper bound).")

yearly = load_yearly_summary(photoperiod)

year = st.selectbox("Select year (for example scenario)", sorted(yearly["year"].unique()), index=len(yearly["year"].unique())-1)

row = yearly[yearly["year"] == year].iloc[0]

# --- Connect your model here:
# Replace this with your actual computed yearly electricity use (kWh/year)
# Example: kwh_year = st.session_state.get("kwh_year_total", 1_000_000)
kwh_year = st.session_state.get("elec_use_kwh", None)
baseline_price = float(row["avg_price_year_eur_kwh"])
fixed_price = float(row["fixed_price_year_eur_kwh"]) if "fixed_price_year_eur_kwh" in row else None
cont_price = float(row["continuous_price_year_eur_kwh"])
sparse_price = float(row["sparse_price_year_eur_kwh"])

baseline_cost = kwh_year * baseline_price
cont_cost = kwh_year * cont_price
sparse_cost = kwh_year * sparse_price

# If your yearly report didn’t include fixed schedule (some older file versions), we compute fallback:
if fixed_price is None:
    fixed_cost = None
else:
    fixed_cost = kwh_year * fixed_price

# --- Metrics row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Baseline (avg) €/kWh", f"{baseline_price:.4f}")
m2.metric("Continuous optimized €/kWh", f"{cont_price:.4f}", f"-{row['continuous_savings_pct']:.1f}%")
m3.metric("Sparse optimized €/kWh", f"{sparse_price:.4f}", f"-{row['sparse_savings_pct']:.1f}%")

if fixed_price is not None:
    fixed_savings_pct = float(row["fixed_savings_pct"])
    m4.metric("Fixed schedule €/kWh", f"{fixed_price:.4f}", f"-{fixed_savings_pct:.1f}%")
else:
    m4.metric("Fixed schedule €/kWh", "—", "Add fixed to summary")

st.divider()

# --- Money impact
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Annual cost comparison")
    cost_rows = [
        {"Mode": "Do nothing (avg)", "€/year": baseline_cost, "Savings €/year": 0.0, "Savings %": 0.0},
        {"Mode": "Continuous optimized", "€/year": cont_cost,
         "Savings €/year": baseline_cost - cont_cost,
         "Savings %": 100.0 * (baseline_cost - cont_cost) / baseline_cost if baseline_cost else 0.0},
        {"Mode": "Sparse optimized (upper bound)", "€/year": sparse_cost,
         "Savings €/year": baseline_cost - sparse_cost,
         "Savings %": 100.0 * (baseline_cost - sparse_cost) / baseline_cost if baseline_cost else 0.0},
    ]
    if fixed_cost is not None:
        cost_rows.insert(1, {"Mode": f"Fixed schedule (start {fixed_start_hour:02d}:00)", "€/year": fixed_cost,
                             "Savings €/year": baseline_cost - fixed_cost,
                             "Savings %": 100.0 * (baseline_cost - fixed_cost) / baseline_cost if baseline_cost else 0.0})

    cost_df = pd.DataFrame(cost_rows)
    st.dataframe(cost_df, use_container_width=True)

with col2:
    st.subheader("Historical yearly summary")
    show_cols = [
        "year",
        "avg_price_year_eur_kwh",
        "continuous_price_year_eur_kwh",
        "continuous_savings_pct",
        "sparse_price_year_eur_kwh",
        "sparse_savings_pct",
    ]
    if "fixed_price_year_eur_kwh" in yearly.columns:
        show_cols.insert(2, "fixed_price_year_eur_kwh")
        show_cols.insert(3, "fixed_savings_pct")

    st.dataframe(yearly[show_cols], use_container_width=True)

st.divider()

# --- Optional: daily schedule lookup (super persuasive in demos)
daily = load_daily_report(photoperiod)
if not daily.empty:
    st.subheader("Daily recommended hours (from historical data)")
    st.session_state["base_price_eur_kwh"] = baseline_price
    st.session_state["opt_price_eur_kwh"] = cont_price
    date_choice = st.date_input("Pick a date", value=daily["date"].min().date(),
                                min_value=daily["date"].min().date(), max_value=daily["date"].max().date())
    day_row = daily[daily["date"].dt.date == date_choice]
    if not day_row.empty:
        r = day_row.iloc[0]
        st.write(f"**Average day price:** {r['avg_day_price_eur_kwh']:.4f} €/kWh")
        st.write(f"**Continuous window start:** {int(r['continuous_start_hour']):02d}:00")
        st.write(f"**Continuous hours:** {r['continuous_hours']}")
        st.write(f"**Sparse hours:** {r['sparse_hours']}")
        st.write(f"**Continuous savings:** {r['continuous_savings_pct']:.1f}% | **Sparse savings:** {r['sparse_savings_pct']:.1f}%")
    else:
        st.info("No row for that date (possible missing-hour days).")
else:
    st.info("Daily report file not found. Add thesis_daily_report_XXh.csv to enable day-by-day viewing.")