import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("data/clean_data/electricity_prices_full.csv")
df["datetime"] = pd.to_datetime(df["datetime"])

df_crisis = df[df["year"].isin([2021, 2022, 2023])]

hourly = df_crisis.groupby(["year", "hour"])["price_eur_kwh"].mean().reset_index()

colors = {
    2021: "green",   # normal
    2022: "red",     # crisis
    2023: "blue"     # recovery
}

plt.figure(figsize=(10, 6))

for year in [2021, 2022, 2023]:
    subset = hourly[hourly["year"] == year]
    plt.plot(
        subset["hour"],
        subset["price_eur_kwh"],
        label=str(year),
        linewidth=2,
        color=colors[year]
    )

plt.xlabel("Hour of Day")
plt.ylabel("Average Price (€/kWh)")
plt.title("Electricity Price Patterns: Normal vs Crisis vs Recovery")

plt.xticks(range(0, 24))
plt.xlim(0, 23)

plt.legend(title="Year")
plt.grid(alpha=0.3)
plt.tight_layout()

os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/crisis_comparison.png", dpi=300)

plt.show()