import sqlite3
import pandas as pd

SOURCE_TABLE = "transactions"


def revenue_by_country(conn: sqlite3.Connection) -> pd.DataFrame:
    """Full country-level rollup — revenue, orders, customers, units."""
    query = f"""
        SELECT
            Country,
            ROUND(SUM(TotalPrice), 2) AS TotalRevenue,
            COUNT(DISTINCT InvoiceNo) AS OrderCount,
            COUNT(DISTINCT CustomerID) AS UniqueCustomers,
            SUM(Quantity) AS TotalUnitsSold,
            ROUND(SUM(TotalPrice) * 1.0 / COUNT(DISTINCT InvoiceNo), 2) AS AvgOrderValue
        FROM {SOURCE_TABLE}
        GROUP BY Country
        ORDER BY TotalRevenue DESC
    """
    return pd.read_sql(query, conn)


def top_countries(conn: sqlite3.Connection, n: int = 10) -> pd.DataFrame:
    return revenue_by_country(conn).head(n)


def country_monthly_trend(conn: sqlite3.Connection, country: str) -> pd.DataFrame:
    """Monthly revenue trend for a single country."""
    query = f"""
        SELECT
            strftime('%Y-%m', InvoiceDate) AS Month,
            ROUND(SUM(TotalPrice), 2) AS Revenue,
            COUNT(DISTINCT InvoiceNo) AS Orders
        FROM {SOURCE_TABLE}
        WHERE Country = ?
        GROUP BY Month
        ORDER BY Month
    """
    return pd.read_sql(query, conn, params=(country,))


def country_customer_counts(conn: sqlite3.Connection) -> pd.DataFrame:
    """Unique customers per country, sorted descending — for map/bar charts."""
    query = f"""
        SELECT
            Country,
            COUNT(DISTINCT CustomerID) AS UniqueCustomers
        FROM {SOURCE_TABLE}
        GROUP BY Country
        ORDER BY UniqueCustomers DESC
    """
    return pd.read_sql(query, conn)


if __name__ == "__main__":
    from pathlib import Path

    db_path = Path(__file__).resolve().parent.parent / "data" / "ecommerce.db"
    conn = sqlite3.connect(db_path)

    print("MODULE DELTA — Regional Revenue Mapping")
    print("=" * 50)
    print("\nTop 10 countries by revenue:")
    print(top_countries(conn, 10).to_string())

    print("\nUK monthly trend (sample):")
    print(country_monthly_trend(conn, "United Kingdom").to_string())

    conn.close()
