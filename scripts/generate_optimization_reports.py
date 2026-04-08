import pandas as pd
import numpy as np
from pathlib import Path

# CONFIG
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "clean_data" / "electricity_prices_full.csv"
REPORT_DIR = BASE_DIR / "data" / "optimization_reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

PHOTOPERIODS = [14, 16, 18]
FIXED_START_HOUR = 6


# OPTIMIZATION FUNCTIONS
def continuous_cost(prices: np.ndarray, hours: int):
    prices_ext = np.concatenate([prices, prices])

    best_cost = float("inf")
    best_start = 0

    for start in range(24):
        cost = prices_ext[start:start+hours].sum()
        if cost < best_cost:
            best_cost = cost
            best_start = start

    selected_hours = [(best_start + i) % 24 for i in range(hours)]

    return best_cost / hours, best_start, selected_hours


def sparse_cost(prices: np.ndarray, hours: int):
    idx = np.argsort(prices)[:hours]
    return prices[idx].mean(), sorted(idx.tolist())


def fixed_schedule_cost(prices: np.ndarray, hours: int, start_hour: int):
    selected = [(start_hour + i) % 24 for i in range(hours)]
    return prices[selected].mean(), selected


# LOAD DATA
df = pd.read_csv(DATA_PATH)
df["datetime"] = pd.to_datetime(
    df["datetime"],
    utc=True,
    errors="coerce"
)

df = df.dropna(subset=["datetime"])
df = df.sort_values("datetime")

# GENERATE REPORTS
for photoperiod in PHOTOPERIODS:

    daily_results = []

    for date, group in df.groupby(df["datetime"].dt.date):

        if len(group) != 24:
            continue

        prices = group.sort_values("hour")["price_eur_kwh"].values
        year = group["year"].iloc[0]

        cont_price, cont_start, cont_hours = continuous_cost(prices, photoperiod)
        sparse_price, sparse_hours = sparse_cost(prices, photoperiod)
        fixed_price, fixed_hours = fixed_schedule_cost(prices, photoperiod, FIXED_START_HOUR)

        daily_results.append({
            "date": date,
            "year": year,
            "avg_day_price_eur_kwh": prices.mean(),

            "continuous_price_eur_kwh": cont_price,
            "continuous_start_hour": cont_start,
            "continuous_hours": ",".join(map(str, cont_hours)),

            "sparse_price_eur_kwh": sparse_price,
            "sparse_hours": ",".join(map(str, sparse_hours)),

            "fixed_price_eur_kwh": fixed_price,
            "fixed_hours": ",".join(map(str, fixed_hours)),
        })

    daily_df = pd.DataFrame(daily_results)

    # YEARLY SUMMARY
    yearly_df = (
        daily_df.groupby("year")
        .agg({
            "avg_day_price_eur_kwh": "mean",
            "continuous_price_eur_kwh": "mean",
            "sparse_price_eur_kwh": "mean",
            "fixed_price_eur_kwh": "mean",
        })
        .reset_index()
        .rename(columns={
            "avg_day_price_eur_kwh": "avg_price_year_eur_kwh",
            "continuous_price_eur_kwh": "continuous_price_year_eur_kwh",
            "sparse_price_eur_kwh": "sparse_price_year_eur_kwh",
            "fixed_price_eur_kwh": "fixed_price_year_eur_kwh",
        })
    )

    # SAVE
    yearly_path = REPORT_DIR / f"thesis_yearly_summary_{photoperiod}h.csv"
    daily_path = REPORT_DIR / f"thesis_daily_report_{photoperiod}h.csv"

    yearly_df.to_csv(yearly_path, index=False)
    daily_df.to_csv(daily_path, index=False)

    print(f"Saved: {yearly_path.name}")
    print(f"Saved: {daily_path.name}")

print("All optimization reports generated successfully.")