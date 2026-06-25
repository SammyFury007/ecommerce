"""
Overview Page — high-level KPI summary across all four modules.
Addresses Objective 1: a behavioral customer dashboard tracking
historical buyer transaction histories at a glance.
"""

import streamlit as st
import plotly.express as px

from data_access import (
    load_transactions,
    load_rfm,
    load_revenue_timeline,
    load_revenue_by_country,
)


def render() -> None:
    st.title("🏠 Overview")
    st.caption("E-Commerce Customer Behavior Analysis — UCI Online Retail Dataset")

    df = load_transactions()
    rfm = load_rfm()
    country_rev = load_revenue_by_country()

    # ---- Top KPI row ----------------------------------------------------
    total_revenue = df["TotalPrice"].sum()
    total_orders = df["InvoiceNo"].nunique()
    total_customers = df["CustomerID"].nunique()
    avg_order_value = total_revenue / total_orders

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"£{total_revenue:,.0f}")
    c2.metric("Total Orders", f"{total_orders:,}")
    c3.metric("Unique Customers", f"{total_customers:,}")
    c4.metric("Avg Order Value", f"£{avg_order_value:,.2f}")

    st.divider()

    # ---- Revenue timeline -------------------------------------------------
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Revenue Trend (Monthly)")
        timeline = load_revenue_timeline("M")
        fig = px.line(
            timeline,
            x="InvoiceDate",
            y="Revenue",
            markers=True,
            labels={"InvoiceDate": "Month", "Revenue": "Revenue (£)"},
        )
        fig.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Customer Segments")
        seg_counts = rfm["Segment_Label"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Customers"]
        fig2 = px.pie(seg_counts, names="Segment", values="Customers", hole=0.4)
        fig2.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        fig2.update_traces(textinfo="label+percent")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ---- Top countries snapshot --------------------------------------------
    st.subheader("Top 5 Markets by Revenue")
    top5 = country_rev.head(5)
    fig3 = px.bar(
        top5,
        x="TotalRevenue",
        y="Country",
        orientation="h",
        text="TotalRevenue",
        labels={"TotalRevenue": "Revenue (£)"},

    st.divider()

    # ---- Visualization View 1: Customer Segment Scatter Diagram -----------
    st.subheader("Customer Segment Scatter Diagram")
    st.caption("Recency vs. Monetary value, sized by Frequency, colored by segment")

    fig = px.scatter(
        rfm,
        x="Recency",
        y="Monetary",
        color="Segment_Label",
        size="Frequency",
        size_max=30,
        color_discrete_map=SEGMENT_COLORS,
        hover_data={"CustomerID": True, "Frequency": True, "RFM_Score": True},
        labels={"Recency": "Recency (days since last purchase)", "Monetary": "Monetary value (£)"},
        log_y=True,

    st.divider()
    
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
    )
    fig3.update_traces(texttemplate="£%{x:,.0f}", textposition="outside")
    fig3.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig3, use_container_width=True)

    st.info(
        "Use the sidebar to dive into each module: **Alpha** (data quality), "
        "**Beta** (RFM segmentation), **Gamma** (product analytics), and "
        "**Delta** (regional revenue).",
    )
