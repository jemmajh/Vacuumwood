import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import os


df = pd.read_csv("data/clean_data/electricity_prices_full.csv")

df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
df["datetime"] = df["datetime"].dt.tz_convert("Europe/Helsinki")

df = df[df["year"] <= 2025].copy()
df = df.sort_values("datetime").reset_index(drop=True)



df["day_of_week"] = df["datetime"].dt.dayofweek
df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

df["lag_1"] = df["price_eur_kwh"].shift(1)
df["lag_24"] = df["price_eur_kwh"].shift(24)

df["rolling_24h_mean"] = df["price_eur_kwh"].shift(1).rolling(24).mean()

df = df.dropna().copy()

feature_cols = [
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_weekend",
    "lag_1",
    "lag_24",
    "rolling_24h_mean"
]

target_col = "price_eur_kwh"

X = df[feature_cols]
y = df[target_col]

# TRAIN / TEST SPLIT
# time-based split
split_idx = int(len(df) * 0.8)

X_train = X.iloc[:split_idx]
X_test = X.iloc[split_idx:]

y_train = y.iloc[:split_idx]
y_test = y.iloc[split_idx:]

df_train = df.iloc[:split_idx].copy()
df_test = df.iloc[split_idx:].copy()

# MODELS
lr_model = LinearRegression()
rf_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)

lr_model.fit(X_train, y_train)
rf_model.fit(X_train, y_train)

lr_pred = lr_model.predict(X_test)
rf_pred = rf_model.predict(X_test)

# EVALUATION
def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))

print("Linear Regression:")
print("MAE:", mean_absolute_error(y_test, lr_pred))
print("RMSE:", rmse(y_test, lr_pred))

print("\nRandom Forest:")
print("MAE:", mean_absolute_error(y_test, rf_pred))
print("RMSE:", rmse(y_test, rf_pred))

# Use RF as final predicted price
df_test["predicted_price"] = rf_pred
df_test["actual_price"] = y_test.values

# OPTIMIZATION
def continuous_cost(day_df, hours, price_col):
    prices = day_df[price_col].values
    min_cost = float("inf")

    for i in range(0, 24 - hours + 1):
        cost = prices[i:i + hours].sum()
        if cost < min_cost:
            min_cost = cost

    return min_cost


def sparse_cost(day_df, hours, price_col):
    return day_df.nsmallest(hours, price_col)[price_col].sum()


def split_cost(day_df, total_hours, price_col):
    block = total_hours // 2
    prices = day_df[price_col].values
    min_cost = float("inf")

    for i in range(0, 24 - block + 1):
        for j in range(0, 24 - block + 1):
            if abs(i - j) < block:
                continue

            cost = prices[i:i + block].sum() + prices[j:j + block].sum()
            if cost < min_cost:
                min_cost = cost

    return min_cost

#Daily optimization
df_test["date"] = df_test["datetime"].dt.date

results = []

for date, group in df_test.groupby("date"):
    group = group.sort_values("hour")

    if len(group) != 24:
        continue

    results.append({
        "date": date,

        # baseline
        "18h_cont_actual": continuous_cost(group, 18, "actual_price"),
        "18h_cont_pred": continuous_cost(group, 18, "predicted_price"),

        # 16h strategies
        "16h_cont_actual": continuous_cost(group, 16, "actual_price"),
        "16h_cont_pred": continuous_cost(group, 16, "predicted_price"),

        "16h_split_actual": split_cost(group, 16, "actual_price"),
        "16h_split_pred": split_cost(group, 16, "predicted_price"),

        "16h_sparse_actual": sparse_cost(group, 16, "actual_price"),
        "16h_sparse_pred": sparse_cost(group, 16, "predicted_price"),

        # 12h strategies
        "12h_cont_actual": continuous_cost(group, 12, "actual_price"),
        "12h_cont_pred": continuous_cost(group, 12, "predicted_price"),

        "12h_split_actual": split_cost(group, 12, "actual_price"),
        "12h_split_pred": split_cost(group, 12, "predicted_price"),

        "12h_sparse_actual": sparse_cost(group, 12, "actual_price"),
        "12h_sparse_pred": sparse_cost(group, 12, "predicted_price"),
    })

results_df = pd.DataFrame(results)
results_df.to_csv("data/clean_data/ml_results.csv", index=False)

print("\nAverage optimized daily costs on test set:")
print(results_df.mean(numeric_only=True))

# PLOT actual VS predicted
os.makedirs("visualisation", exist_ok=True)

plot_df = df_test.iloc[:24 * 7].copy()  # first 7 days of test set

plt.figure(figsize=(12, 5))
plt.plot(plot_df["datetime"], plot_df["actual_price"], label="Actual", linewidth=2)
plt.plot(plot_df["datetime"], plot_df["predicted_price"], label="Predicted", linewidth=2)

plt.title("Actual vs Predicted Electricity Prices")
plt.xlabel("Datetime")
plt.ylabel("Price (€/kWh)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("visualizations/actual_vs_predicted_prices.png", dpi=300)
plt.show()
