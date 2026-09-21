import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sports_booking.db"


def get_customer_segments():
    """
    Return customers grouped by their booking behavior.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            customer_id,
            name,
            email,
            customer_type,
            booking_frequency,
            last_booking_date
        FROM customers
        ORDER BY booking_frequency DESC
    """

    customers = pd.read_sql_query(query, connection)

    connection.close()

    return customers


def get_target_customers(slot, limit=5):
    """
    Find customers who are most likely to book
    the selected sport and time slot.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            c.customer_id,
            c.name,
            c.email,
            c.customer_type,
            c.booking_frequency,
            c.last_booking_date,

            COUNT(
                CASE
                    WHEN court.sport = ?
                    THEN b.booking_id
                END
            ) AS sport_bookings,

            COUNT(
                CASE
                    WHEN court.sport = ?
                    AND s.start_time = ?
                    THEN b.booking_id
                END
            ) AS similar_slot_bookings

        FROM customers c

        LEFT JOIN bookings b
            ON c.customer_id = b.customer_id

        LEFT JOIN slots s
            ON b.slot_id = s.slot_id

        LEFT JOIN courts court
            ON s.court_id = court.court_id

        GROUP BY
            c.customer_id,
            c.name,
            c.email,
            c.customer_type,
            c.booking_frequency,
            c.last_booking_date
    """

    customers = pd.read_sql_query(
        query,
        connection,
        params=(
            slot["sport"],
            slot["sport"],
            slot["start_time"]
        )
    )

    connection.close()

    if customers.empty:
        return customers

    # Start with zero targeting score
    customers["score"] = 0

    # Previous bookings for the same sport
    customers["score"] += (
        customers["sport_bookings"] * 10
    )

    # Previous bookings at the same time
    customers["score"] += (
        customers["similar_slot_bookings"] * 15
    )

    # Customer loyalty
    customers.loc[
        customers["customer_type"] == "Regular",
        "score"
    ] += 20

    customers.loc[
        customers["customer_type"] == "Occasional",
        "score"
    ] += 10

    # Overall booking frequency
    customers["score"] += (
        customers["booking_frequency"] * 2
    )

    # Sort by highest targeting score
    customers = customers.sort_values(
        by="score",
        ascending=False
    )

    return customers.head(limit)

if __name__ == "__main__":

    customers = get_customer_segments()

    print("Customer Segments")
    print("=================")

    print(
        customers[
            [
                "name",
                "customer_type",
                "booking_frequency"
            ]
        ].head(10).to_string(index=False)
    )