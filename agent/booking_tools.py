from datetime import datetime

from database.database import (
    get_customer_available_slots,
    create_booking
)


# -----------------------------------
# Search Available Slots
# -----------------------------------

def search_slots(
    sport: str,
    slot_date: str,
    max_price: float
):
    """
    Search available sports slots.

    Use an empty string for sport or slot_date
    when the customer did not specify them.

    Use 0 for max_price when there is no
    maximum price.

    Args:
        sport: Sport name such as Football or Badminton.
        slot_date: Date in YYYY-MM-DD format, or empty string.
        max_price: Maximum price, or 0 if there is no limit.
    """

    if sport == "":
        sport_filter = None
    else:
        sport_filter = sport

    if slot_date == "":
        date_filter = None
    else:
        date_filter = slot_date

    if max_price <= 0:
        price_limit = None
    else:
        price_limit = max_price

    slots = get_customer_available_slots(
        sport=sport_filter,
        slot_date=date_filter
    )

    today = datetime.now().strftime("%Y-%m-%d")

    results = []

    for slot in slots:

        (
            slot_id,
            court_name,
            sport_name,
            date,
            start_time,
            end_time,
            base_price
        ) = slot

        # Ignore past dates
        if date < today:
            continue

        # Apply maximum price filter
        if (
            price_limit is not None
            and base_price > price_limit
        ):
            continue

        results.append(
            {
                "slot_id": slot_id,
                "court_name": court_name,
                "sport": sport_name,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "price": base_price
            }
        )

    return results


# -----------------------------------
# Search Slots By Time
# -----------------------------------

def search_slots_by_time(
    sport: str,
    slot_date: str,
    preferred_time: str,
    max_price: float
):
    """
    Search available slots using a preferred
    time period.

    Args:
        sport: Sport name such as Football or Badminton.
        slot_date: Date in YYYY-MM-DD format, or empty string.
        preferred_time: morning, afternoon, or evening.
        max_price: Maximum price, or 0 if there is no limit.
    """

    slots = search_slots(
        sport=sport,
        slot_date=slot_date,
        max_price=max_price
    )

    if preferred_time == "":
        return slots

    filtered_slots = []

    for slot in slots:

        hour = int(
            slot["start_time"].split(":")[0]
        )

        if preferred_time.lower() == "morning":

            if 6 <= hour < 12:
                filtered_slots.append(slot)

        elif preferred_time.lower() == "afternoon":

            if 12 <= hour < 17:
                filtered_slots.append(slot)

        elif preferred_time.lower() == "evening":

            if 17 <= hour <= 22:
                filtered_slots.append(slot)

    return filtered_slots


# -----------------------------------
# Book Slot
# -----------------------------------

def book_slot(
    customer_id: int,
    slot_id: int
):
    """
    Book a specific sports slot.

    The database independently verifies that the
    slot exists, is available, and uses the actual
    current price from the database.
    """

    from database.database import get_connection

    connection = get_connection()

    # Check the slot and get its actual database price
    slot = connection.execute(
        """
        SELECT
            s.status,
            s.base_price,
            c.court_name,
            c.sport,
            s.slot_date,
            s.start_time,
            s.end_time
        FROM slots s
        JOIN courts c
            ON s.court_id = c.court_id
        WHERE s.slot_id = ?
        """,
        (int(slot_id),)
    ).fetchone()

    if slot is None:
        connection.close()

        return {
            "success": False,
            "message": "Slot not found."
        }

    (
        status,
        actual_price,
        court_name,
        sport,
        slot_date,
        start_time,
        end_time
    ) = slot

    # Check availability
    if status != "Available":
        # If THIS customer already holds a confirmed booking for the slot
        # (for example the chat retried the same request after a temporary
        # Gemini error), say so instead of "no longer available".
        mine = connection.execute(
            """
            SELECT amount_paid
            FROM bookings
            WHERE customer_id = ?
              AND slot_id = ?
              AND status = 'Confirmed'
            """,
            (int(customer_id), int(slot_id))
        ).fetchone()

        connection.close()

        if mine:
            return {
                "success": True,
                "message": "This slot is already booked for you.",
                "slot_id": slot_id,
                "court": court_name,
                "sport": sport,
                "date": slot_date,
                "start_time": start_time,
                "end_time": end_time,
                "price": mine[0],
                "already_booked": True
            }

        return {
            "success": False,
            "message": "Sorry, this slot is no longer available."
        }

    connection.close()

    # Use the database price, NOT a price supplied by Gemini
    success, message = create_booking(
        customer_id=customer_id,
        slot_id=slot_id,
        amount_paid=actual_price
    )

    return {
        "success": success,
        "message": message,
        "slot_id": slot_id,
        "court": court_name,
        "sport": sport,
        "date": slot_date,
        "start_time": start_time,
        "end_time": end_time,
        "price": actual_price
    }

# -----------------------------------
# Terminal Test
# -----------------------------------

if __name__ == "__main__":

    print("\n--- Available Football Slots ---")

    slots = search_slots(
        sport="Football",
        slot_date="",
        max_price=0
    )

    for slot in slots[:5]:
        print(slot)

    print("\n--- Evening Football Under ₹1000 ---")

    slots = search_slots_by_time(
        sport="Football",
        slot_date="",
        preferred_time="evening",
        max_price=1000
    )

    for slot in slots:
        print(slot)