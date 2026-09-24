import streamlit as st

def apply_custom_css():
    """Inject premium, handcrafted glassmorphism CSS theme."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Radial Deep Purple Space Canvas */
    .stApp {
        background: radial-gradient(circle at 50% -10%, #201335 0%, #0d0818 55%, #05030a 100%);
        color: #f8fafc;
    }

    /* Hide default Streamlit elements */
    header[data-testid="stHeader"], footer, #MainMenu {
        visibility: hidden;
        display: none;
    }

    /* Center Container Bounds */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 760px !important;
    }

    /* Header Styling */
    .header-container {
        text-align: center;
        margin-bottom: 1.8rem;
    }

    .brand-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 40%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.1;
    }

    .badge-pill {
        display: inline-block;
        background: rgba(168, 85, 247, 0.12);
        color: #d8b4fe;
        border: 1px solid rgba(168, 85, 247, 0.28);
        border-radius: 20px;
        padding: 0.35rem 0.95rem;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }

    .app-desc {
        color: #a1a1aa;
        font-size: 0.94rem;
        font-weight: 500;
        text-align: center;
        margin: 0.8rem auto 0 auto;
        line-height: 1.5;
        letter-spacing: -0.01em;
        width: 100%;
    }

    /* Custom Input Fields */
    .stTextInput > div > div > input {
        background: rgba(12, 9, 22, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #f8fafc !important;
        border-radius: 14px !important;
        padding: 0.8rem 1.1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.5) !important;
    }

    .stTextInput > div > div > input:hover {
        border-color: rgba(192, 132, 252, 0.4) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 22px rgba(168, 85, 247, 0.35), inset 0 2px 5px rgba(0,0,0,0.5) !important;
    }

    /* Premium Electric Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #ec4899 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.75rem 1.3rem !important;
        font-weight: 700 !important;
        font-size: 0.94rem !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.35) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer;
    }

    .stButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 12px 35px rgba(168, 85, 247, 0.55) !important;
        filter: brightness(1.1);
    }

    .stButton > button:active {
        transform: translateY(0px) scale(0.99);
    }

    /* Selectboxes */
    .stSelectbox > div > div {
        background: rgba(12, 9, 22, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #f8fafc !important;
        border-radius: 14px !important;
        transition: all 0.25s ease !important;
    }

    .stSelectbox > div > div:hover {
        border-color: #a855f7 !important;
        box-shadow: 0 0 16px rgba(168, 85, 247, 0.25) !important;
    }

    /* Thumbnail Hover Zoom */
    img {
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 14px 35px rgba(0, 0, 0, 0.6) !important;
        transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.4s ease !important;
    }

    img:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 20px 45px rgba(168, 85, 247, 0.3) !important;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        color: #94a3b8 !important;
    }

    /* Subtle Glass Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.08) !important;
        margin: 1.8rem 0 !important;
    }

    /* Custom Info Cards */
    .info-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.6rem;
        transition: all 0.25s ease;
    }
    .info-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(168, 85, 247, 0.35);
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
