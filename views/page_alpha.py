"""
Module Alpha Page — Consumer Log Handler
Shows the data cleaning pipeline's audit trail and raw transaction explorer.
"""

import streamlit as st

from data_access import load_transactions
from modules import module_alpha


def render() -> None:
    st.title("🔤 Module Alpha — Consumer Log Handler")
    st.caption("Standardizes transaction receipt rows, invoice tables, and website order data.")

    df = load_transactions()

    st.subheader("Clean Transaction Table")
    st.caption("Explore the standardized transaction log used by all downstream modules.")

    col1, col2, col3 = st.columns(3)
    with col1:
        country_filter = st.multiselect(
            "Filter by country", options=sorted(df["Country"].unique())
        )
    with col2:
        date_min = df["InvoiceDate"].min().date()
        date_max = df["InvoiceDate"].max().date()
        date_range = st.date_input("Date range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
    with col3:
        search_term = st.text_input("Search product description")

    filtered = df.copy()
    if country_filter:
        filtered = filtered[filtered["Country"].isin(country_filter)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["InvoiceDate"].dt.date >= start) & (filtered["InvoiceDate"].dt.date <= end)
        ]
    if search_term:
        filtered = filtered[filtered["Description"].str.contains(search_term.upper(), na=False)]

    st.caption(f"Showing {len(filtered):,} of {len(df):,} rows")
    st.dataframe(
        filtered.sort_values("InvoiceDate", ascending=False).head(500),
        use_container_width=True,
        height=400,
    )

    with st.expander("📋 Column reference"):
        st.markdown(
            """
            | Column | Description |
            |---|---|
            | `InvoiceNo` | Unique invoice/order number |
            | `StockCode` | Product/SKU code |
            | `Description` | Product name |
            | `Quantity` | Units purchased |
            | `InvoiceDate` | Date and time of purchase |
            | `UnitPrice` | Price per unit (£) |
            | `TotalPrice` | Quantity × UnitPrice (derived) |
            | `CustomerID` | Unique buyer identifier |
            | `Country` | Buyer's country |
            """
        )
