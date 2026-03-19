import os
import requests
import pandas as pd
from datetime import date, timedelta

STS_TOKEN_URL = "https://sts.nordpoolgroup.com/connect/token"  # OAuth token endpoint  [oai_citation:4‡Nord Pool](https://www.nordpoolgroup.com/en/services/power-market-data-services/faq/faq-premium-container/technical/?utm_source=chatgpt.com)
BASE_API_URL = "https://data-api.nordpoolgroup.com"

def get_access_token(username: str, password: str, basic_auth_b64: str) -> str:
    # basic_auth_b64 is the base64 string used in the Authorization header (from Nord Pool FAQ examples)  [oai_citation:5‡Nord Pool](https://www.nordpoolgroup.com/en/services/power-market-data-services/faq/faq-premium-container/technical/?utm_source=chatgpt.com)
    headers = {"Authorization": f"Basic {basic_auth_b64}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "password",
        "scope": "marketdata_api",
        "username": username,
        "password": password,
    }
    r = requests.post(STS_TOKEN_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def fetch_day_ahead_prices_FI(token: str, subscription_key: str, delivery_date: date) -> pd.DataFrame:
    """
    Uses Market Data API v2 Auction Prices endpoint (see API definition listing endpoints).  [oai_citation:6‡Nord Pool Data API](https://data-api.nordpoolgroup.com/index.html?utm_source=chatgpt.com)
    NOTE: parameter names in the final request must match Nord Pool v2 swagger.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Ocp-Apim-Subscription-Key": subscription_key,  # subscription key required  [oai_citation:7‡Nord Pool](https://www.nordpoolgroup.com/en/services/power-market-data-services/faq/faq-premium-container/technical-212/?utm_source=chatgpt.com)
        "Accept": "application/json",
    }

    # Endpoint name exists in API definition; exact query params come from swagger.  [oai_citation:8‡Nord Pool Data API](https://data-api.nordpoolgroup.com/index.html?utm_source=chatgpt.com)
    url = f"{BASE_API_URL}/api/v2/Auction/Prices/ByArea"
    params = {
        "deliveryArea": "FI",
        "date": delivery_date.isoformat(),
        "currency": "EUR",
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()

    # You’ll map payload -> DataFrame once you see the exact schema from swagger response.
    # Typical outcome: timestamps + prices (EUR/MWh or EUR/kWh).
    rows = []
    for item in payload.get("data", []):
        rows.append({
            "start": item["startTime"],
            "end": item["endTime"],
            "price_eur_mwh": item["price"],
        })
    df = pd.DataFrame(rows)
    df["start"] = pd.to_datetime(df["start"])
    df["price_eur_per_kwh"] = df["price_eur_mwh"] / 1000.0
    return df.sort_values("start").reset_index(drop=True)

def tomorrow() -> date:
    return date.today() + timedelta(days=1)