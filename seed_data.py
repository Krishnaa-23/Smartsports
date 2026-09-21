import pandas as pd
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "database" / "sports_booking.db"

CUSTOMERS_CSV = BASE_DIR / "data" / "customers.csv"
BOOKINGS_CSV = BASE_DIR / "data" / "bookings.csv"
SLOTS_CSV = BASE_DIR / "data" / "slots.csv"


def seed_database():

    connection = sqlite3.connect(DATABASE_PATH)

    # Clear existing data
    connection.execute("DELETE FROM agent_decisions")
    connection.execute("DELETE FROM bookings")
    connection.execute("DELETE FROM slots")
    connection.execute("DELETE FROM customers")
    connection.execute("DELETE FROM courts")

    # Reset auto-increment counters
    connection.execute(
        "DELETE FROM sqlite_sequence"
    )

    # Add courts
    courts = [
        (1, "Turf 1", "Football", 1200),
        (2, "Court 2", "Badminton", 500),
        (3, "Turf 2", "Football", 900)
    ]

    connection.executemany(
        """
        INSERT INTO courts
        (court_id, court_name, sport, hourly_price)
        VALUES (?, ?, ?, ?)
        """,
        courts
    )

    # Load customers
    customers = pd.read_csv(CUSTOMERS_CSV)

    customers.to_sql(
        "customers",
        connection,
        if_exists="append",
        index=False
    )

    # Load slots
    slots = pd.read_csv(SLOTS_CSV)

    slots.to_sql(
        "slots",
        connection,
        if_exists="append",
        index=False
    )

    # Load bookings
    bookings = pd.read_csv(BOOKINGS_CSV)

    bookings.to_sql(
        "bookings",
        connection,
        if_exists="append",
        index=False
    )

    connection.commit()
    connection.close()

    print("Database refreshed successfully!")
    print(f"Customers loaded: {len(customers)}")
    print(f"Slots loaded: {len(slots)}")
    print(f"Bookings loaded: {len(bookings)}")


if __name__ == "__main__":
    seed_database()