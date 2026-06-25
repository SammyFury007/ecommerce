"""
MODULE GAMMA — Product Purchase Analytics Module
===================================================
Tally order totals across the catalog to trace product performance trends.

This module is intentionally lightweight: it does not write a new table to the
database. Instead it exposes a set of parameterized SQL query functions that
the dashboard calls directly against the `transactions` table built by
Module Alpha. Product analytics are naturally "ad hoc" (top-N, date-filtered,
country-filtered), so computing them on demand via SQL is more flexible than
pre-materializing a fixed table.

Functions:
  - top_products_by_revenue(conn, n)
  - top_products_by_quantity(conn, n)
  - product_summary(conn)                 -> full catalog-level aggregation
  - revenue_timeline(conn, freq)           -> revenue over time (for trend charts)
  - product_detail(conn, stock_code)       -> drill-down for a single SKU
"""

import sqlite3
import pandas as pd

SOURCE_TABLE = "transactions"


def top_products_by_revenue(conn: sqlite3.Connection, n: int = 10) -> pd.DataFrame:
    query = f"""
        SELECT
            StockCode,
            Description,
            SUM(TotalPrice) AS TotalRevenue,
            SUM(Quantity) AS TotalUnitsSold,
            COUNT(DISTINCT InvoiceNo) AS OrderCount
        FROM {SOURCE_TABLE}
        GROUP BY StockCode, Description
        ORDER BY TotalRevenue DESC
        LIMIT ?
    """
    return pd.read_sql(query, conn, params=(n,))


def top_products_by_quantity(conn: sqlite3.Connection, n: int = 10) -> pd.DataFrame:
    query = f"""
        SELECT
            StockCode,
            Description,
            SUM(Quantity) AS TotalUnitsSold,
            SUM(TotalPrice) AS TotalRevenue,
            COUNT(DISTINCT InvoiceNo) AS OrderCount
        FROM {SOURCE_TABLE}
        GROUP BY StockCode, Description
        ORDER BY TotalUnitsSold DESC
        LIMIT ?
    """
    return pd.read_sql(query, conn, params=(n,))


def product_summary(conn: sqlite3.Connection) -> pd.DataFrame:
    """Full catalog aggregated by product — used for the Catalog Revenue Matrix."""
    query = f"""
        SELECT
            StockCode,
            Description,
            SUM(Quantity) AS TotalUnitsSold,
            ROUND(SUM(TotalPrice), 2) AS TotalRevenue,
            COUNT(DISTINCT InvoiceNo) AS OrderCount,
            COUNT(DISTINCT CustomerID) AS UniqueCustomers,
            ROUND(AVG(UnitPrice), 2) AS AvgUnitPrice
        FROM {SOURCE_TABLE}
        GROUP BY StockCode, Description
        ORDER BY TotalRevenue DESC
    """
    return pd.read_sql(query, conn)


def revenue_timeline(conn: sqlite3.Connection, freq: str = "D") -> pd.DataFrame:
    """
    Revenue and order volume over time, used for the Purchase Ingestion Timeline.
    freq: 'D' (daily), 'W' (weekly), or 'M' (monthly) — resampled in pandas
    since SQLite has no native date-bucketing for arbitrary frequencies.

    Accepts the user-facing aliases D/W/M and maps them to whichever resample
    alias the installed pandas version expects (pandas >= 2.2 renamed the
    month-end alias from 'M' to 'ME').
    """
    freq_map = {"D": "D", "W": "W", "M": "ME"}
    resample_freq = freq_map.get(freq, freq)

    query = f"SELECT InvoiceDate, TotalPrice, InvoiceNo FROM {SOURCE_TABLE}"
    df = pd.read_sql(query, conn, parse_dates=["InvoiceDate"])
    df = df.set_index("InvoiceDate")

    try:
        resampler = df.resample(resample_freq)
    except ValueError:
        # Fallback for older pandas versions that still expect 'M'
        fallback = {"ME": "M", "W": "W", "D": "D"}.get(resample_freq, resample_freq)
        resampler = df.resample(fallback)

    timeline = (
        resampler.agg(Revenue=("TotalPrice", "sum"), Orders=("InvoiceNo", "nunique"))
        .reset_index()
    )
    timeline["Revenue"] = timeline["Revenue"].round(2)
    return timeline


def product_detail(conn: sqlite3.Connection, stock_code: str) -> pd.DataFrame:
    """Drill-down detail for a single product, including monthly trend."""
    query = f"""
        SELECT
            strftime('%Y-%m', InvoiceDate) AS Month,
            SUM(Quantity) AS UnitsSold,
            ROUND(SUM(TotalPrice), 2) AS Revenue
        FROM {SOURCE_TABLE}
        WHERE StockCode = ?
        GROUP BY Month
        ORDER BY Month
    """
    return pd.read_sql(query, conn, params=(stock_code,))


if __name__ == "__main__":
    from pathlib import Path

    db_path = Path(__file__).resolve().parent.parent / "data" / "ecommerce.db"
    conn = sqlite3.connect(db_path)

    print("MODULE GAMMA — Product Purchase Analytics")
    print("=" * 50)
    print("\nTop 5 products by revenue:")
    print(top_products_by_revenue(conn, 5).to_string())

    print("\nTop 5 products by quantity sold:")
    print(top_products_by_quantity(conn, 5).to_string())

    print("\nMonthly revenue timeline:")
    print(revenue_timeline(conn, "M").to_string())

    conn.close()
