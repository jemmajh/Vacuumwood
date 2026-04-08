import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("data/clean_data/electricity_prices_full.csv")

df["datetime"] = pd.to_datetime(df["datetime"])

df_recent = df[df["year"].isin([2023, 2024, 2025])]

hourly = df_recent.groupby(["year", "hour"])["price_eur_kwh"].mean().reset_index()

colors = {
    2023: "blue",
    2024: "orange",
    2025: "green"
}

plt.figure(figsize=(10, 6))

for year in [2023, 2024, 2025]:
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
plt.title("Recent Electricity Price Trends (2023–2025)")

plt.xticks(range(0, 24))
plt.xlim(0, 23)

plt.legend(title="Year", loc="upper right", fontsize=8, frameon=False)

plt.grid(alpha=0.3)
plt.tight_layout()

os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/recent_trends.png", dpi=300)

plt.show()