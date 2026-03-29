import pandas as pd

df = pd.read_csv("../data/nordpool_raw/electricity_prices_2013_2020.csv")

df.rename(columns={
    "timestamp": "datetime",
    "price_eur_per_kwh": "price_eur_kwh"
}, inplace=True)

df["datetime"] = pd.to_datetime(df["datetime"])

df = df[df["datetime"] < "2020-01-01"]

df["year"] = df["datetime"].dt.year
df["month"] = df["datetime"].dt.month
df["day"] = df["datetime"].dt.day
df["hour"] = df["datetime"].dt.hour

df["season"] = df["month"].map({
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn"
})

df["is_weekend"] = df["datetime"].dt.weekday >= 5

df["source"] = "nordpool"

df = df[
    [
        "datetime",
        "price_eur_mwh",
        "price_eur_kwh",
        "year",
        "month",
        "day",
        "hour",
        "season",
        "is_weekend",
        "source"
    ]
]

df.to_csv("../data/nordpool_clean.csv", index=False)

print("✅ Nordpool cleaned!")
print(df.head())
print(df.tail())
print(f"Rows: {len(df)}")