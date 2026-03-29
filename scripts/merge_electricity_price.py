import pandas as pd

df_nord = pd.read_csv("../data/clean_data/nordpool_clean.csv")
df_entsoe = pd.read_csv("../data/clean_data/entsoe_clean_all.csv")

df_nord["datetime"] = pd.to_datetime(df_nord["datetime"])
df_entsoe["datetime"] = pd.to_datetime(df_entsoe["datetime"], utc=True).dt.tz_convert("Europe/Helsinki")

#fixing DST error
df_nord["datetime"] = df_nord["datetime"].dt.tz_localize(
    "Europe/Helsinki",
    nonexistent="shift_forward",
    ambiguous="NaT"
)
# Remove problematic times
df_nord = df_nord.dropna(subset=["datetime"])

df_all = pd.concat([df_nord, df_entsoe])

df_all = df_all.drop_duplicates(subset="datetime")

df_all = df_all.sort_values("datetime").reset_index(drop=True)

df_all.to_csv("../data/electricity_prices_full.csv", index=False)

print("🚀 FINAL DATASET READY")
print(df_all.head())
print(df_all.tail())
print(f"Total rows: {len(df_all)}")