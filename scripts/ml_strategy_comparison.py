import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd


os.makedirs("visualizations", exist_ok=True)
results_df = pd.read_csv("data/clean_data/ml_results.csv")
avg = results_df.mean(numeric_only=True)
def plot_actual_vs_pred(avg, duration):

    import numpy as np
    import matplotlib.pyplot as plt

    if duration == 18:
        strategies = ["Continuous"]

        actual = [avg["18h_cont_actual"]]
        predicted = [avg["18h_cont_pred"]]

    else:
        strategies = ["Continuous", "Split", "Sparse"]

        actual = [
            avg[f"{duration}h_cont_actual"],
            avg[f"{duration}h_split_actual"],
            avg[f"{duration}h_sparse_actual"]
        ]

        predicted = [
            avg[f"{duration}h_cont_pred"],
            avg[f"{duration}h_split_pred"],
            avg[f"{duration}h_sparse_pred"]
        ]

    x = np.arange(len(strategies))
    width = 0.35

    plt.figure(figsize=(6, 4))

    plt.bar(x - width/2, actual, width, label="Actual")
    plt.bar(x + width/2, predicted, width, label="Predicted")

    plt.xticks(x, strategies)
    plt.ylabel("Average Daily Cost (€)")
    plt.title(f"{duration}h Lighting: Actual vs Predicted")

    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    # values
    for i, v in enumerate(actual):
        plt.text(i - width/2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)

    for i, v in enumerate(predicted):
        plt.text(i + width/2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.show()


avg = results_df.mean(numeric_only=True)

plot_actual_vs_pred(avg, 18)
plot_actual_vs_pred(avg, 16)
plot_actual_vs_pred(avg, 12)