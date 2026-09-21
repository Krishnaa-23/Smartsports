import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd

REFERENCE_DATE = datetime(2026, 9, 15).date()
# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite database
DATABASE_PATH = BASE_DIR / "database" / "sports_booking.db"


def get_available_slots():
    """
    Get only available future slots.
    Historical slots are excluded because they are
    used only for demand analysis.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            s.slot_id,
            s.court_id,
            c.court_name,
            c.sport,
            s.slot_date,
            s.start_time,
            s.end_time,
            s.base_price
        FROM slots s
        JOIN courts c
            ON s.court_id = c.court_id
        WHERE s.status = 'Available'
        AND datetime(s.slot_date || ' ' || s.start_time)
            >= datetime('now', 'localtime')
        ORDER BY s.slot_date, s.start_time
    """

    slots = pd.read_sql_query(query, connection)

    connection.close()

    return slots

def calculate_fill_rate(court_id, start_time):
    """
    Calculate historical fill rate for a specific court
    and time slot.

    Historical period:
    August 1, 2026 to September 14, 2026
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
        WHERE s.court_id = ?
        AND s.start_time = ?
        AND s.slot_date < '2026-09-15'
    """

    result = pd.read_sql_query(
        query,
        connection,
        params=(int(court_id), start_time)
    )

    connection.close()

    total_slots = int(result.iloc[0]["total_slots"])
    booked_slots = int(result.iloc[0]["booked_slots"])

    if total_slots == 0:
        return 0.0

    return round(
        (booked_slots / total_slots) * 100,
        2
    )

def calculate_hours_until_slot(slot_date, start_time):
    """
    Calculate how many hours remain before a slot starts.
    """

    slot_datetime = datetime.strptime(
        f"{slot_date} {start_time}",
        "%Y-%m-%d %H:%M"
    )

    current_datetime = datetime.now()

    difference = slot_datetime - current_datetime

    hours_remaining = difference.total_seconds() / 3600

    return round(hours_remaining, 2)


def analyze_slot(slot):
    """
    Analyze a single vacant slot and return
    useful business context for the AI agent.
    """

    fill_rate = calculate_fill_rate(
        slot["court_id"],
        slot["start_time"]
    )

    hours_remaining = calculate_hours_until_slot(
        slot["slot_date"],
        slot["start_time"]
    )

    if fill_rate < 40:
        demand_level = "Low"

    elif fill_rate < 70:
        demand_level = "Medium"

    else:
        demand_level = "High"

    if hours_remaining <= 3:
        urgency = "High"

    elif hours_remaining <= 12:
        urgency = "Medium"

    else:
        urgency = "Low"

    return {
        "slot_id": int(slot["slot_id"]),
        "court_name": slot["court_name"],
        "sport": slot["sport"],
        "slot_date": slot["slot_date"],
        "start_time": slot["start_time"],
        "end_time": slot["end_time"],
        "base_price": float(slot["base_price"]),
        "historical_fill_rate": fill_rate,
        "demand_level": demand_level,
        "hours_remaining": hours_remaining,
        "urgency": urgency
    }


if __name__ == "__main__":

    available_slots = get_available_slots()

    print(f"Available slots found: {len(available_slots)}")
    print()

    # Analyze first 5 available slots
    for _, slot in available_slots.head(5).iterrows():

        analysis = analyze_slot(slot)

        print("--------------------------------")
        print(f"Slot: {analysis['court_name']}")
        print(
            f"Time: {analysis['slot_date']} "
            f"{analysis['start_time']} - {analysis['end_time']}"
        )
        print(
            f"Historical Fill Rate: "
            f"{analysis['historical_fill_rate']}%"
        )
        print(f"Demand Level: {analysis['demand_level']}")
        print(
            f"Hours Remaining: "
            f"{analysis['hours_remaining']}"
        )
        print(f"Urgency: {analysis['urgency']}")