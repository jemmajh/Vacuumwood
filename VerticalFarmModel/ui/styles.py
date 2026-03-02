# ui/styles.py
import streamlit as st

def apply_branding():
    css = """
    <style>
      .vw-logo {font-weight:700; font-size:42px; line-height:1.1; letter-spacing:4px;}
      .vw-black {color:#000000;}
      .vw-green {color:#3CB371;}
      .vw-container {text-align:center; margin-top:10px; margin-bottom:4px;}
    </style>
    """

    logo = """
    <div class="vw-container">
      <div class="vw-logo">
        <span class="vw-black">VACUUM</span><br>
        <span class="vw-black">WOOD.</span><br>
        <span class="vw-green">TECH</span>
      </div>
    </div>
    """

    st.markdown(css + logo, unsafe_allow_html=True)


def vw_section(title: str):
    st.markdown(
        f"""
        <div style='font-size:18px; font-weight:700; color:#000; margin-top:22px; margin-bottom:8px;'>
            • {title}
        </div>
        """,
        unsafe_allow_html=True
    )