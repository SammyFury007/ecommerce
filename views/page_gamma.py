"""
Module Gamma Page — Product Purchase Analytics Module
Addresses Objective 3 (top products), Visualization View 2 (Purchase
Ingestion Timeline), and Visualization View 3 (Catalog Revenue Matrix).
"""

import streamlit as st
import plotly.express as px

from data_access import (
    load_top_products_revenue,
    load_top_products_quantity,
    load_product_summary,
    load_revenue_timeline,
    load_product_detail,
)


def render() -> None:
    st.title("📦 Module Gamma — Product Purchase Analytics")
    st.caption("Tally order totals across the catalog to trace product performance trends.")

    # ---- Visualization View 2: Purchase Ingestion Timeline -----------------
    st.subheader("Purchase Ingestion Timeline")
    freq_label = st.radio("Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True, index=2)
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
    timeline = load_revenue_timeline(freq_map[freq_label])

    fig = px.area(
        timeline,
        x="InvoiceDate",
        y="Revenue",
        labels={"InvoiceDate": "Date", "Revenue": "Revenue (£)"},
    )
    fig.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---- Top products: revenue vs quantity ----------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Products by Revenue")
        top_rev = load_top_products_revenue(10)
        fig2 = px.bar(
            top_rev,
            x="TotalRevenue",
            y="Description",
            orientation="h",
            text="TotalRevenue",
        )
        fig2.update_traces(texttemplate="£%{x:,.0f}", textposition="outside")
        fig2.update_layout(
            height=420, margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(autorange="reversed", title="")
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("Top 10 Products by Units Sold")
        top_qty = load_top_products_quantity(10)
        fig3 = px.bar(
            top_qty,
            x="TotalUnitsSold",
            y="Description",
            orientation="h",
            text="TotalUnitsSold",
            color_discrete_sequence=["#A78BFA"],
        )
        fig3.update_traces(texttemplate="%{x:,.0f}", textposition="outside")
        fig3.update_layout(
            height=420, margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(autorange="reversed", title="")
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # ---- Visualization View 3: Catalog Revenue Matrix -----------------------
    st.subheader("Catalog Revenue Matrix")
    st.caption("Full inventory ranked by total contribution margin (revenue)")

    summary = load_product_summary()
    search = st.text_input("Search product catalog", placeholder="e.g. LANTERN, MUG, HEART...")
    if search:
        summary_view = summary[summary["Description"].str.contains(search.upper(), na=False)]
    else:
        summary_view = summary

    st.caption(f"{len(summary_view):,} products")
    st.dataframe(summary_view, use_container_width=True, height=350)

    st.divider()

    # ---- Product drill-down ------------------------------------------------
    st.subheader("Product Drill-Down")
    product_options = summary.set_index("StockCode")["Description"].to_dict()
    chosen_code = st.selectbox(
        "Select a product (by code)",
        options=list(product_options.keys()),
        format_func=lambda code: f"{code} — {product_options[code]}",
    )
    detail = load_product_detail(chosen_code)
    if not detail.empty:
        fig4 = px.bar(detail, x="Month", y="Revenue", text="Revenue")
        fig4.update_traces(texttemplate="£%{y:,.0f}", textposition="outside")
        fig4.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No monthly data available for this product.")
