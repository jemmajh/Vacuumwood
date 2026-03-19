# VerticalFarmModel/ui/styles.py
import streamlit as st


def apply_branding():
    """
    Branding ONLY: no app logic, no model imports, no circular imports.
    Keeps your font size unchanged.
    Fixes logo clipping by adding top padding and safe header spacing.
    """
    st.markdown(
        """
        <style>
          /* Give breathing room so the logo never clips */
          .block-container {
            padding-top: 2.6rem !important;
            padding-bottom: 2.0rem !important;
          }

          /* Centered logo container */
          .vw-container {
            text-align: center;
            padding-top: 0.8rem;
            padding-bottom: 0.3rem;
          }

          /* Keep font size as-is (you said don't change it) */
          .vw-logo { font-weight: 700; font-size: 42px; line-height: 1.1; letter-spacing: 4px; }
          .vw-black { color: #000000; }
          .vw-green { color: #3CB371; }

          /* Make tabs/sections feel more "report-like" */
          div[data-testid="stTabs"] button {
            font-weight: 600;
          }
        </style>

        <div class="vw-container" aria-label="VacuumWood logo">
          <div class="vw-logo">
            <span class="vw-black">VACUUM</span><br>
            <span class="vw-black">WOOD.</span><br>
            <span class="vw-green">TECH</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def vw_section(title: str):
    st.markdown(
        f"""
        <div style="
            font-size:18px;
            font-weight:700;
            color:#000;
            margin-top:22px;
            margin-bottom:8px;
        ">
          • {title}
        </div>
        """,
        unsafe_allow_html=True,
    )