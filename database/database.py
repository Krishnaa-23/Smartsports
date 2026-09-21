import sqlite3
from pathlib import Path


# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Location of the SQLite database
DATABASE_PATH = BASE_DIR / "database" / "sports_booking.db"

# Location of the SQL schema
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_connection():
    """Create and return a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create all required tables using schema.sql."""
    connection = get_connection()

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        schema = file.read()

    connection.executescript(schema)
    connection.commit()
    connection.close()

    print("Database initialized successfully!")


def save_agent_decision(
    slot_id,
    decision,
    discount_percentage,
    reason,
    offer_message
):
    """
    Save an agent decision to the database.
    """

    connection = get_connection()

    query = """
        INSERT INTO agent_decisions
        (
            slot_id,
            decision,
            discount_percentage,
            reason,
            offer_message
        )
        VALUES (?, ?, ?, ?, ?)
    """

    connection.execute(
        query,
        (
            int(slot_id),
            decision,
            float(discount_percentage),
            reason,
            offer_message
        )
    )

    connection.commit()
    connection.close()


def get_agent_decisions():
    """
    Retrieve all agent decisions from the database.
    """

    connection = get_connection()

    query = """
        SELECT
            a.decision_id,
            a.slot_id,
            c.court_name,
            c.sport,
            s.slot_date,
            s.start_time,
            s.end_time,
            a.decision,
            a.discount_percentage,
            a.reason,
            a.offer_message,
            a.created_at
        FROM agent_decisions a
        JOIN slots s
            ON a.slot_id = s.slot_id
        JOIN courts c
            ON s.court_id = c.court_id
        ORDER BY a.created_at DESC
    """

    result = connection.execute(query).fetchall()

    columns = [
        "decision_id",
        "slot_id",
        "court_name",
        "sport",
        "slot_date",
        "start_time",
        "end_time",
        "decision",
        "discount_percentage",
        "reason",
        "offer_message",
        "created_at"
    ]

    connection.close()

    return result, columns

def get_customer_available_slots(sport=None, slot_date=None):
    """
    Retrieve available slots for customers.
    Optional filters:
    - sport
    - slot_date
    """

    connection = get_connection()

    query = """
        SELECT
            s.slot_id,
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
    """

    parameters = []

    if sport and sport.lower() != "all":
        query += " AND LOWER(c.sport) = LOWER(?)"
        parameters.append(sport.strip())

    if slot_date:
        query += " AND s.slot_date = ?"
        parameters.append(slot_date.strip())
    else:
        query += " AND s.slot_date >= date('now')"

    query += """
        ORDER BY
            s.slot_date,
            s.start_time,
            s.base_price
    """

    result = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return result


def create_booking(
    customer_id,
    slot_id,
    amount_paid
):
    """
    Create a booking for a customer and mark
    the selected slot as booked.
    """

    connection = get_connection()

    # Check whether the slot is still available
    slot = connection.execute(
        """
        SELECT status
        FROM slots
        WHERE slot_id = ?
        """,
        (int(slot_id),)
    ).fetchone()

    if slot is None:
        connection.close()
        return False, "Slot not found."

    if slot[0] != "Available":
        connection.close()
        return False, "Sorry, this slot is no longer available."

    # Create booking
    connection.execute(
        """
        INSERT INTO bookings
        (
            customer_id,
            slot_id,
            booking_date,
            amount_paid,
            status
        )
        VALUES (?, ?, datetime('now'), ?, 'Confirmed')
        """,
        (
            int(customer_id),
            int(slot_id),
            float(amount_paid)
        )
    )

    # Mark slot as booked
    connection.execute(
        """
        UPDATE slots
        SET status = 'Booked'
        WHERE slot_id = ?
        """,
        (int(slot_id),)
    )

    connection.commit()
    connection.close()

    return True, "Booking confirmed successfully."


def init_dynamic_pricing_table():
    """Ensure dynamic_prices table exists in the database."""
    connection = get_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS dynamic_prices (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            base_price REAL NOT NULL,
            suggested_price REAL NOT NULL,
            approved_price REAL NOT NULL,
            adjustment_percentage REAL NOT NULL,
            demand TEXT NOT NULL,
            status TEXT DEFAULT 'Approved',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (slot_id) REFERENCES slots(slot_id)
        )
        """
    )
    connection.commit()
    connection.close()


def apply_dynamic_price(
    slot_id,
    approved_price,
    base_price,
    suggested_price,
    adjustment_percentage,
    demand,
    status="Approved"
):
    """
    Record an approved/modified dynamic price in dynamic_prices
    and update the actual base_price in slots table if approved or modified.
    """
    connection = get_connection()

    # Insert into audit table
    connection.execute(
        """
        INSERT INTO dynamic_prices (
            slot_id,
            base_price,
            suggested_price,
            approved_price,
            adjustment_percentage,
            demand,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(slot_id),
            float(base_price),
            float(suggested_price),
            float(approved_price),
            float(adjustment_percentage),
            str(demand),
            str(status)
        )
    )

    # If approved or modified, update the actual slot base_price
    if status in ("Approved", "Modified"):
        connection.execute(
            """
            UPDATE slots
            SET base_price = ?
            WHERE slot_id = ?
            """,
            (
                float(approved_price),
                int(slot_id)
            )
        )

    connection.commit()
    connection.close()

    return True, f"Slot #{slot_id} price set to ₹{approved_price:,.0f} ({status})."


