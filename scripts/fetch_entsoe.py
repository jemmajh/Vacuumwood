import requests
import os

API_KEY = "447dddf9-d16d-4199-af98-9064437ad696"
DOMAIN = "10YFI-1--------U"

url = "https://web-api.tp.entsoe.eu/api"

years = [2025]

output_dir = "data/entsoe_raw"
os.makedirs(output_dir, exist_ok=True)
for year in years:
    print(f"Downloading {year}...")

    params = {
        "securityToken": API_KEY,
        "documentType": "A44",
        "in_Domain": DOMAIN,
        "out_Domain": DOMAIN,
        "periodStart": f"{year}01010000",
        "periodEnd": f"{year}12312300"
    }

    response = requests.get(url, params=params)

    file_path = f"{output_dir}/entsoe_{year}.xml"

    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"Saved: {file_path}")