import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("data/clean_data/electricity_prices_full.csv")
df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
df["datetime"] = df["datetime"].dt.tz_convert("Europe/Helsinki")

df = df[df["year"] <= 2025]
df["date"] = df["datetime"].dt.date


def find_continuous_block(day_df, block_size):
    prices = day_df["price_eur_kwh"].values

    min_cost = float("inf")

    for i in range(0, 24 - block_size + 1):
        cost = prices[i:i+block_size].sum()
        if cost < min_cost:
            min_cost = cost

    return min_cost


def find_sparse(day_df, hours_needed):
    sorted_prices = day_df.sort_values("price_eur_kwh")
    return sorted_prices.head(hours_needed)["price_eur_kwh"].sum()


results = []

for date, group in df.groupby("date"):
    group = group.sort_values("hour")

    if len(group) != 24:
        continue

    cost_3h = find_continuous_block(group, 3)
    cost_6h = find_continuous_block(group, 6)
    cost_8h = find_continuous_block(group, 8)
    cost_sparse_16h = find_sparse(group, 16)

    results.append({
        "date": date,
        "3h_cont": cost_3h,
        "6h_cont": cost_6h,
        "8h_cont": cost_8h,
        "16h_sparse": cost_sparse_16h
    })

results_df = pd.DataFrame(results)


avg_costs = results_df.mean(numeric_only=True)

print("Average costs:")
print(avg_costs)


plt.figure(figsize=(8, 5))

labels = ["3h cont", "6h cont", "8h cont", "16h sparse"]
values = [
    avg_costs["3h_cont"],
    avg_costs["6h_cont"],
    avg_costs["8h_cont"],
    avg_costs["16h_sparse"]
]

colors = ["blue", "green", "orange", "red"]

plt.bar(labels, values, color=colors)

plt.ylabel("Average Daily Cost (€/kWh)")
plt.title("Comparison of Lighting Strategies")

plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/strategy_comparison.png", dpi=300)

plt.show()