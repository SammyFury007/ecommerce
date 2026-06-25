import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ecommerce.db"
SOURCE_TABLE = "transactions"
TARGET_TABLE = "rfm_segments"


def load_transactions(db_path: Path = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql(f"SELECT * FROM {SOURCE_TABLE}", conn, parse_dates=["InvoiceDate"])
    finally:
        conn.close()
    return df


def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Compute raw Recency, Frequency, Monetary values per customer."""
    snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = (
        df.groupby("CustomerID")
        .agg(
            Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("TotalPrice", "sum"),
        )
        .reset_index()
    )
    rfm["Monetary"] = rfm["Monetary"].round(2)
    return rfm


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """Assign 1-5 quintile scores to R, F, M and derive segment labels."""
    rfm = rfm.copy()

    # Recency: lower days = better, so reverse the labels (5 = most recent)
    rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)

    # Frequency and Monetary: higher = better.
    # rank(method="first") avoids errors when there are many duplicate values
    # at the bin edges (common with Frequency, which has few distinct values).
    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]
    rfm["RFM_Segment_Code"] = (
        rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)
    )

    def label_segment(score: int) -> str:
        if score >= 13:
            return "Champions"
        elif score >= 10:
            return "Loyal Customers"
        elif score >= 8:
            return "Potential Loyalist"
        elif score >= 6:
            return "At Risk"
        else:
            return "Hibernating / Lost"

    rfm["Segment_Label"] = rfm["RFM_Score"].apply(label_segment)

    return rfm


def build_rfm_table(rfm: pd.DataFrame, db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        rfm.to_sql(TARGET_TABLE, conn, if_exists="replace", index=False)
        cur = conn.cursor()
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_rfm_customer ON {TARGET_TABLE}(CustomerID)")
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_rfm_segment ON {TARGET_TABLE}(Segment_Label)")
        conn.commit()
    finally:
        conn.close()


def run_pipeline(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Full Module Beta entry point: read transactions -> compute RFM -> persist."""
    df = load_transactions(db_path)
    rfm = compute_rfm(df)
    rfm_scored = score_rfm(rfm)
    build_rfm_table(rfm_scored, db_path)
    return rfm_scored


if __name__ == "__main__":
    result = run_pipeline()
    print("MODULE BETA — RFM Segmentation Core")
    print("=" * 50)
    print(f"Customers scored: {len(result)}")
    print()
    print("Segment distribution:")
    print(result["Segment_Label"].value_counts())
    print()
    print("Sample output:")
    print(result.head(8).to_string())
