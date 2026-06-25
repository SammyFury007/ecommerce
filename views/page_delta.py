"""
Module Delta Page — Regional Revenue Mapping Subsystem
Addresses Objective 4 (geographic growth / retention insight) via
country-level revenue rollups and trend drill-downs.
"""

import streamlit as st
import plotly.express as px

from data_access import (
    load_revenue_by_country,
    load_country_monthly_trend,
    load_country_customer_counts,
)

# ISO-3 mapping for the choropleth map (covers the countries present in this dataset)
COUNTRY_ISO3 = {
    "United Kingdom": "GBR", "Germany": "DEU", "France": "FRA", "Eire": "IRL",
    "Spain": "ESP", "Netherlands": "NLD", "Belgium": "BEL", "Switzerland": "CHE",
    "Portugal": "PRT", "Australia": "AUS", "Norway": "NOR", "Italy": "ITA",
    "Channel Islands": "GGY", "Finland": "FIN", "Cyprus": "CYP", "Sweden": "SWE",
    "Austria": "AUT", "Denmark": "DNK", "Japan": "JPN", "Poland": "POL",
    "Israel": "ISR", "Usa": "USA", "Hong Kong": "HKG", "Singapore": "SGP",
    "Iceland": "ISL", "Canada": "CAN", "Greece": "GRC", "Malta": "MLT",
    "United Arab Emirates": "ARE", "European Community": None, "Rsa": "ZAF",
    "Lebanon": "LBN", "Lithuania": "LTU", "Brazil": "BRA", "Czech Republic": "CZE",
    "Bahrain": "BHR", "Saudi Arabia": "SAU", "Unspecified": None,
}


def render() -> None:
    st.title("🌍 Module Delta — Regional Revenue Mapping")
    st.caption("Tracks customer orders by country to monitor geographic growth.")

    country_rev = load_revenue_by_country()
    customer_counts = load_country_customer_counts()

    # ---- World map choropleth ----------------------------------------------
    st.subheader("Global Revenue Distribution")
    map_df = country_rev.copy()
    map_df["iso3"] = map_df["Country"].map(COUNTRY_ISO3)
    map_df = map_df.dropna(subset=["iso3"])

    fig_map = px.choropleth(
        map_df,
        locations="iso3",
        color="TotalRevenue",
        hover_name="Country",
        hover_data={"iso3": False, "OrderCount": True, "UniqueCustomers": True},
        color_continuous_scale="Blues",
        labels={"TotalRevenue": "Revenue (£)"},
    )
    fig_map.update_layout(height=420, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig_map, use_container_width=True)

    st.caption(
        "Note: the UK dominates this dataset by volume — toggle 'Exclude UK' below "
        "to see relative performance across other markets."
    )

    st.divider()

    # ---- Top markets bar chart (with UK toggle) -----------------------------
    exclude_uk = st.checkbox("Exclude United Kingdom (to see other markets clearly)")
    chart_df = country_rev[country_rev["Country"] != "United Kingdom"] if exclude_uk else country_rev

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Revenue by Country")
        top_n = chart_df.head(15)
        fig = px.bar(top_n, x="TotalRevenue", y="Country", orientation="h", text="TotalRevenue")
        fig.update_traces(texttemplate="£%{x:,.0f}", textposition="outside")
        fig.update_layout(height=450, margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(autorange="reversed", title=""))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Unique Customers by Country")
        cc = customer_counts[customer_counts["Country"] != "United Kingdom"] if exclude_uk else customer_counts
        cc_top = cc.head(15)
        fig2 = px.bar(
            cc_top, x="UniqueCustomers", y="Country", orientation="h", text="UniqueCustomers",
            color_discrete_sequence=["#22C55E"],
        )
        fig2.update_traces(texttemplate="%{x}", textposition="outside")
        fig2.update_layout(height=450, margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(autorange="reversed", title=""))
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ---- Country drill-down -------------------------------------------------
    st.subheader("Country Drill-Down")
    chosen_country = st.selectbox("Select a country", options=country_rev["Country"].tolist())
    trend = load_country_monthly_trend(chosen_country)

    if not trend.empty:
        fig3 = px.line(trend, x="Month", y="Revenue", markers=True, labels={"Revenue": "Revenue (£)"})
        fig3.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)

        row = country_rev[country_rev["Country"] == chosen_country].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"£{row['TotalRevenue']:,.0f}")
        c2.metric("Orders", f"{row['OrderCount']:,}")
        c3.metric("Unique Customers", f"{row['UniqueCustomers']:,}")
        c4.metric("Avg Order Value", f"£{row['AvgOrderValue']:,.2f}")
    else:
        st.info("No monthly data available for this country.")

    st.divider()
    st.subheader("Full Country Breakdown")
    st.dataframe(country_rev, use_container_width=True, height=300)
