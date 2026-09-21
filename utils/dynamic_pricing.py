from datetime import datetime
from database.database import get_connection


def get_historical_fill_rate(court_id, start_time):
    """
    Calculate historical fill rate for a court and
    time slot using completed/past slots.

    Returns a value between 0 and 1.
    """

    connection = get_connection()

    query = """
        SELECT
            COUNT(*) AS total_slots,
            SUM(
                CASE
                    WHEN status = 'Booked' THEN 1
                    ELSE 0
                END
            ) AS booked_slots
        FROM slots
        WHERE court_id = ?
        AND start_time = ?
        AND slot_date < date('now')
    """

    result = connection.execute(
        query,
        (
            int(court_id),
            start_time
        )
    ).fetchone()

    connection.close()

    total_slots = result[0] or 0
    booked_slots = result[1] or 0

    if total_slots == 0:
        return 0.5

    return booked_slots / total_slots


def classify_demand(fill_rate):
    """
    Convert historical fill rate into a demand category.
    """

    if fill_rate >= 0.75:
        return "HIGH"

    if fill_rate >= 0.50:
        return "MEDIUM"

    return "LOW"


def calculate_dynamic_price(
    base_price,
    historical_fill_rate,
    days_until_slot
):
    """
    Calculate a suggested dynamic price.

    Rules:
    HIGH demand   -> +10%
    MEDIUM demand -> no change
    LOW demand    -> -10%

    Lead time can add another adjustment:

    HIGH demand + <= 1 day -> +5%
    LOW demand + <= 2 days -> -5%

    Maximum total adjustment is capped at +/-15%.
    """

    demand = classify_demand(
        historical_fill_rate
    )

    adjustment = 0

    # Demand-based adjustment
    if demand == "HIGH":
        adjustment += 10

    elif demand == "LOW":
        adjustment -= 10

    # Lead-time adjustment
    if days_until_slot <= 1:

        if demand == "HIGH":
            adjustment += 5

    elif days_until_slot <= 2:

        if demand == "LOW":
            adjustment -= 5

    # Protect against extreme pricing
    adjustment = max(
        -15,
        min(15, adjustment)
    )

    suggested_price = (
        base_price *
        (1 + adjustment / 100)
    )

    # Round to nearest ₹10
    suggested_price = round(
        suggested_price / 10
    ) * 10

    return {
        "base_price": base_price,
        "suggested_price": suggested_price,
        "adjustment_percentage": adjustment,
        "demand": demand,
        "historical_fill_rate": historical_fill_rate
    }


def get_slot_dynamic_price(slot_id):
    """
    Calculate dynamic pricing for a specific slot.
    """

    connection = get_connection()

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
        WHERE s.slot_id = ?
    """

    slot = connection.execute(
        query,
        (int(slot_id),)
    ).fetchone()

    connection.close()

    if slot is None:
        return None

    (
        slot_id,
        court_id,
        court_name,
        sport,
        slot_date,
        start_time,
        end_time,
        base_price
    ) = slot

    historical_fill_rate = get_historical_fill_rate(
        court_id=court_id,
        start_time=start_time
    )

    today = datetime.now().date()
    target_date = datetime.strptime(
        slot_date,
        "%Y-%m-%d"
    ).date()

    days_until_slot = (
        target_date - today
    ).days

    pricing = calculate_dynamic_price(
        base_price=base_price,
        historical_fill_rate=historical_fill_rate,
        days_until_slot=days_until_slot
    )

    return {
        "slot_id": slot_id,
        "court_name": court_name,
        "sport": sport,
        "date": slot_date,
        "start_time": start_time,
        "end_time": end_time,
        "days_until_slot": days_until_slot,
        **pricing
    }


if __name__ == "__main__":

    print()
    print("💰 SmartSports Dynamic Pricing Engine")
    print("=" * 50)

    slot_id = 1238

    result = get_slot_dynamic_price(
        slot_id
    )

    if result is None:

        print("Slot not found.")

    else:

        print()
        print(f"🏟️ Court: {result['court_name']}")
        print(f"🏅 Sport: {result['sport']}")
        print(f"📅 Date: {result['date']}")
        print(
            f"⏰ Time: "
            f"{result['start_time']} - "
            f"{result['end_time']}"
        )

        print()
        print(
            f"📊 Historical Fill Rate: "
            f"{result['historical_fill_rate']:.2%}"
        )

        print(
            f"📈 Demand: "
            f"{result['demand']}"
        )

        print(
            f"⏳ Days Until Slot: "
            f"{result['days_until_slot']}"
        )

        print()
        print(
            f"💰 Base Price: "
            f"₹{result['base_price']:.0f}"
        )

        print(
            f"🔄 Adjustment: "
            f"{result['adjustment_percentage']}%"
        )

        print(
            f"💵 Suggested Price: "
            f"₹{result['suggested_price']:.0f}"
        )