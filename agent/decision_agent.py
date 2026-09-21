from utils.slot_optimizer import analyze_slot
from agent.offer_generator import generate_offer
from analytics.customer_segmentation import get_target_customers
from analytics.revenue_analysis import calculate_slot_economics


def make_decision(slot):
    """
    Decide the best action for a vacant sports slot.

    Possible decisions:
    - NOTIFY
    - DISCOUNT
    - NOTIFY + DISCOUNT
    - NO ACTION

    The decision considers:
    - Historical demand
    - Time remaining
    - Revenue impact
    - Estimated profit impact
    """

    analysis = analyze_slot(slot)

    fill_rate = analysis["historical_fill_rate"]
    demand = analysis["demand_level"]
    urgency = analysis["urgency"]
    hours_remaining = analysis["hours_remaining"]
    base_price = analysis["base_price"]

    # ------------------------------------------------
    # Calculate economics for a 10% discount
    # ------------------------------------------------

    economics = calculate_slot_economics(
        base_price,
        10
    )

    discounted_profit = economics["discounted_profit"]
    profit_margin = economics["profit_margin"]

    # ------------------------------------------------
    # Decision Logic
    # ------------------------------------------------

    if demand == "Low" and urgency == "High":

        decision = "NOTIFY + DISCOUNT"
        discount = 10

        reason = (
            f"The slot has low historical demand "
            f"({fill_rate}%) and only {hours_remaining} hours "
            f"remain before the slot starts. A 10% discount "
            f"combined with targeted outreach can improve the "
            f"chance of filling the slot. The estimated profit "
            f"after discount remains ₹{discounted_profit:.0f} "
            f"with an estimated margin of {profit_margin:.2f}%."
        )

    elif demand == "Low":

        decision = "DISCOUNT"
        discount = 10

        reason = (
            f"The slot has low historical demand "
            f"({fill_rate}%). A 10% discount is recommended "
            f"to improve booking probability while maintaining "
            f"an estimated profit of ₹{discounted_profit:.0f} "
            f"and margin of {profit_margin:.2f}%."
        )

    elif demand == "Medium" and urgency == "High":

        decision = "NOTIFY + DISCOUNT"
        discount = 10

        reason = (
            f"The slot has medium historical demand "
            f"({fill_rate}%) but only {hours_remaining} hours "
            f"remain. Targeted outreach with a 10% discount "
            f"can encourage a quick booking. The estimated "
            f"profit after discount is ₹{discounted_profit:.0f} "
            f"with a margin of {profit_margin:.2f}%."
        )

    elif demand == "High":

        decision = "NOTIFY"
        discount = 0

        reason = (
            f"The slot has a high historical fill rate "
            f"({fill_rate}%). Discounting could unnecessarily "
            f"reduce revenue, so targeted notification is "
            f"recommended instead."
        )

    else:

        decision = "NOTIFY"
        discount = 0

        reason = (
            f"The slot has moderate demand with a historical "
            f"fill rate of {fill_rate}%. Targeted outreach is "
            f"recommended while avoiding an unnecessary "
            f"discount."
        )

        # ------------------------------------------------
    # Calculate Final Economics
    # ------------------------------------------------

    final_economics = calculate_slot_economics(
        base_price,
        discount
    )

    estimated_profit = final_economics["discounted_profit"]
    final_profit_margin = final_economics["profit_margin"]

    # ------------------------------------------------
    # Find Target Customers
    # ------------------------------------------------

    target_customers = get_target_customers(
        slot,
        limit=5
    )

    target_customer_names = target_customers[
        "name"
    ].tolist()

    # ------------------------------------------------
    # Return Decision
    # ------------------------------------------------

    return {
        "slot_id": analysis["slot_id"],
        "court_name": analysis["court_name"],
        "sport": analysis["sport"],
        "slot_date": analysis["slot_date"],
        "start_time": analysis["start_time"],
        "end_time": analysis["end_time"],
        "base_price": base_price,

        "historical_fill_rate": fill_rate,
        "demand_level": demand,
        "hours_remaining": hours_remaining,
        "urgency": urgency,

        "decision": decision,
        "discount_percentage": discount,

        "discounted_price": final_economics["discounted_price"],
        "estimated_profit": estimated_profit,
        "profit_margin": final_profit_margin,

        "reason": reason,
        "target_customers": target_customer_names
    }


if __name__ == "__main__":

    from utils.slot_optimizer import get_available_slots

    available_slots = get_available_slots()

    print(f"Available slots: {len(available_slots)}")
    print()

    # Test the agent with the first 5 available slots

    for _, slot in available_slots.head(5).iterrows():

        result = make_decision(slot)

        offer = generate_offer(result)

        print("--------------------------------------")

        print(f"Court: {result['court_name']}")

        print(f"Sport: {result['sport']}")

        print(
            f"Slot: {result['slot_date']} "
            f"{result['start_time']} - "
            f"{result['end_time']}"
        )

        print(
            f"Historical Fill Rate: "
            f"{result['historical_fill_rate']}%"
        )

        print(
            f"Demand: "
            f"{result['demand_level']}"
        )

        print(
            f"Urgency: "
            f"{result['urgency']}"
        )

        print(
            f"Decision: "
            f"{result['decision']}"
        )

        print(
            f"Discount: "
            f"{result['discount_percentage']}%"
        )

        print(
            f"Estimated Profit: "
            f"₹{result['estimated_profit']}"
        )

        print(
            f"Profit Margin: "
            f"{result['profit_margin']}%"
        )

        print(
            f"Reason: "
            f"{result['reason']}"
        )

        print()

        print("Target Customers:")

        for customer in result["target_customers"]:
            print(f"- {customer}")

        print()

        print("Customer Offer:")

        print(offer)