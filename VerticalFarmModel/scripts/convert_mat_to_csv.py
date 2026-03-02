import scipy.io
import pandas as pd
import sys
print("Running python from:", sys.executable)


def convert_mat_to_csv(mat_path, output_csv_path):
    mat = scipy.io.loadmat(mat_path)
    price_matrix = mat["price"]  # (8761, 8)

    years = list(range(2013, 2021))
    n_hours, n_years = price_matrix.shape

    all_data = []

    for i, year in enumerate(years):
        date_range = pd.date_range(
            start=f"{year}-01-01 00:00",
            periods=n_hours,
            freq="H"
        )

        df_year = pd.DataFrame({
            "timestamp": date_range,
            "year": year,
            "price_eur_mwh": price_matrix[:, i]
        })

        all_data.append(df_year)

    df = pd.concat(all_data).reset_index(drop=True)
    df["price_eur_per_kwh"] = df["price_eur_mwh"] / 1000.0

    df.to_csv(output_csv_path, index=False)
    print("Saved to:", output_csv_path)


if __name__ == "__main__":
    convert_mat_to_csv("PRICE_ALL.mat", "electricity_prices_2013_2020.csv")