from __future__ import annotations
import pandas as pd

def _prep(df: pd.DataFrame, ts_col="timestamp", price_col="price_eur_per_kwh") -> pd.DataFrame:
    df = df.copy()
    df[ts_col] = pd.to_datetime(df[ts_col])
    df["date"] = df[ts_col].dt.date
    df["year"] = df[ts_col].dt.year
    df["hour"] = df[ts_col].dt.hour
    return df

def fixed_schedule_daily(df_day: pd.DataFrame, hours_needed: int, start_hour: int) -> dict:
    """
    Fixed: lights on for `hours_needed` hours starting at `start_hour` (wraps around midnight if needed).
    Example: 16h starting 6 => 06..21.
    """
    hours = [(start_hour + i) % 24 for i in range(hours_needed)]
    chosen = df_day[df_day["hour"].isin(hours)].copy()
    if len(chosen) != hours_needed:
        # If your data has missing hours (DST etc.), this guards
        chosen = chosen.sort_values("timestamp").head(hours_needed)
    return {
        "fixed_mean_price": float(chosen["price_eur_per_kwh"].mean()),
        "fixed_hours": hours,
    }

def continuous_optimized_daily(df_day: pd.DataFrame, hours_needed: int) -> dict:
    """
    Continuous (circular): cheapest consecutive `hours_needed` window,
    allowing wrap-around across midnight.
    """
    g = df_day.sort_values("timestamp").reset_index(drop=True)

    # Basic guard (DST may cause 23/25 hours; still workable if >= hours_needed)
    if len(g) < hours_needed:
        raise ValueError("Not enough rows in day for continuous optimization.")

    # Make it circular by doubling the day
    g2 = pd.concat([g, g], ignore_index=True)

    # Rolling mean over doubled series
    roll = g2["price_eur_per_kwh"].rolling(window=hours_needed).mean()

    # Evaluate only windows that START within the first 24 hours
    # roll index i corresponds to window ending at i, starting at i-hours_needed+1
    best_start = None
    best_mean = float("inf")

    for start in range(0, min(24, len(g))):
        end = start + hours_needed - 1
        if end >= len(g2):
            break
        mean_val = float(g2.loc[start:end, "price_eur_per_kwh"].mean())
        if mean_val < best_mean:
            best_mean = mean_val
            best_start = start

    block = g2.loc[best_start:best_start + hours_needed - 1].copy()

    # Hours list should be modulo 24
    hours_list = [int(h) for h in (block["hour"].tolist())]

    return {
        "cont_mean_price": float(block["price_eur_per_kwh"].mean()),
        "cont_start_hour": int(block["hour"].iloc[0]),
        "cont_hours": hours_list,
    }

def sparse_optimized_daily(df_day: pd.DataFrame, hours_needed: int) -> dict:
    """
    Sparse: choose the cheapest `hours_needed` individual hours (not necessarily consecutive).
    """
    g = df_day.sort_values("price_eur_per_kwh").head(hours_needed).copy()
    g = g.sort_values("timestamp")  # nicer for reporting
    return {
        "sparse_mean_price": float(g["price_eur_per_kwh"].mean()),
        "sparse_hours": list(g["hour"].astype(int).tolist()),
    }

def build_daily_report(
    df: pd.DataFrame,
    hours_needed: int,
    fixed_start_hour: int = 6,
    ts_col: str = "timestamp",
    price_col: str = "price_eur_per_kwh",
) -> pd.DataFrame:
    """
    Returns one row per day with:
      - avg_day_price
      - fixed/continuous/sparse mean prices
      - savings vs avg
      - chosen hours for each mode
    """
    df = _prep(df, ts_col=ts_col, price_col=price_col)

    rows = []
    for d, g in df.groupby("date", sort=True):
        g = g.sort_values(ts_col)

        # Expect ~24 rows/day; allow minor exceptions
        if len(g) < 20:
            continue

        avg_day = float(g[price_col].mean())

        fixed = fixed_schedule_daily(g, hours_needed, fixed_start_hour)
        cont = continuous_optimized_daily(g, hours_needed)
        sparse = sparse_optimized_daily(g, hours_needed)

        rows.append({
            "date": pd.to_datetime(d),
            "year": int(g["year"].iloc[0]),
            "avg_day_price_eur_kwh": avg_day,

            "fixed_mean_price_eur_kwh": fixed["fixed_mean_price"],
            "continuous_mean_price_eur_kwh": cont["cont_mean_price"],
            "sparse_mean_price_eur_kwh": sparse["sparse_mean_price"],

            "fixed_savings_pct": (avg_day - fixed["fixed_mean_price"]) / avg_day if avg_day else 0.0,
            "continuous_savings_pct": (avg_day - cont["cont_mean_price"]) / avg_day if avg_day else 0.0,
            "sparse_savings_pct": (avg_day - sparse["sparse_mean_price"]) / avg_day if avg_day else 0.0,

            "fixed_hours": ",".join(map(str, fixed["fixed_hours"])),
            "continuous_start_hour": cont["cont_start_hour"],
            "continuous_hours": ",".join(map(str, cont["cont_hours"])),
            "sparse_hours": ",".join(map(str, sparse["sparse_hours"])),
        })

    daily = pd.DataFrame(rows)
    # Convert savings to %
    for c in ["fixed_savings_pct", "continuous_savings_pct", "sparse_savings_pct"]:
        daily[c] = daily[c] * 100.0
    return daily

def yearly_summary_from_daily(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Yearly averages for UI and financial model.
    """
    y = (daily.groupby("year")
         .agg(
             avg_price_year_eur_kwh=("avg_day_price_eur_kwh", "mean"),
             fixed_price_year_eur_kwh=("fixed_mean_price_eur_kwh", "mean"),
             continuous_price_year_eur_kwh=("continuous_mean_price_eur_kwh", "mean"),
             sparse_price_year_eur_kwh=("sparse_mean_price_eur_kwh", "mean"),

             fixed_savings_pct=("fixed_savings_pct", "mean"),
             continuous_savings_pct=("continuous_savings_pct", "mean"),
             sparse_savings_pct=("sparse_savings_pct", "mean"),
         )
         .reset_index())

    return y