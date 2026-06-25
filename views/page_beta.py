import streamlit as st
import plotly.express as px

from data_access import load_rfm

SEGMENT_COLORS = {
    "Champions": "#22C55E",
    "Loyal Customers": "#3B82F6",
    "Potential Loyalist": "#A78BFA",
    "At Risk": "#F59E0B",
    "Hibernating / Lost": "#EF4444",
}


def render() -> None:
    st.title("🎯 Module Beta — RFM Segmentation Core")
    st.caption("Measures customer value boundaries using Recency, Frequency, and Monetary metrics.")

    rfm = load_rfm()

    # ---- Segment KPI strip --------------------------------------------------
    seg_counts = rfm["Segment_Label"].value_counts()
    cols = st.columns(len(SEGMENT_COLORS))
    for col, (segment, color) in zip(cols, SEGMENT_COLORS.items()):
        count = seg_counts.get(segment, 0)
        pct = 100 * count / len(rfm)
        col.markdown(
            f"""
            <div style="border-left: 4px solid {color}; padding-left: 10px;">
                <div style="font-size: 0.8rem; color: #9CA3AF;">{segment}</div>
                <div style="font-size: 1.4rem; font-weight: 700;">{count}</div>
                <div style="font-size: 0.75rem; color: #9CA3AF;">{pct:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
    )
    fig.update_layout(height=500, legend_title_text="Segment")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---- Segment breakdown table + filter ----------------------------------
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Segment Averages")
        avg_table = (
            rfm.groupby("Segment_Label")[["Recency", "Frequency", "Monetary"]]
            .mean()
            .round(1)
            .reindex(SEGMENT_COLORS.keys())
        )
        st.dataframe(avg_table, use_container_width=True)

    with col_right:
        st.subheader("Explore Customers by Segment")
        chosen_segment = st.selectbox("Select a segment", options=list(SEGMENT_COLORS.keys()))
        segment_df = rfm[rfm["Segment_Label"] == chosen_segment].sort_values(
            "Monetary", ascending=False
        )
        st.caption(f"{len(segment_df):,} customers in **{chosen_segment}**")
        st.dataframe(
            segment_df[["CustomerID", "Recency", "Frequency", "Monetary", "RFM_Score", "RFM_Segment_Code"]],
            use_container_width=True,
            height=300,
        )

    with st.expander("ℹ️ How segments are defined"):
        st.markdown(
            """
            Each customer is scored 1–5 on **Recency**, **Frequency**, and **Monetary**
            value using quintiles (5 = best). The three scores are summed into an
            **RFM Score** (range 3–15), which maps to a business segment:

            - **Champions** (score ≥ 13): Bought recently, buy often, spend the most.
            - **Loyal Customers** (10–12): Consistent buyers, strong value.
            - **Potential Loyalist** (8–9): Recent customers with average frequency/spend.
            - **At Risk** (6–7): Below-average recency — haven't purchased in a while.
            - **Hibernating / Lost** (< 6): Long inactive, low value — re-engagement candidates.
            """
        )
