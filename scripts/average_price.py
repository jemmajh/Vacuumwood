import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("data/clean_data/electricity_prices_full.csv")

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

plt.xlim(0, 23)
plt.xticks(range(0, 24))

plt.legend(
    loc="upper right",
    fontsize=7,
    ncol=2,
    frameon=False
)
plt.grid(alpha=0.3)
plt.tight_layout()

os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/hourly_price_by_year.png", dpi=300, bbox_inches="tight")


plt.show()