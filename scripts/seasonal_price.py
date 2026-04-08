import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("data/clean_data/electricity_prices_full.csv")

df["datetime"] = pd.to_datetime(df["datetime"])

df = df[df["year"] <= 2025]

season_hour = df.groupby(["season", "hour"])["price_eur_kwh"].mean().reset_index()

plt.figure(figsize=(10, 6))
colors = {
    "winter": "blue",
    "spring": "green",   # or "pink" if you prefer
    "summer": "red",
    "autumn": "orange"
}

for season in ["winter", "spring", "summer", "autumn"]:
    subset = season_hour[season_hour["season"] == season]
    plt.plot(subset["hour"],
             subset["price_eur_kwh"],
             label=season,
             linewidth=2,
             color=colors[season]
    )

plt.xlabel("Hour of Day")
plt.ylabel("Average Price (€/kWh)")
plt.title("Seasonal Electricity Price Patterns by Hour (2013 - 2025)")

plt.xticks(range(0, 24))
plt.xlim(0, 23)

plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()

# save
os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/seasonal_hourly_price.png", dpi=300)

plt.show()