def get_dynamic_price_history():
    """
    Retrieve all recorded dynamic price decisions with slot and court details.
    """
    connection = get_connection()

    query = """
        SELECT
            dp.price_id,
            dp.slot_id,
            c.court_name,
            c.sport,
            s.slot_date,
            s.start_time,
            s.end_time,
            dp.base_price,
            dp.suggested_price,
            dp.approved_price,
            dp.adjustment_percentage,
            dp.demand,
            dp.status,
            dp.created_at
        FROM dynamic_prices dp
        JOIN slots s ON dp.slot_id = s.slot_id
        JOIN courts c ON s.court_id = c.court_id
        ORDER BY dp.created_at DESC
    """

    result = connection.execute(query).fetchall()

    columns = [
        "price_id",
        "slot_id",
        "court_name",
        "sport",
        "slot_date",
        "start_time",
        "end_time",
        "base_price",
        "suggested_price",
        "approved_price",
        "adjustment_percentage",
        "demand",
        "status",
        "created_at"
    ]

    connection.close()

    return result, columns


def init_notifications_table():
    """Ensure notifications table exists in the database."""
    connection = get_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            channel TEXT DEFAULT 'WhatsApp',
            recipient_name TEXT,
            message TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (slot_id) REFERENCES slots(slot_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
        """
    )
    connection.commit()
    connection.close()


def dispatch_notifications(slot_id, target_customers, message, channel="WhatsApp"):
    """
    Dispatch and log personalized notifications to target customers.
    """
    connection = get_connection()
    count = 0

    for cust in target_customers:
        cust_id = cust.get("customer_id")
        cust_name = cust.get("name", "Valued Customer")
        if cust_id is not None:
            connection.execute(
                """
                INSERT INTO notifications (
                    slot_id,
                    customer_id,
                    channel,
                    recipient_name,
                    message
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    int(slot_id),
                    int(cust_id),
                    channel,
                    cust_name,
                    message
                )
            )
            count += 1

    connection.commit()
    connection.close()
    return count


def get_notification_history():
    """
    Retrieve logged notification dispatches.
    """
    connection = get_connection()
    query = """
        SELECT
            n.notification_id,
            n.slot_id,
            c.court_name,
            c.sport,
            s.slot_date,
            s.start_time,
            s.end_time,
            n.recipient_name,
            n.channel,
            n.message,
            n.sent_at
        FROM notifications n
        JOIN slots s ON n.slot_id = s.slot_id
        JOIN courts c ON s.court_id = c.court_id
        ORDER BY n.sent_at DESC
    """
    result = connection.execute(query).fetchall()
    columns = [
        "notification_id",
        "slot_id",
        "court_name",
        "sport",
        "slot_date",
        "start_time",
        "end_time",
        "recipient_name",
        "channel",
        "message",
        "sent_at"
    ]
    connection.close()
    return result, columns


def get_customer_bookings(customer_id):
    """
    Retrieve all bookings for a given customer.
    """
    connection = get_connection()
    query = """
        SELECT
            b.booking_id,
            b.slot_id,
            c.court_name,
            c.sport,
            s.slot_date,
            s.start_time,
            s.end_time,
            b.amount_paid,
            b.status,
            b.booking_date
        FROM bookings b
        JOIN slots s ON b.slot_id = s.slot_id
        JOIN courts c ON s.court_id = c.court_id
        WHERE b.customer_id = ?
        ORDER BY s.slot_date DESC, s.start_time DESC
    """
    result = connection.execute(query, (int(customer_id),)).fetchall()
    columns = [
        "booking_id",
        "slot_id",
        "court_name",
        "sport",
        "slot_date",
        "start_time",
        "end_time",
        "amount_paid",
        "status",
        "booking_date"
    ]
    connection.close()
    return result, columns


def cancel_booking(booking_id):
    """
    Cancel a customer booking and revert the slot status back to 'Available'.
    """
    connection = get_connection()

    booking = connection.execute(
        """
        SELECT slot_id, status
        FROM bookings
        WHERE booking_id = ?
        """,
        (int(booking_id),)
    ).fetchone()

    if not booking:
        connection.close()
        return False, "Booking not found."

    slot_id, current_status = booking
    if current_status == "Cancelled":
        connection.close()
        return False, "This booking is already cancelled."

    # Update booking status
    connection.execute(
        """
        UPDATE bookings
        SET status = 'Cancelled'
        WHERE booking_id = ?
        """,
        (int(booking_id),)
    )

    # Free up slot
    connection.execute(
        """
        UPDATE slots
        SET status = 'Available'
        WHERE slot_id = ?
        """,
        (int(slot_id),)
    )

    connection.commit()
    connection.close()
    return True, f"Booking #{booking_id} cancelled. Slot #{slot_id} is now Available again."


# Ensure tables exist upon module import
try:
    init_dynamic_pricing_table()
    init_notifications_table()
except Exception:
    pass


if __name__ == "__main__":
    initialize_database()