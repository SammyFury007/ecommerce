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
