import xml.etree.ElementTree as ET
import pandas as pd
import glob

files = glob.glob("../data/entsoe_raw/entsoe_*.xml")

all_data = []

for file in files:
    print(f"Parsing {file}...")

    tree = ET.parse(file)
    root = tree.getroot()

    ns = {'ns': root.tag.split('}')[0].strip('{')}

    for ts in root.findall(".//ns:TimeSeries", ns):
        for period in ts.findall(".//ns:Period", ns):

            start_time = period.find("ns:timeInterval/ns:start", ns).text

            for point in period.findall("ns:Point", ns):

                position = int(point.find("ns:position", ns).text)
                price = float(point.find("ns:price.amount", ns).text)

                all_data.append([start_time, position, price])

if len(all_data) == 0:
    print("❌ No data extracted — check XML files")
    exit()

df = pd.DataFrame(all_data, columns=["start_time", "hour_position", "price_eur_mwh"])

df["datetime"] = pd.to_datetime(df["start_time"]) + pd.to_timedelta(df["hour_position"] - 1, unit="h")

df["price_eur_kwh"] = df["price_eur_mwh"] / 1000

df["year"] = df["datetime"].dt.year
df["month"] = df["datetime"].dt.month
df["day"] = df["datetime"].dt.day
df["hour"] = df["datetime"].dt.hour

df["season"] = df["month"].map({
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn"
})

df["is_weekend"] = df["datetime"].dt.weekday >= 5

df["source"] = "entsoe"

df = df[
    [
        "datetime",
        "price_eur_mwh",
        "price_eur_kwh",
        "year",
        "month",
        "day",
        "hour",
        "season",
        "is_weekend",
        "source"
    ]
]

df = df.sort_values("datetime").reset_index(drop=True)
df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert("Europe/Helsinki")

df.to_csv("../data/entsoe_clean_all.csv", index=False)

print("🚀 SUCCESS — ENTOS-E data parsed correctly!")
print(df.head())
print(f"Total rows: {len(df)}")