import sqlite3
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "Online_Retail.xlsx"
DB_PATH = BASE_DIR / "data" / "ecommerce.db"
TABLE_NAME = "transactions"


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw Online Retail Excel file into a DataFrame."""
    df = pd.read_excel(path)
    return df


def clean_transactions(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    stats = {"raw_rows": len(df)}

    # 1. Standardize column dtypes / strip whitespace on text columns
    df = df.copy()
    for col in ["InvoiceNo", "StockCode", "Description", "Country"]:
        df[col] = df[col].astype("string").str.strip()

    # 2. Drop rows with missing CustomerID — can't segment a buyer we can't identify
    df = df.dropna(subset=["CustomerID"])
    stats["after_drop_missing_customer"] = len(df)

    # 3. Drop rows with missing/blank Description
    df = df.dropna(subset=["Description"])
    df = df[df["Description"].str.len() > 0]
    stats["after_drop_missing_description"] = len(df)

    # 4. Remove cancelled invoices (InvoiceNo beginning with 'C')
    df = df[~df["InvoiceNo"].str.startswith("C", na=False)]
    stats["after_drop_cancellations"] = len(df)

    # 5. Remove non-positive Quantity or UnitPrice (returns, free items, bad data)
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    stats["after_drop_nonpositive"] = len(df)

    # 6. Standardize casing
    df["Description"] = df["Description"].str.upper()
    df["Country"] = df["Country"].str.title()

    # 7. CustomerID as clean integer (was float because of NaNs originally)
    df["CustomerID"] = df["CustomerID"].astype("int64")

    # 8. Drop exact duplicate rows
    df = df.drop_duplicates()
    stats["after_drop_duplicates"] = len(df)

    # 9. Derive TotalPrice for monetary calculations downstream
    df["TotalPrice"] = (df["Quantity"] * df["UnitPrice"]).round(2)

    # 10. Ensure InvoiceDate is proper datetime
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # Final column order
    df = df[
        [
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "TotalPrice",
            "CustomerID",
            "Country",
        ]
    ].reset_index(drop=True)

    stats["final_rows"] = len(df)
    stats["rows_removed"] = stats["raw_rows"] - stats["final_rows"]
    stats["pct_removed"] = round(100 * stats["rows_removed"] / stats["raw_rows"], 2)

    return df, stats


def build_database(df: pd.DataFrame, db_path: Path = DB_PATH) -> None:
    """Persist the cleaned transactions DataFrame into a SQLite database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

        # Helpful indexes for the query patterns used by Beta/Gamma/Delta
        cur = conn.cursor()
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_customer ON {TABLE_NAME}(CustomerID)")
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_country ON {TABLE_NAME}(Country)")
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_stockcode ON {TABLE_NAME}(StockCode)")
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_invoicedate ON {TABLE_NAME}(InvoiceDate)")
        conn.commit()
    finally:
        conn.close()


def run_pipeline(raw_path: Path = RAW_DATA_PATH, db_path: Path = DB_PATH) -> dict:
    """Full Module Alpha entry point: load -> clean -> persist. Returns audit stats."""
    raw_df = load_raw_data(raw_path)
    clean_df, stats = clean_transactions(raw_df)
    build_database(clean_df, db_path)
    return stats


if __name__ == "__main__":
    audit = run_pipeline()
    print("MODULE ALPHA — Consumer Log Handler")
    print("=" * 50)
    for key, value in audit.items():
        print(f"{key:32s}: {value}")
    print("=" * 50)
    print(f"Database written to: {DB_PATH}")
