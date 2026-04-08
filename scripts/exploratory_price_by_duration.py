import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("data/clean_data/electricity_prices_full.csv")

df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
df["datetime"] = df["datetime"].dt.tz_convert("Europe/Helsinki")

df = df[df["year"] <= 2025]

df["date"] = df["datetime"].dt.date


def find_min_cost(day_df, block_size):
    prices = day_df["price_eur_kwh"].values
    min_cost = float("inf")

    for i in range(0, 24 - block_size + 1):
        cost = prices[i:i+block_size].sum()
        if cost < min_cost:
            min_cost = cost

    return min_cost


durations = [3, 4, 6, 8, 10, 12, 14, 16, 18]

avg_costs = []


for d in durations:
    daily_costs = []

    for date, group in df.groupby("date"):
        group = group.sort_values("hour")

        if len(group) != 24:
            continue

        cost = find_min_cost(group, d)
        daily_costs.append(cost)

    avg_cost = sum(daily_costs) / len(daily_costs)
    avg_costs.append(avg_cost)

    print(f"{d}h → {avg_cost:.4f} €/day")


plt.figure(figsize=(8, 5))

plt.plot(durations, avg_costs, marker="o")

plt.xlabel("Lighting Duration (hours)")
plt.ylabel("Average Minimum Daily Cost (€)")
plt.title("Minimum Electricity Cost vs Lighting Duration (Continuous Blocks)")

plt.grid(alpha=0.3)

plt.tight_layout()

os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/duration_vs_cost.png", dpi=300)

plt.show()