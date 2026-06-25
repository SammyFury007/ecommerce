"""
Admin authentication gate.

Credentials are read from Streamlit secrets (st.secrets), never hardcoded
in source. Locally this comes from .streamlit/secrets.toml (gitignored).
On Streamlit Community Cloud this comes from the app's "Secrets" settings panel.

Expected secrets.toml structure:

    [admin]
    username = "admin"
    password = "your-password-here"

Session state key `authenticated` tracks login status across reruns within
a single browser session. There is no persistent session across browser
restarts/tabs by design — closing the tab requires logging in again, which
is the right behavior for an admin-only internal dashboard.
"""

import streamlit as st


def check_login(username: str, password: str) -> bool:
    """Validate credentials against st.secrets. Returns True if they match."""
    try:
        valid_username = st.secrets["admin"]["username"]
        valid_password = st.secrets["admin"]["password"]
    except (KeyError, FileNotFoundError):
        st.error(
            "Admin credentials are not configured. "
            "Add an [admin] section with username/password to your Streamlit secrets."
        )
        return False

    return username == valid_username and password == valid_password


def login_screen() -> None:
    """Render the login form. Sets st.session_state.authenticated on success."""
    st.markdown(
        """
        <div style="text-align:center; margin-top: 4rem;">
            <h1>QubitEdge Kart</h1>
            <h2>E-Commerce Analytics Dashboard</h2>
            <p style="color:#9CA3AF;">Admin access only. Please sign in to continue.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

            if submitted:
                if check_login(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


def require_login() -> bool:
    """
    Call at the top of the main app. Returns True if the user is authenticated
    (and the rest of the app should render). Returns False if it rendered the
    login screen instead (caller should stop / return).
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        login_screen()
        return False

    return True


def logout_button() -> None:
    """Render a logout button, typically placed in the sidebar."""
    if st.sidebar.button("🚪 Log out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.pop("username", None)
        st.rerun()
