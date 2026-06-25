"""
Data access layer for the Streamlit dashboard.

Wraps Module Alpha/Beta/Gamma/Delta functions with st.cache_data so the
dashboard doesn't re-run SQL/pandas on every widget interaction. Also handles
first-run bootstrapping: if ecommerce.db doesn't exist yet (e.g. fresh clone
on Streamlit Cloud), it builds it from the raw Excel automatically.
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from modules import module_alpha, module_beta, module_gamma, module_delta

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "ecommerce.db"
RAW_DATA_PATH = BASE_DIR / "data" / "Online_Retail.xlsx"


def ensure_database_exists() -> None:
    """Build the SQLite database from raw data if it doesn't exist yet."""
    if not DB_PATH.exists():
        if not RAW_DATA_PATH.exists():
            st.error(
                f"Raw dataset not found at {RAW_DATA_PATH}. "
                "Make sure Online_Retail.xlsx is committed to the repo's data/ folder."
            )
            st.stop()
        with st.spinner("First-time setup: building database from raw data..."):
            module_alpha.run_pipeline()
            module_beta.run_pipeline()


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ---------------------------------------------------------------------------
# Cached data loaders — one per logical dataset the dashboard needs.
# TTL-free cache (data is static for the session); clear via "Rebuild Data"
# button if the underlying Excel file changes.
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_transactions() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM transactions", conn, parse_dates=["InvoiceDate"])
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_rfm() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM rfm_segments", conn)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_top_products_revenue(n: int = 10) -> pd.DataFrame:
    conn = get_connection()
    df = module_gamma.top_products_by_revenue(conn, n)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_top_products_quantity(n: int = 10) -> pd.DataFrame:
    conn = get_connection()
    df = module_gamma.top_products_by_quantity(conn, n)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_product_summary() -> pd.DataFrame:
    conn = get_connection()
    df = module_gamma.product_summary(conn)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_revenue_timeline(freq: str = "D") -> pd.DataFrame:
    conn = get_connection()
    df = module_gamma.revenue_timeline(conn, freq)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_product_detail(stock_code: str) -> pd.DataFrame:
    conn = get_connection()
    df = module_gamma.product_detail(conn, stock_code)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_revenue_by_country() -> pd.DataFrame:
    conn = get_connection()
    df = module_delta.revenue_by_country(conn)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_country_monthly_trend(country: str) -> pd.DataFrame:
    conn = get_connection()
    df = module_delta.country_monthly_trend(conn, country)
    conn.close()
    return df


@st.cache_data(show_spinner=False)
def load_country_customer_counts() -> pd.DataFrame:
    conn = get_connection()
    df = module_delta.country_customer_counts(conn)
    conn.close()
    return df


def rebuild_database() -> dict:
    """Force-rebuild the DB from raw Excel and clear all caches. Returns Alpha's audit stats."""
    audit_stats = module_alpha.run_pipeline()
    module_beta.run_pipeline()
    st.cache_data.clear()
    return audit_stats
