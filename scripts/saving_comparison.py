import matplotlib.pyplot as plt
import numpy as np
import os

baseline = 0.934089

data = {
    "18h": [0.934089, 0.860639, 0.788282],
    "16h": [0.795261, 0.727418, 0.667396],
    "12h": [0.554596, 0.477905, 0.448514],
}

labels = ["Continuous", "Split", "Sparse"]

savings = {
    k: [(baseline - v)/baseline * 100 for v in vals]
    for k, vals in data.items()
}

x = np.arange(len(data))  # 3 groups
width = 0.25

plt.figure(figsize=(10, 6))

colors = ["red", "orange", "green"]

for i in range(3):
    vals = [savings[k][i] for k in data.keys()]
    plt.bar(x + i*width, vals, width, label=labels[i], color=colors[i])

plt.xticks(x + width, list(data.keys()))
plt.ylabel("Cost Savings (%) vs 18h Continuous")
plt.title("Electricity Cost Savings by Lighting Strategy")

plt.legend()
plt.grid(axis="y", alpha=0.3)

for i in range(3):
    vals = [savings[k][i] for k in data.keys()]
    for j, v in enumerate(vals):
        plt.text(j + i*width, v + 1, f"{v:.1f}%", ha="center", fontsize=8)

plt.tight_layout()

os.makedirs("visualizations", exist_ok=True)
plt.savefig("visualizations/savings_comparison.png", dpi=300)

plt.show()