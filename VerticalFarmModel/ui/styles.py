import streamlit as st

from ui.styles import apply_branding, vw_section


# -----------------------------
# Page config (must be first Streamlit call)
# -----------------------------
st.set_page_config(
    page_title="VacuumWood Financial Model",
    layout="wide",
    initial_sidebar_state="collapsed",  # hides the big input sidebar feeling
)

# Branding header (logo)
apply_branding()

# Optional: remove Streamlit top padding a bit
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Main content (no big input UI)
# -----------------------------
vw_section("Financial Model Summary")

st.write(
    "This dashboard shows the latest baseline outputs from the financial model. "
    "Use the **electricity optimization** page for historical Nordpool scheduling."
)

# Layout
col1, col2, col3 = st.columns(3)

# You can plug your real model outputs here.
# For now, we try to import and compute; if something fails, we show a readable error.
try:
    # Import your own project modules (adjust if your function names differ)
    import config
    from core.model import build_model_outputs  # <-- if your project has a different function name, tell me
    # Example: outputs = build_model_outputs(config.DEFAULT_PARAMS)

    outputs = build_model_outputs()  # simplest call; change if needed

    # Expected outputs structure (example):
    # outputs = {
    #   "total_yearly_sales": 1471500,
    #   "total_capex": 4025000,
    #   "payback_years": 6.2,
    #   "notes": "...",
    # }

    with col1:
        st.metric("Total Yearly Sales (€)", f"{outputs['total_yearly_sales']:,.0f}")

    with col2:
        st.metric("Total CAPEX (€)", f"{outputs['total_capex']:,.0f}")

    with col3:
        if "payback_years" in outputs and outputs["payback_years"] is not None:
            st.metric("Payback (years)", f"{outputs['payback_years']:.1f}")
        else:
            st.metric("Payback (years)", "—")

    vw_section("Notes")
    if "notes" in outputs and outputs["notes"]:
        st.info(outputs["notes"])
    else:
        st.caption("No notes.")

except Exception as e:
    # This keeps the app “alive” even if your model import/function name isn't matching yet.
    st.warning(
        "I couldn’t run the model function from `core/model.py` yet. "
        "This is normal if the function name/signature is different."
    )
    st.caption("Fix: tell me what function you want to call to compute outputs, and what it returns.")
    st.exception(e)


# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("VacuumWood • Vertical Farming Financial Model")