"""
Vertical Farm Dashboard  –  unified Streamlit application
Tabs: Farm Setup | Electricity Optimization | Strategy Comparison | Financial Model
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys, os

# ── path setup ────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(__file__)
sys.path.insert(0, ROOT)

import config as cfg
from core.schemas import FarmInputs, CropInputs, FinanceInputs, ElectricityScenario
from core.model import compute_areas, compute_sales, compute_capex, compute_opex, build_forecast
from core.validation import validate_inputs
from core.lighting_optimization import build_daily_report, yearly_summary_from_daily
from core.strategy_engine import compute_strategy_table, build_comparison_df

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VacuumWood · Vertical Farm Model",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Barlow+Condensed:wght@700&family=Syne:wght@400;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

  .block-container { padding-top: 3.5rem !important; padding-bottom: 2rem !important; }

  [data-testid="stSidebar"] { display: none !important; }
  [data-testid="collapsedControl"] { display: none !important; }
  
  /* logo */
  .vw-container { text-align: center; padding-top: 1.5rem; padding-bottom: 0.5rem; }
  .vw-logo { font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 42px;
             letter-spacing: 4px; line-height: 1.1; }
  .vw-black { color: #000000; }
  .vw-green { color: #3CB371; }

  /* metric cards */
  .metric-card { background: #f8faf9; border: 1.5px solid #e0ece6; border-radius: 12px;
                 padding: 1.1rem 1.3rem; text-align: center; }
  .metric-card .label { font-size: 12px; font-weight: 600; text-transform: uppercase;
                        letter-spacing: 1.5px; color: #7a9e8e; margin-bottom: 4px; }
  .metric-card .value { font-size: 26px; font-weight: 700; color: #111; font-family: 'DM Mono', monospace; }
  .metric-card .sub   { font-size: 12px; color: #aaa; margin-top: 2px; }

  /* saving badge */
  .saving-badge { display:inline-block; background:#e6f5ed; color:#1d7a48; border-radius:20px;
                  padding:3px 12px; font-size:13px; font-weight:700; font-family:'DM Mono',monospace; }
  .saving-neg   { background:#fdecea; color:#c0392b; }

  /* section headers */
  .section-header { font-size:18px; font-weight:700; color:#111; border-bottom:2.5px solid #2D9C5C;
                    padding-bottom:6px; margin:1.4rem 0 1rem; letter-spacing:0.5px; }

  /* tab override */
  div[data-testid="stTabs"] button { font-weight:700; font-size:15px; letter-spacing:0.4px; }
  div[data-testid="stTabs"] button[aria-selected="true"] { color: #2D9C5C !important; }

  /* number inputs */
  div[data-testid="stNumberInput"] label { font-size:13px; font-weight:600; color:#444; }

  /* info box */
  .info-box { background:#f0f7f4; border-left:4px solid #2D9C5C; padding:0.8rem 1rem;
              border-radius:0 8px 8px 0; font-size:14px; color:#2a5a40; margin:0.6rem 0; }

  /* strategy bar highlight */
  .best-strategy { background:#e6f5ed; border:2px solid #2D9C5C; border-radius:10px; padding:0.8rem 1rem; }
</style>
""", unsafe_allow_html=True)

# ── logo ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vw-container" aria-label="VacuumWood logo">
  <div class="vw-logo">
    <div class="vw-black">VACUUM</div>
    <div class="vw-black">WOOD.</div>
    <div class="vw-green">TECH</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  DATA LOADING  (cached)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="Loading electricity price data…")
def load_price_data():
    path = os.path.join(ROOT, "data", "clean_data", "electricity_prices_full.csv")
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df = df[df["year"] <= 2025].copy()
    df["timestamp"] = df["datetime"]
    df["price_eur_per_kwh"] = df["price_eur_kwh"]
    return df

@st.cache_data(show_spinner="Computing strategy comparison…")
def load_strategy_yearly():
    df = load_price_data()
    return compute_strategy_table(df)

@st.cache_data(show_spinner="Running lighting optimisation…")
def load_lighting_optimisation(fixed_start: int):
    df = load_price_data()
    daily = build_daily_report(df, hours_needed=18, fixed_start_hour=fixed_start)
    yearly = yearly_summary_from_daily(daily)
    return daily, yearly

price_df   = load_price_data()
strat_yr   = load_strategy_yearly()

