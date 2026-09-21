def generate_offer(decision_result):
    """
    Generate a customer-facing message based on
    the agent's decision.
    """

    court_name = decision_result["court_name"]
    sport = decision_result["sport"]
    date = decision_result["slot_date"]
    start_time = decision_result["start_time"]
    end_time = decision_result["end_time"]

    decision = decision_result["decision"]
    discount = decision_result["discount_percentage"]
    base_price = decision_result["base_price"]

    discounted_price = base_price * (1 - discount / 100)

    if decision == "NOTIFY":

        message = (
            f"🏟️ {sport} Slot Available!\n\n"
            f"{court_name} is available on {date} "
            f"from {start_time} to {end_time}.\n\n"
            f"Book your slot now for ₹{base_price:.0f}."
        )

    elif decision == "DISCOUNT":

        message = (
            f"🔥 Special Offer!\n\n"
            f"{court_name} is available on {date} "
            f"from {start_time} to {end_time}.\n\n"
            f"Get {discount:.0f}% OFF!\n"
            f"Original Price: ₹{base_price:.0f}\n"
            f"Offer Price: ₹{discounted_price:.0f}\n\n"
            f"Book now and grab the slot!"
        )

    elif decision == "NOTIFY + DISCOUNT":

        message = (
            f"🔥 Limited-Time Sports Offer!\n\n"
            f"{court_name} is available on {date} "
            f"from {start_time} to {end_time}.\n\n"
            f"Get {discount:.0f}% OFF your booking!\n"
            f"Original Price: ₹{base_price:.0f}\n"
            f"Offer Price: ₹{discounted_price:.0f}\n\n"
            f"Book now before the slot is taken!"
        )

    else:

        message = (
            f"{court_name} is currently available on "
            f"{date} from {start_time} to {end_time}."
        )

    return message