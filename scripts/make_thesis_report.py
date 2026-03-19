import pandas as pd
from core.lighting_optimization import build_daily_report, yearly_summary_from_daily

df = pd.read_csv("electricity_prices_2013_2020.csv", parse_dates=["timestamp"])

# Choose realistic daily lighting hours for vertical farming (common: 14–18)
for hours_needed in [14, 16, 18]:
    daily = build_daily_report(df, hours_needed=hours_needed, fixed_start_hour=6)
    yearly = yearly_summary_from_daily(daily)

    daily.to_csv(f"thesis_daily_report_{hours_needed}h.csv", index=False)
    yearly.to_csv(f"thesis_yearly_summary_{hours_needed}h.csv", index=False)

    print(f"Saved reports for {hours_needed}h/day")