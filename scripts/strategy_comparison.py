import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv("data/clean_data/electricity_prices_full.csv")

df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
df["datetime"] = df["datetime"].dt.tz_convert("Europe/Helsinki")

df = df[df["year"] <= 2025]
df["date"] = df["datetime"].dt.date


def continuous_cost(day_df, hours):
    prices = day_df["price_eur_kwh"].values
    min_cost = float("inf")

    for i in range(0, 24 - hours + 1):
        cost = prices[i:i+hours].sum()
        if cost < min_cost:
            min_cost = cost

    return min_cost


def sparse_cost(day_df, hours):
    return day_df.nsmallest(hours, "price_eur_kwh")["price_eur_kwh"].sum()


def split_cost(day_df, total_hours):
    block = total_hours // 2
    prices = day_df["price_eur_kwh"].values

    min_cost = float("inf")

    for i in range(0, 24 - block + 1):
        for j in range(0, 24 - block + 1):

            if abs(i - j) < block:
                continue

            cost = prices[i:i+block].sum() + prices[j:j+block].sum()

            if cost < min_cost:
                min_cost = cost

    return min_cost


results = []

for date, group in df.groupby("date"):
    group = group.sort_values("hour")

    if len(group) != 24:
        continue

    results.append({
        "18h_cont": continuous_cost(group, 18),
        "18h_split": split_cost(group, 18),
        "18h_sparse": sparse_cost(group, 18),

        "16h_cont": continuous_cost(group, 16),
        "16h_split": split_cost(group, 16),
        "16h_sparse": sparse_cost(group, 16),

        "12h_cont": continuous_cost(group, 12),
        "12h_split": split_cost(group, 12),
        "12h_sparse": sparse_cost(group, 12),
    })

df_res = pd.DataFrame(results)


avg = df_res.mean()

print(avg)


labels = [
    "18h cont", "2×9h", "18h sparse",
    "16h cont", "2×8h", "16h sparse",
    "12h cont", "2×6h", "12h sparse"
]

values = [
    avg["18h_cont"], avg["18h_split"], avg["18h_sparse"],
    avg["16h_cont"], avg["16h_split"], avg["16h_sparse"],
    avg["12h_cont"], avg["12h_split"], avg["12h_sparse"],
]

colors = [
    "red", "orange", "green",
    "red", "orange", "green",
    "red", "orange", "green"
]

plt.figure(figsize=(10, 6))

plt.bar(labels, values, color=colors)
for i, v in enumerate(values):
    plt.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)

plt.ylabel("Average Daily Electricity Cost (€)")
plt.title("Comparison of Lighting Strategies")

plt.xticks(rotation=30)
plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/strategy_comparison.png", dpi=300)

plt.show()