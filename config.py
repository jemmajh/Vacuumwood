DEFAULT_YIELD = {"Lettuce": 70.0, "Basil": 30.0}  # kg per m² per year
DEFAULT_PRICE = {"Lettuce": 7.0, "Basil": 20.0}   # € per kg

# --- CAPEX calibrated to Excel ---
CAPEX_BUILDING_PER_M2 = 778.30        # 466,980 / 600
CAPEX_EQUIPMENT_PER_M2 = 950.00       # 2,565,000 / 2700
CAPEX_OTHER_FIXED = 50_000.0
CAPEX_SUBSIDY_SHARE = 0.2952          # 909,594 / 3,081,980

# --- OPEX calibrated to Excel ---
ELEC_KWH_PER_M2_YEAR = 710.0          # from Excel "Total per m2"
OTHER_OPEX_PER_M2_YEAR = 126.16       # (493,884 - 153,265) / 2700

# electricity prices (baseline should match Excel)
ELEC_PRICE_BASE = 0.08
ELEC_PRICE_OPT = 0.08  # override this later from the optimization page