import streamlit as st


def check_login(username: str, password: str) -> bool:
    
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
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        login_screen()
        return False

    return True


def logout_button() -> None:
    
    if st.sidebar.button("🚪 Log out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.pop("username", None)
        st.rerun()