# ═══════════════════════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "️Farm Setup",
    "Electricity Optimisation",
    "Strategy Comparison",
    "Financial Model",
])

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 1  –  FARM SETUP
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">Building Dimensions</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    length = c1.number_input("Length (m)", 5.0, 500.0, cfg.DEFAULT_LENGTH_M, 1.0)
    width  = c2.number_input("Width (m)",  5.0, 500.0, cfg.DEFAULT_WIDTH_M,  1.0)
    height = c3.number_input("Height (m)", 2.0,  20.0, cfg.DEFAULT_HEIGHT_M, 0.1)
    floors = c4.number_input("Number of Floors", 1, 30, cfg.DEFAULT_FLOORS, 1)

    c5, c6 = st.columns(2)
    floor_eff  = c5.slider("Floor Usage Efficiency", 0.40, 1.00, cfg.DEFAULT_FLOOR_USAGE_EFF, 0.01,
                           help="Share of each floor that is actual cultivation area")
    insulation = c6.number_input("Insulation thickness (m)", 0.05, 1.0, cfg.DEFAULT_INSULATION_M, 0.05)

    farm = FarmInputs(length_m=length, width_m=width, height_m=height,
                      insulation_m=insulation, floor_usage_eff=floor_eff, floors=floors)
    areas = compute_areas(farm)

    # area summary cards
    st.markdown('<div class="section-header">Area Summary</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.markdown(f"""<div class="metric-card">
        <div class="label">Floor Area</div>
        <div class="value">{areas['floor_area']:,.0f} m²</div>
        <div class="sub">per floor</div></div>""", unsafe_allow_html=True)
    m2.markdown(f"""<div class="metric-card">
        <div class="label">Cultivation / Floor</div>
        <div class="value">{areas['cultivable_per_floor']:,.0f} m²</div>
        <div class="sub">after {floor_eff*100:.0f}% efficiency</div></div>""", unsafe_allow_html=True)
    m3.markdown(f"""<div class="metric-card">
        <div class="label">Total Cultivatable</div>
        <div class="value">{areas['total_cultivatable']:,.0f} m²</div>
        <div class="sub">{floors} floors combined</div></div>""", unsafe_allow_html=True)

    # ── Crop configuration ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Crop Configuration</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Defaults from the VacuumWood Excel model · adjust to explore scenarios</div>',
                unsafe_allow_html=True)

    crop_cols = st.columns(2)
    crop_data = {}
    all_crops = ["Lettuce", "Basil", "Spinach", "Microgreens"]
    selected_crops = []

    with crop_cols[0]:
        st.markdown("**Crop selection & area share**")
        lettuce_share = st.slider("Lettuce share (%)", 0, 100, int(cfg.DEFAULT_SHARES["Lettuce"]*100), 5) / 100
        basil_share   = st.slider("Basil share (%)",   0, 100, int(cfg.DEFAULT_SHARES["Basil"]*100),   5) / 100
        remaining = max(0.0, 1.0 - lettuce_share - basil_share)
        st.caption(f"Remaining share: {remaining*100:.1f}%  (unallocated area)")

    with crop_cols[1]:
        st.markdown("**Yield & price (€/kg)**")
        lettuce_yield = st.number_input("Lettuce yield (kg/m²/yr)", 10.0, 200.0, cfg.DEFAULT_YIELDS["Lettuce"], 5.0)
        basil_yield   = st.number_input("Basil yield (kg/m²/yr)",   5.0,  150.0, cfg.DEFAULT_YIELDS["Basil"],   5.0)
        lettuce_price = st.number_input("Lettuce price (€/kg)", 1.0, 50.0, cfg.DEFAULT_PRICE["Lettuce"], 0.5)
        basil_price   = st.number_input("Basil price (€/kg)",   1.0, 80.0, cfg.DEFAULT_PRICE["Basil"],   1.0)

    shares = {}
    yields_map = {}
    prices_map = {}
    if lettuce_share > 0:
        shares["Lettuce"] = lettuce_share
        yields_map["Lettuce"] = lettuce_yield
        prices_map["Lettuce"] = lettuce_price
        selected_crops.append("Lettuce")
    if basil_share > 0:
        shares["Basil"] = basil_share
        yields_map["Basil"] = basil_yield
        prices_map["Basil"] = basil_price
        selected_crops.append("Basil")

    # patch config prices for this session
    cfg.DEFAULT_PRICE["Lettuce"] = lettuce_price
    cfg.DEFAULT_PRICE["Basil"]   = basil_price

    share_sum = sum(shares.values())
    errors = validate_inputs(shares, int(floors), cfg.DEFAULT_DISCOUNT_RATE,
                             cfg.DEFAULT_YEAR1_EFF, cfg.DEFAULT_EFF_GAIN, cfg.DEFAULT_YEARS)
    if errors:
        for e in errors:
            st.error(e)

    # store in session state for other tabs
    st.session_state["farm"]    = farm
    st.session_state["areas"]   = areas
    st.session_state["shares"]  = shares
    st.session_state["yields"]  = yields_map
    st.session_state["crops"]   = selected_crops

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 2  –  ELECTRICITY OPTIMISATION
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">Electricity Price Optimisation</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        Nordic electricity (FI) spot prices 2013–2025. Three scheduling strategies are compared
        against a fixed start-time baseline. The chosen optimised price feeds into the Financial Model.
    </div>""", unsafe_allow_html=True)

    col_ctrl, col_chart = st.columns([1, 2])

    with col_ctrl:
        fixed_start = st.selectbox("Fixed schedule start hour", list(range(24)),
                                   index=6, format_func=lambda h: f"{h:02d}:00")
        year_filter = st.multiselect("Filter years", sorted(price_df["year"].unique().tolist()),
                                     default=sorted(price_df["year"].unique().tolist()))

    daily_rep, yearly_opt = load_lighting_optimisation(fixed_start)

    # filter by selected years
    yearly_f = yearly_opt[yearly_opt["year"].isin(year_filter)] if year_filter else yearly_opt
    daily_f  = daily_rep[daily_rep["year"].isin(year_filter)]   if year_filter else daily_rep

    # ── savings summary cards ─────────────────────────────────────────────────
    if not yearly_f.empty:
        avg_fixed = yearly_f["fixed_savings_pct"].mean()
        avg_cont  = yearly_f["continuous_savings_pct"].mean()
        avg_spar  = yearly_f["sparse_savings_pct"].mean()

        avg_fixed_price = yearly_f["fixed_price_year_eur_kwh"].mean()
        avg_cont_price  = yearly_f["continuous_price_year_eur_kwh"].mean()
        avg_spar_price  = yearly_f["sparse_price_year_eur_kwh"].mean()
        avg_base_price  = yearly_f["avg_price_year_eur_kwh"].mean()

        st.markdown('<div class="section-header">Average Savings vs Unoptimised Baseline</div>',
                    unsafe_allow_html=True)
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.markdown(f"""<div class="metric-card">
            <div class="label">Unoptimised avg</div>
            <div class="value">{avg_base_price*100:.2f} c/kWh</div>
            <div class="sub">no scheduling</div></div>""", unsafe_allow_html=True)
        mc2.markdown(f"""<div class="metric-card">
            <div class="label">Fixed ({fixed_start:02d}:00)</div>
            <div class="value">{avg_fixed_price*100:.2f} c/kWh</div>
            <div class="sub"><span class="saving-badge">{'▼' if avg_fixed>=0 else '▲'} {abs(avg_fixed):.1f}%</span></div>
            </div>""", unsafe_allow_html=True)
        mc3.markdown(f"""<div class="metric-card">
            <div class="label">Continuous block</div>
            <div class="value">{avg_cont_price*100:.2f} c/kWh</div>
            <div class="sub"><span class="saving-badge">▼ {avg_cont:.1f}%</span></div>
            </div>""", unsafe_allow_html=True)
        mc4.markdown(f"""<div class="metric-card">
            <div class="label">Sparse (cheapest hrs)</div>
            <div class="value">{avg_spar_price*100:.2f} c/kWh</div>
            <div class="sub"><span class="saving-badge">▼ {avg_spar:.1f}%</span></div>
            </div>""", unsafe_allow_html=True)

        # ── store for financial tab ────────────────────────────────────────────
        st.session_state["elec_base_price"] = avg_base_price
        st.session_state["elec_cont_price"] = avg_cont_price
        st.session_state["elec_spar_price"] = avg_spar_price
        st.session_state["elec_savings_cont"] = avg_cont
        st.session_state["elec_savings_spar"] = avg_spar

        # ── yearly savings trend chart ─────────────────────────────────────────
        st.markdown('<div class="section-header">Yearly Savings Trend (%)</div>', unsafe_allow_html=True)
        fig_sav = go.Figure()
        fig_sav.add_trace(go.Scatter(x=yearly_f["year"], y=yearly_f["fixed_savings_pct"],
                          mode="lines+markers", name="Fixed", line=dict(color="#f0a500", width=2)))
        fig_sav.add_trace(go.Scatter(x=yearly_f["year"], y=yearly_f["continuous_savings_pct"],
                          mode="lines+markers", name="Continuous", line=dict(color="#2D9C5C", width=2)))
        fig_sav.add_trace(go.Scatter(x=yearly_f["year"], y=yearly_f["sparse_savings_pct"],
                          mode="lines+markers", name="Sparse", line=dict(color="#1a6edb", width=2)))
        fig_sav.update_layout(
            height=320, margin=dict(t=10, b=30, l=40, r=10),
            yaxis_title="Savings vs unoptimised (%)",
            legend=dict(orientation="h", y=-0.25),
            plot_bgcolor="#fafafa", paper_bgcolor="white",
            font=dict(family="Syne"),
        )
        st.plotly_chart(fig_sav, use_container_width=True)

        # ── average price by year ──────────────────────────────────────────────
        st.markdown('<div class="section-header">Average Electricity Price by Year (€/kWh)</div>',
                    unsafe_allow_html=True)
        fig_pr = go.Figure()
        fig_pr.add_trace(go.Bar(x=yearly_f["year"], y=yearly_f["avg_price_year_eur_kwh"],
                         name="Unoptimised", marker_color="#dde8e2"))
        fig_pr.add_trace(go.Bar(x=yearly_f["year"], y=yearly_f["continuous_price_year_eur_kwh"],
                         name="Continuous", marker_color="#2D9C5C"))
        fig_pr.add_trace(go.Bar(x=yearly_f["year"], y=yearly_f["sparse_price_year_eur_kwh"],
                         name="Sparse", marker_color="#1a6edb"))
        fig_pr.update_layout(
            barmode="group", height=300, margin=dict(t=10, b=30, l=50, r=10),
            yaxis_title="€/kWh",
            legend=dict(orientation="h", y=-0.28),
            plot_bgcolor="#fafafa", paper_bgcolor="white",
            font=dict(family="Syne"),
        )
        st.plotly_chart(fig_pr, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 3  –  STRATEGY COMPARISON (interactive)
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">Lighting Strategy Comparison</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-box">
        Compare three scheduling strategies across different daily light hour requirements.
        <b>Continuous</b> = cheapest consecutive block · <b>Split</b> = two equal blocks ·
        <b>Sparse</b> = cheapest individual hours (plant-stress risk).
    </div>""", unsafe_allow_html=True)

    sc1, sc2 = st.columns([1, 3])
    with sc1:
        hours_choice = st.radio("Daily light hours", [12, 16, 18],
                                index=2, horizontal=False,
                                help="18 h matches the default farm model (6,570 h/yr ÷ 365)")
        year_range = st.select_slider("Year range",
                                      options=sorted(strat_yr["year"].tolist()),
                                      value=(int(strat_yr["year"].min()), int(strat_yr["year"].max())))
        show_cost   = st.checkbox("Show absolute cost (€/day)", value=False)
        show_saving = st.checkbox("Show savings % vs baseline", value=True)

    comp_df = build_comparison_df(strat_yr, hours_choice)
    comp_df = comp_df[(comp_df["year"] >= year_range[0]) & (comp_df["year"] <= year_range[1])]

    with sc2:
        if show_cost:
            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(x=comp_df["year"], y=comp_df["baseline_cost"],
                            name="Unoptimised baseline", marker_color="#e0e0e0"))
            fig_c.add_trace(go.Bar(x=comp_df["year"], y=comp_df["continuous_cost"],
                            name="Continuous block", marker_color="#f0a500"))
            fig_c.add_trace(go.Bar(x=comp_df["year"], y=comp_df["split_cost"],
                            name="Split (2 blocks)", marker_color="#2D9C5C"))
            fig_c.add_trace(go.Bar(x=comp_df["year"], y=comp_df["sparse_cost"],
                            name="Sparse (cheapest hrs)", marker_color="#1a6edb"))
            fig_c.update_layout(barmode="group", height=340,
                                yaxis_title=f"Avg daily cost for {hours_choice}h (€)",
                                margin=dict(t=15,b=30,l=50,r=10),
                                legend=dict(orientation="h",y=-0.30),
                                plot_bgcolor="#fafafa", paper_bgcolor="white",
                                font=dict(family="Syne"))
            st.plotly_chart(fig_c, use_container_width=True)

        if show_saving:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=comp_df["year"], y=comp_df["continuous_saving_pct"],
                            mode="lines+markers", name="Continuous", line=dict(color="#f0a500", width=2.5)))
            fig_s.add_trace(go.Scatter(x=comp_df["year"], y=comp_df["split_saving_pct"],
                            mode="lines+markers", name="Split", line=dict(color="#2D9C5C", width=2.5)))
            fig_s.add_trace(go.Scatter(x=comp_df["year"], y=comp_df["sparse_saving_pct"],
                            mode="lines+markers", name="Sparse", line=dict(color="#1a6edb", width=2.5)))
            fig_s.update_layout(height=320, yaxis_title="Savings vs unoptimised baseline (%)",
                                margin=dict(t=15,b=30,l=50,r=10),
                                legend=dict(orientation="h",y=-0.30),
                                plot_bgcolor="#fafafa", paper_bgcolor="white",
                                font=dict(family="Syne"))
            st.plotly_chart(fig_s, use_container_width=True)

    # ── summary table ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Summary Table</div>', unsafe_allow_html=True)
    avg_row = comp_df[["continuous_saving_pct","split_saving_pct","sparse_saving_pct"]].mean()
    best    = avg_row.idxmax()
    best_label = {"continuous_saving_pct": "Continuous Block",
                  "split_saving_pct":      "Split (2 Blocks)",
                  "sparse_saving_pct":     "Sparse (Cheapest Hours)"}[best]

    st.markdown(f"""<div class="best-strategy">
        🏆 <b>Best strategy for {hours_choice}h/day</b> over selected period:
        <b>{best_label}</b> — average saving of
        <span class="saving-badge">▼ {avg_row[best]:.1f}%</span>
        vs paying unoptimised spot price
    </div>""", unsafe_allow_html=True)

    disp = comp_df[["year","baseline_cost","continuous_cost","split_cost","sparse_cost",
                    "continuous_saving_pct","split_saving_pct","sparse_saving_pct"]].copy()
    disp.columns = ["Year","Baseline (€)","Continuous (€)","Split (€)","Sparse (€)",
                    "Continuous saving %","Split saving %","Sparse saving %"]
    disp = disp.set_index("Year")
    st.dataframe(
        disp.style
            .format({"Baseline (€)":"{:.3f}","Continuous (€)":"{:.3f}",
                     "Split (€)":"{:.3f}","Sparse (€)":"{:.3f}",
                     "Continuous saving %":"{:.1f}%","Split saving %":"{:.1f}%","Sparse saving %":"{:.1f}%"})
            .background_gradient(subset=["Continuous saving %","Split saving %","Sparse saving %"],
                                 cmap="Greens"),
        use_container_width=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
#  TAB 4  –  FINANCIAL MODEL
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">Financial Assumptions</div>', unsafe_allow_html=True)

    # pull areas/crops from session state (set in tab1)
    areas_t4  = st.session_state.get("areas", compute_areas(FarmInputs(
        cfg.DEFAULT_LENGTH_M, cfg.DEFAULT_WIDTH_M, cfg.DEFAULT_HEIGHT_M,
        cfg.DEFAULT_INSULATION_M, cfg.DEFAULT_FLOOR_USAGE_EFF, cfg.DEFAULT_FLOORS)))
    shares_t4 = st.session_state.get("shares", cfg.DEFAULT_SHARES)
    yields_t4 = st.session_state.get("yields", cfg.DEFAULT_YIELDS)
    crops_t4  = st.session_state.get("crops",  cfg.DEFAULT_CROPS)

    if not shares_t4 or abs(sum(shares_t4.values()) - 1.0) > 0.01:
        st.warning("Crop shares don't sum to 100% — check Farm Setup tab.")
        shares_t4 = cfg.DEFAULT_SHARES
        yields_t4 = cfg.DEFAULT_YIELDS
        crops_t4  = cfg.DEFAULT_CROPS

    fc1, fc2, fc3 = st.columns(3)
    discount_rate = fc1.number_input("Discount rate (%)", 1.0, 30.0,
                                     cfg.DEFAULT_DISCOUNT_RATE * 100, 0.5) / 100
    year1_eff     = fc2.slider("Year 1 operational efficiency", 0.50, 1.00, cfg.DEFAULT_YEAR1_EFF, 0.01)
    eff_gain      = fc3.number_input("Annual efficiency gain (%)", 0.0, 10.0,
                                     cfg.DEFAULT_EFF_GAIN * 100, 0.5) / 100
    fin_years     = st.slider("Forecast years", 5, 20, cfg.DEFAULT_YEARS)

    # ── electricity price scenario ─────────────────────────────────────────────
    st.markdown('<div class="section-header">Electricity Price Scenario</div>', unsafe_allow_html=True)

    base_price_default = st.session_state.get("elec_base_price", cfg.BASE_ELEC_PRICE)
    cont_price_default = st.session_state.get("elec_cont_price", base_price_default * 0.87)
    spar_price_default = st.session_state.get("elec_spar_price", base_price_default * 0.80)
    saving_cont = st.session_state.get("elec_savings_cont", 13.0)
    saving_spar = st.session_state.get("elec_savings_spar", 20.0)

    ep1, ep2 = st.columns([1, 2])
    with ep1:
        scenario_choice = st.radio(
            "Select electricity scenario",
            ["Base (no optimisation)", "Continuous block", "Sparse (cheapest hours)"],
            index=0,
        )
        st.markdown(f"""<div class="info-box">
            <b>Continuous block</b> saves ~<b>{saving_cont:.1f}%</b> vs baseline<br>
            <b>Sparse strategy</b> saves ~<b>{saving_spar:.1f}%</b> vs baseline<br>
            <small>Based on 2013–2025 Nord Pool FI spot prices</small>
        </div>""", unsafe_allow_html=True)

    with ep2:
        base_price_input = st.number_input("Base electricity price (€/kWh)",
                                           0.01, 0.50, float(round(base_price_default, 4)), 0.005,
                                           format="%.4f")
        opt_price_input  = st.number_input("Optimised electricity price (€/kWh)",
                                           0.005, 0.40,
                                           float(round(min(cont_price_default, spar_price_default), 4)),
                                           0.005, format="%.4f",
                                           help="Populated from Electricity Optimisation tab")

    scenario_map = {
        "Base (no optimisation)":   "base",
        "Continuous block":         "opt",
        "Sparse (cheapest hours)":  "opt",
    }
    opt_price_used = {
        "Base (no optimisation)":   base_price_input,
        "Continuous block":         cont_price_default,
        "Sparse (cheapest hours)":  spar_price_default,
    }[scenario_choice]

    scenario = ElectricityScenario(
        base_price_eur_kwh=base_price_input,
        opt_price_eur_kwh=opt_price_used,
        selected=scenario_map[scenario_choice],
    )

    # ── compute model ──────────────────────────────────────────────────────────
    crop_inputs = CropInputs(selected=crops_t4, shares=shares_t4, yields_kg_m2_yr=yields_t4)
    sales_df, total_sales = compute_sales(areas_t4["total_cultivatable"], crop_inputs)
    capex   = compute_capex(areas_t4["floor_area"], areas_t4["total_cultivatable"])
    opex    = compute_opex(areas_t4["total_cultivatable"], scenario)
    fin_in  = FinanceInputs(discount_rate=discount_rate, year1_eff=year1_eff,
                            eff_gain=eff_gain, years=fin_years)
    forecast, payback = build_forecast(total_sales, opex["yearly_opex"], capex["net"], fin_in)

    # also compute base+opt for comparison
    scen_base = ElectricityScenario(base_price_eur_kwh=base_price_input,
                                    opt_price_eur_kwh=opt_price_used, selected="base")
    scen_opt  = ElectricityScenario(base_price_eur_kwh=base_price_input,
                                    opt_price_eur_kwh=opt_price_used, selected="opt")
    opex_base = compute_opex(areas_t4["total_cultivatable"], scen_base)
    opex_opt  = compute_opex(areas_t4["total_cultivatable"], scen_opt)
    _, payback_base = build_forecast(total_sales, opex_base["yearly_opex"], capex["net"], fin_in)
    _, payback_opt  = build_forecast(total_sales, opex_opt["yearly_opex"],  capex["net"], fin_in)

    elec_saving_eur = opex_base["elec_cost"] - opex_opt["elec_cost"]
    elec_saving_pct = (elec_saving_eur / opex_base["elec_cost"] * 100) if opex_base["elec_cost"] > 0 else 0

    # ── KPI row ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Key Financials</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(f"""<div class="metric-card">
        <div class="label">Total Sales / yr</div>
        <div class="value">€{total_sales/1e6:.2f}M</div>
        <div class="sub">{areas_t4['total_cultivatable']:,.0f} m²</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="metric-card">
        <div class="label">CapEx (net)</div>
        <div class="value">€{capex['net']/1e6:.2f}M</div>
        <div class="sub">gross €{capex['gross']/1e6:.2f}M · subsidy €{capex['subsidy']/1e3:.0f}k</div></div>""",
        unsafe_allow_html=True)
    k3.markdown(f"""<div class="metric-card">
        <div class="label">Total OpEx / yr</div>
        <div class="value">€{opex['yearly_opex']/1e3:.0f}k</div>
        <div class="sub">elec €{opex['elec_cost']/1e3:.0f}k + other €{opex['other_opex']/1e3:.0f}k</div></div>""",
        unsafe_allow_html=True)
    k4.markdown(f"""<div class="metric-card">
        <div class="label">Elec saving (opt vs base)</div>
        <div class="value">€{abs(elec_saving_eur)/1e3:.0f}k/yr</div>
        <div class="sub"><span class="saving-badge">▼ {elec_saving_pct:.1f}%</span></div></div>""",
        unsafe_allow_html=True)
    payback_str = f"Year {payback}" if payback else ">forecast"
    k5.markdown(f"""<div class="metric-card">
        <div class="label">Payback (current)</div>
        <div class="value">{payback_str}</div>
        <div class="sub">base: yr {payback_base or '—'} · opt: yr {payback_opt or '—'}</div></div>""",
        unsafe_allow_html=True)

    # ── OpEx breakdown ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">OpEx Breakdown — Electricity vs Other Costs</div>',
                unsafe_allow_html=True)

    elec_pct_base = opex_base["elec_cost"] / opex_base["yearly_opex"] * 100
    elec_pct_opt  = opex_opt["elec_cost"]  / opex_opt["yearly_opex"]  * 100

    ob1, ob2, ob3 = st.columns([1.1, 1.1, 0.9])

    # Left: stacked bar — base vs optimised, showing elec + other split
    with ob1:
        fig_stack = go.Figure()
        fig_stack.add_trace(go.Bar(
            name="Electricity", x=["Base scenario", "Optimised scenario"],
            y=[opex_base["elec_cost"], opex_opt["elec_cost"]],
            marker_color=["#f0a500", "#2D9C5C"],
            text=[f"€{opex_base['elec_cost']/1e3:.0f}k<br>({elec_pct_base:.0f}%)",
                  f"€{opex_opt['elec_cost']/1e3:.0f}k<br>({elec_pct_opt:.0f}%)"],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color="white", size=13, family="DM Mono"),
        ))
        fig_stack.add_trace(go.Bar(
            name="Other OpEx", x=["Base scenario", "Optimised scenario"],
            y=[opex_base["other_opex"], opex_opt["other_opex"]],
            marker_color=["#d0ddd8", "#d0ddd8"],
            text=[f"€{opex_base['other_opex']/1e3:.0f}k<br>({100-elec_pct_base:.0f}%)",
                  f"€{opex_opt['other_opex']/1e3:.0f}k<br>({100-elec_pct_opt:.0f}%)"],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color="#555", size=13, family="DM Mono"),
        ))
        fig_stack.update_layout(
            barmode="stack", height=300,
            margin=dict(t=10, b=10, l=50, r=10),
            yaxis_title="Annual OpEx (€)",
            legend=dict(orientation="h", y=-0.18),
            plot_bgcolor="#fafafa", paper_bgcolor="white",
            font=dict(family="Syne"),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

    # Middle: donut — electricity share of base opex
    with ob2:
        fig_donut = go.Figure(go.Pie(
            labels=["Electricity", "Other OpEx"],
            values=[opex_base["elec_cost"], opex_base["other_opex"]],
            hole=0.62,
            marker_colors=["#f0a500", "#d0ddd8"],
            textinfo="label+percent",
            textfont=dict(family="Syne", size=13),
            hovertemplate="%{label}: €%{value:,.0f}<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>{elec_pct_base:.0f}%</b><br>electricity",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, family="Syne", color="#111"),
        )
        fig_donut.update_layout(
            height=300, margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False, paper_bgcolor="white",
            title=dict(text="Base OpEx split", font=dict(size=13, family="Syne"), x=0.5),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Right: savings summary callout
    with ob3:
        saving_eur  = opex_base["elec_cost"] - opex_opt["elec_cost"]
        saving_pct_ = saving_eur / opex_base["elec_cost"] * 100 if opex_base["elec_cost"] > 0 else 0
        total_saving_pct = saving_eur / opex_base["yearly_opex"] * 100

        st.markdown(f"""
        <div style="padding-top:10px">
          <div class="metric-card" style="margin-bottom:12px">
            <div class="label">Electricity share of OpEx</div>
            <div class="value">{elec_pct_base:.0f}%</div>
            <div class="sub">base · {elec_pct_opt:.0f}% optimised</div>
          </div>
          <div class="metric-card" style="margin-bottom:12px">
            <div class="label">Annual elec. saving</div>
            <div class="value">€{saving_eur/1e3:.1f}k</div>
            <div class="sub"><span class="saving-badge">▼ {saving_pct_:.1f}% of elec cost</span></div>
          </div>
          <div class="metric-card">
            <div class="label">Total OpEx reduction</div>
            <div class="value">{total_saving_pct:.1f}%</div>
            <div class="sub">from electricity optimisation alone</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── revenue–cost waterfall ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">Revenue & Cost Waterfall</div>', unsafe_allow_html=True)
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Annual Revenue", "Electricity (base)", "Elec. saving (opt)", "Other OpEx", "Net Margin"],
        y=[
            total_sales,
            -opex_base["elec_cost"],
            saving_eur,
            -opex_base["other_opex"],
            0,
        ],
        connector={"line": {"color": "#ccc", "width": 1}},
        increasing={"marker": {"color": "#2D9C5C"}},
        decreasing={"marker": {"color": "#e05050"}},
        totals={"marker": {"color": "#1a6edb"}},
        text=[
            f"€{total_sales/1e3:.0f}k",
            f"−€{opex_base['elec_cost']/1e3:.0f}k",
            f"+€{saving_eur/1e3:.0f}k",
            f"−€{opex_base['other_opex']/1e3:.0f}k",
            f"€{(total_sales - opex_base['other_opex'] - opex_opt['elec_cost'])/1e3:.0f}k",
        ],
        textposition="outside",
        textfont=dict(family="DM Mono", size=12),
    ))
    fig_wf.update_layout(
        height=320, margin=dict(t=15, b=10, l=60, r=10),
        yaxis_title="€", plot_bgcolor="#fafafa", paper_bgcolor="white",
        font=dict(family="Syne"),
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    # ── NPV / payback chart ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">NPV Forecast — Base vs Optimised Electricity</div>',
                unsafe_allow_html=True)

    fc_base, _ = build_forecast(total_sales, opex_base["yearly_opex"], capex["net"], fin_in)
    fc_opt,  _ = build_forecast(total_sales, opex_opt["yearly_opex"],  capex["net"], fin_in)

    fig_npv = go.Figure()
    fig_npv.add_hline(y=0, line_dash="dot", line_color="#999", line_width=1.5)
    fig_npv.add_trace(go.Scatter(
        x=fc_base["Year"], y=fc_base["NPV - CAPEX (€)"],
        mode="lines+markers", name="Base electricity",
        line=dict(color="#ccc", width=2), marker=dict(size=6),
        fill="tozeroy", fillcolor="rgba(200,200,200,0.15)"
    ))
    fig_npv.add_trace(go.Scatter(
        x=fc_opt["Year"], y=fc_opt["NPV - CAPEX (€)"],
        mode="lines+markers", name="Optimised electricity",
        line=dict(color="#2D9C5C", width=2.5), marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(45,156,92,0.10)"
    ))
    fig_npv.update_layout(
        height=370, margin=dict(t=15,b=30,l=60,r=10),
        yaxis_title="Cumulative NPV − CapEx (€)",
        xaxis_title="Year",
        legend=dict(orientation="h", y=-0.22),
        plot_bgcolor="#fafafa", paper_bgcolor="white",
        font=dict(family="Syne"),
    )
    st.plotly_chart(fig_npv, use_container_width=True)

    # ── forecast table ─────────────────────────────────────────────────────────
    with st.expander("Detailed forecast table"):
        disp_fc = forecast.copy()
        for col in ["Net Cashflow (€)", "Discounted (€)", "Cumulative NPV (€)", "NPV - CAPEX (€)"]:
            disp_fc[col] = disp_fc[col].map(lambda x: f"€{x:,.0f}")
        st.dataframe(disp_fc.set_index("Year"), use_container_width=True)

    # ── sales breakdown ────────────────────────────────────────────────────────
    with st.expander("Revenue breakdown by crop"):
        disp_sales = sales_df.copy()
        disp_sales["Revenue (€)"] = disp_sales["Revenue (€)"].map(lambda x: f"€{x:,.0f}")
        disp_sales["Area (m²)"] = disp_sales["Area (m²)"].map(lambda x: f"{x:,.0f}")
        st.dataframe(disp_sales, use_container_width=True)