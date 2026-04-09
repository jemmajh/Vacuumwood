from __future__ import annotations
import numpy as np
import pandas as pd
from functools import lru_cache


def _continuous(prices: np.ndarray, hours: int) -> float:
    return min(float(prices[i : i + hours].sum()) for i in range(0, 25 - hours))


def _sparse(prices: np.ndarray, hours: int) -> float:
    return float(np.sort(prices)[:hours].sum())


def _split(prices: np.ndarray, total_hours: int) -> float:
    block = total_hours // 2
    best = float("inf")
    for i in range(0, 25 - block):
        for j in range(0, 25 - block):
            if abs(i - j) < block:
                continue
            c = prices[i : i + block].sum() + prices[j : j + block].sum()
            if c < best:
                best = c
    return float(best)


def compute_strategy_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    df must have columns: datetime (tz-aware), price_eur_kwh, year.
    Returns one row per year with mean daily cost for each strategy × hours combo.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["datetime"]).dt.date

    rows = []
    for date, g in df.groupby("date"):
        g = g.sort_values("hour")
        if len(g) != 24:
            continue
        p = g["price_eur_kwh"].values
        rows.append({
            "date": date,
            "year": int(g["year"].iloc[0]),
            "avg": float(p.mean()),
            "c18": _continuous(p, 18), "sp18": _split(p, 18), "s18": _sparse(p, 18),
            "c16": _continuous(p, 16), "sp16": _split(p, 16), "s16": _sparse(p, 16),
            "c12": _continuous(p, 12), "sp12": _split(p, 12), "s12": _sparse(p, 12),
        })

    daily = pd.DataFrame(rows)
    yearly = (
        daily.groupby("year")
        .mean(numeric_only=True)
        .reset_index()
    )
    return yearly


def savings_pct(strategy_cost: float, hours: int, avg_price: float) -> float:
    """
    % saving vs paying unoptimised avg price for <hours> hours.
    """
    baseline = avg_price * hours
    if baseline == 0:
        return 0.0
    return (baseline - strategy_cost) / baseline * 100


def build_comparison_df(yearly: pd.DataFrame, hours: int) -> pd.DataFrame:
    """
    For a chosen hours value (12 / 16 / 18) return a tidy df with savings %.
    """
    col_c  = f"c{hours}"
    col_sp = f"sp{hours}"
    col_s  = f"s{hours}"

    out = yearly[["year", "avg"]].copy()
    out["continuous_cost"]  = yearly[col_c]
    out["split_cost"]       = yearly[col_sp]
    out["sparse_cost"]      = yearly[col_s]
    out["baseline_cost"]    = yearly["avg"] * hours

    for col, label in [("continuous_cost", "continuous"), ("split_cost", "split"), ("sparse_cost", "sparse")]:
        out[f"{label}_saving_pct"] = (out["baseline_cost"] - out[col]) / out["baseline_cost"] * 100

    return out