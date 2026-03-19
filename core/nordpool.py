import pandas as pd

def effective_price_from_csv(df: pd.DataFrame) -> float:
    if "price_eur_per_kwh" in df.columns:
        return float(df["price_eur_per_kwh"].mean())
    if "price_eur_mwh" in df.columns:
        return float((df["price_eur_mwh"] / 1000.0).mean())
    raise ValueError("CSV missing 'price_eur_per_kwh' or 'price_eur_mwh'.")