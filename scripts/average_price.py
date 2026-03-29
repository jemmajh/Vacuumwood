import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("../data/clean_data/electricity_prices_full.csv")

df["datetime"] = pd.to_datetime(df["datetime"])

df = df[df["year"] <= 2025]

hourly_year = df.groupby(["year", "hour"])["price_eur_kwh"].mean().reset_index()

plt.figure(figsize=(12, 6))

for year in sorted(hourly_year["year"].unique()):
    subset = hourly_year[hourly_year["year"] == year]
    plt.plot(subset["hour"], subset["price_eur_kwh"], label=str(year), alpha=0.7)

plt.xlabel("Hour of Day")
plt.ylabel("Average Price (€/kWh)")
plt.title("Average Electricity Price by Hour (2013–2025)")
plt.legend(ncol=4, fontsize=8)
plt.grid()

plt.show()