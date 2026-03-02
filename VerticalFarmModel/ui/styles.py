# ui/styles.py
import streamlit as st

def apply_branding():
    st.set_page_config(page_title="Vacuumwood Financial Model", layout="wide")

    st.markdown(
        """
        <style>
            .vw-logo { font-weight:700; font-size:42px; line-height:1.1; letter-spacing:4px; }
            .vw-black { color:#000000; }
            .vw-green { color:#3CB371; }
            .vw-container { text-align:center; margin-top:10px; margin-bottom:4px; }

            .stButton > button { background-color:#3CB371; color:white; border-radius:6px; border:none; padding:0.4rem 1rem; font-weight:600; }
            .stButton > button:hover { background-color:#34a165; }

            [data-testid="stSidebar"] { background-color:#F4F4F4 !important; }
            [data-testid="stSidebar"] * { color:#000 !important; }
            [data-testid="stSidebar"] h2 { color:#3CB371 !important; }

            thead tr th { background-color:#0E1A25 !important; color:#fff !important; font-weight:600; }
            tbody tr:nth-child(even) { background-color:#F5F7FA !important; }
            tbody tr:nth-child(odd) { background-color:#FFFFFF !important; }
            tbody tr:hover { background-color:#E3F3EB !important; }
        </style>
        <div class="vw-container">
            <div class="vw-logo">
                <span class="vw-black">V A C U U M</span><br>
                <span class="vw-black">W O O D.</span><br>
                <span class="vw-green">T E C H</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def vw_section(title: str):
    st.markdown(
        f"""
        <div style='font-size:18px; font-weight:700; color:#000; margin-top:22px; margin-bottom:8px;'>
            • {title}
        </div>
        """,
        unsafe_allow_html=True
    )