import sqlite3
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sports_booking.db"


def get_overall_fill_rate():
    """
    Calculate the historical overall fill rate.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            COUNT(DISTINCT s.slot_id) AS total_slots,
            COUNT(
                DISTINCT CASE
                    WHEN b.booking_id IS NOT NULL
                    THEN s.slot_id
                END
            ) AS booked_slots
        FROM slots s
        LEFT JOIN bookings b
            ON s.slot_id = b.slot_id
        WHERE s.slot_date < '2026-09-15'
    """

    result = pd.read_sql_query(query, connection)

    connection.close()

    total_slots = int(result.iloc[0]["total_slots"])
    booked_slots = int(result.iloc[0]["booked_slots"])

    if total_slots == 0:
        return 0.0

    return round(
        (booked_slots / total_slots) * 100,
        2
    )


def get_fill_rate_by_court():
    """
    Calculate historical fill rate for each court.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            c.court_name,
            c.sport,
            COUNT(DISTINCT s.slot_id) AS total_slots,
            COUNT(
                DISTINCT CASE
                    WHEN b.booking_id IS NOT NULL
                    THEN s.slot_id
                END
            ) AS booked_slots
        FROM courts c
        JOIN slots s
            ON c.court_id = s.court_id
        LEFT JOIN bookings b
            ON s.slot_id = b.slot_id
        WHERE s.slot_date < '2026-09-15'
        GROUP BY c.court_id
        ORDER BY c.court_id
    """

    result = pd.read_sql_query(query, connection)

    connection.close()

    result["fill_rate"] = (
        result["booked_slots"] /
        result["total_slots"] *
        100
    ).round(2)

    return result


def get_fill_rate_by_time():
    """
    Calculate historical fill rate for each time slot.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            s.start_time,
            COUNT(DISTINCT s.slot_id) AS total_slots,
            COUNT(
                DISTINCT CASE
                    WHEN b.booking_id IS NOT NULL
                    THEN s.slot_id
                END
            ) AS booked_slots
        FROM slots s
        LEFT JOIN bookings b
            ON s.slot_id = b.slot_id
        WHERE s.slot_date < '2026-09-15'
        GROUP BY s.start_time
        ORDER BY s.start_time
    """

    result = pd.read_sql_query(query, connection)

    connection.close()

    result["fill_rate"] = (
        result["booked_slots"] /
        result["total_slots"] *
        100
    ).round(2)

    return result