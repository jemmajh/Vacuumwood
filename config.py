# defaults extracted from Vertical_farming_finances_model.xlsx

# Farm geometry
DEFAULT_LENGTH_M        = 30.0
DEFAULT_WIDTH_M         = 20.0
DEFAULT_HEIGHT_M        = 2.6
DEFAULT_INSULATION_M    = 0.3
DEFAULT_FLOOR_USAGE_EFF = 0.75
DEFAULT_FLOORS          = 6

# Energy
LED_POWER_W_PER_M2      = 80.0     # LED light W/m²
LIGHT_HOURS_PER_YEAR    = 6570     # hours/yr (18 h/day × 365)
CLIMATE_W_PER_M2        = 20.0
OTHER_W_PER_M2          = 8.0
ELEC_KWH_PER_M2_YEAR    = 709.56  # total kWh/m²/yr
BASE_ELEC_PRICE         = 0.080   # €/kWh (base scenario from spreadsheet)

# Crops
DEFAULT_CROPS           = ["Lettuce", "Basil"]
DEFAULT_SHARES          = {"Lettuce": 0.80, "Basil": 0.20}
DEFAULT_YIELDS          = {"Lettuce": 70.0,  "Basil": 30.0}  # kg/m²/yr
DEFAULT_PRICE           = {"Lettuce": 7.0,   "Basil": 20.0}  # €/kg

# CapEx (from Investointi)
CAPEX_BUILDING_PER_M2   = 466_980 / 600     # ≈ 778 €/m² floor area
CAPEX_EQUIPMENT_PER_M2  = 2_565_000 / 2700  # ≈ 950 €/m² cultivatable
CAPEX_OTHER_FIXED       = 50_000
CAPEX_SUBSIDY_SHARE     = 909_594 / (466_980 + 2_565_000 + 50_000)  # ≈ 0.295

# OpEx
OTHER_OPEX_PER_M2_YEAR  = (493_884.36 - 153_264.96) / 2700  # non-elec opex/m²

# Finance (from Takaisinmaksu)
DEFAULT_DISCOUNT_RATE   = 0.05
DEFAULT_YEAR1_EFF       = 0.80
DEFAULT_EFF_GAIN        = 0.015
DEFAULT_YEARS           = 10

# Lighting strategy hours default
DEFAULT_LIGHT_HOURS_DAY = 18  # 6570 / 365 ≈ 18 h/day