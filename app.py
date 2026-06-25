import streamlit as st

from auth import require_login, logout_button
from data_access import ensure_database_exists, rebuild_database
from views import overview, page_alpha, page_beta, page_gamma, page_delta

st.set_page_config(
    page_title="E-Commerce Customer Behavior Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 1. Login gate — nothing below this renders until authenticated
# ---------------------------------------------------------------------------
if not require_login():
    st.stop()

# ---------------------------------------------------------------------------
# 2. Ensure the SQLite database exists (auto-build on first run / fresh deploy)
# ---------------------------------------------------------------------------
ensure_database_exists()

# ---------------------------------------------------------------------------
# 3. Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("📊 Analytics Dashboard")
st.sidebar.caption(f"Signed in as **{st.session_state.get('username', 'admin')}**")
st.sidebar.divider()

PAGES = {
    "🏠 Overview": "overview",
    "🔤 Module Alpha — Consumer Log Handler": "alpha",
    "🎯 Module Beta — RFM Segmentation": "beta",
    "📦 Module Gamma — Product Analytics": "gamma",
    "🌍 Module Delta — Regional Revenue": "delta",
}

selection = st.sidebar.radio(
    "Navigate to module",
    options=list(PAGES.keys()),
    label_visibility="collapsed",
)

st.sidebar.divider()

with st.sidebar.expander("⚙️ Data management"):
    st.caption("Rebuild the database from the raw Excel file if it changed.")
    if st.button("🔄 Rebuild data", use_container_width=True):
        with st.spinner("Rebuilding database..."):
            stats = rebuild_database()
        st.success(f"Done. {stats['final_rows']:,} clean rows loaded.")
        st.rerun()

logout_button()

# ---------------------------------------------------------------------------
# 4. Dispatch to the selected module page
# ---------------------------------------------------------------------------
route = PAGES[selection]

if route == "overview":
    overview.render()
elif route == "alpha":
    page_alpha.render()
elif route == "beta":
    page_beta.render()
elif route == "gamma":
    page_gamma.render()
elif route == "delta":
    page_delta.render()
