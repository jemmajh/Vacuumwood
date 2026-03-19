import pandas as pd
from typing import Optional, Tuple

def cheapest_continuous_block(
    df: pd.DataFrame,
    block_hours: float,
    price_col: str = "price_eur_per_kwh",
    start_col: str = "start",
    allowed_start_hour: Optional[Tuple[int, int]] = None,
) -> dict:
    """
    Works for 60-min or 15-min data as long as df rows are equally spaced.
    """
    df = df.copy().sort_values(start_col).reset_index(drop=True)

    # infer time step
    step_seconds = (df[start_col].iloc[1] - df[start_col].iloc[0]).total_seconds()
    steps_per_hour = int(round(3600 / step_seconds))
    window = int(round(block_hours * steps_per_hour))

    if window < 1 or window > len(df):
        raise ValueError("Invalid block length for available data.")

    # rolling sum of prices
    roll = df[price_col].rolling(window).sum()
    # Equivalent SQL (window function):
    # SELECT
    #   SUM(price_eur_per_kwh) OVER (
    #       ORDER BY start
    #       ROWS BETWEEN window PRECEDING AND CURRENT ROW
    #   )
    best_i = None
    best_val = None

    for i in range(window - 1, len(df)):
        start_time = df[start_col].iloc[i - window + 1]
        if allowed_start_hour:
            lo, hi = allowed_start_hour
            if not (lo <= start_time.hour < hi):
                continue

        v = roll.iloc[i]
        if best_val is None or v < best_val:
            best_val = v
            best_i = i - window + 1

    if best_i is None:
        raise ValueError("No feasible block found given constraints.")

    out = df.iloc[best_i: best_i + window].copy()
    return {
        "start": out[start_col].iloc[0],
        "end": out[start_col].iloc[-1],
        "mean_price": float(out[price_col].mean()),
        "total_price_sum": float(out[price_col].sum()),
        "block": out,
    }