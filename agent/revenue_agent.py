"""
Unified Revenue Optimization Agent for SmartSports.
Combines Demand Analysis, Dynamic Pricing, Profit Economics,
Customer Segmentation, and Offer Generation into a single decision engine.
"""

from utils.slot_optimizer import analyze_slot
from utils.dynamic_pricing import get_slot_dynamic_price
from analytics.customer_segmentation import get_target_customers
from analytics.revenue_analysis import calculate_slot_economics


def optimize_slot_revenue(slot):
    """
    Run full revenue optimization analysis on a vacant slot.

    Pipeline:
    1. Demand & Urgency Analysis
    2. Dynamic Pricing Engine (Fill Rate + Lead Time Offset)
    3. Profit & Margin Impact Computation
    4. Behavioral Customer Segmentation (Targeting)
    5. Contextual Promotional Offer Generation
    6. Unified Action Recommendation
    """

    # 1. Base slot analysis
    slot_analysis = analyze_slot(slot)
    slot_id = slot_analysis["slot_id"]
    court_name = slot_analysis["court_name"]
    sport = slot_analysis["sport"]
    slot_date = slot_analysis["slot_date"]
    start_time = slot_analysis["start_time"]
    end_time = slot_analysis["end_time"]
    base_price = slot_analysis["base_price"]
    historical_fill_rate = slot_analysis["historical_fill_rate"]
    urgency = slot_analysis["urgency"]
    hours_remaining = slot_analysis["hours_remaining"]

    # 2. Dynamic Pricing Engine
    dyn_pricing = get_slot_dynamic_price(slot_id)
    if dyn_pricing:
        suggested_price = dyn_pricing["suggested_price"]
        adjustment_pct = dyn_pricing["adjustment_percentage"]
        demand_level = dyn_pricing["demand"]
        days_until_slot = dyn_pricing["days_until_slot"]
    else:
        suggested_price = base_price
        adjustment_pct = 0
        demand_level = slot_analysis["demand_level"].upper()
        days_until_slot = max(0, int(hours_remaining // 24))

    # 3. Economics & Profit Impact
    effective_discount = -adjustment_pct if adjustment_pct < 0 else 0
    economics = calculate_slot_economics(
        base_price=base_price,
        discount_percentage=effective_discount
    )

    profit = economics["discounted_profit"]
    margin = economics["profit_margin"]

    # 4. Strategic Revenue Action & Reasoning
    if demand_level == "HIGH":
        action = "SURGE PRICING + VIP NOTIFICATION"
        reasoning = (
            f"Strong historical fill rate ({historical_fill_rate:.1f}%). "
            f"Demand allows a dynamic surge of {adjustment_pct:+.0f}% to ₹{suggested_price:,.0f} "
            f"while preserving high booking probability. Notify high-frequency VIP players first."
        )
    elif demand_level == "LOW" and urgency in ("High", "Medium"):
        action = "DYNAMIC DISCOUNT + URGENT CLEARANCE"
        reasoning = (
            f"Low demand ({historical_fill_rate:.1f}%) and high urgency ({hours_remaining:.1f} hrs left). "
            f"Reducing price by {abs(adjustment_pct):.0f}% to ₹{suggested_price:,.0f} stimulates fast conversion "
            f"to prevent slot expiry and zero revenue, yielding ₹{profit:,.0f} profit ({margin:.1f}% margin)."
        )
    elif demand_level == "LOW":
        action = "DYNAMIC DISCOUNT + EARLY-BIRD OUTREACH"
        reasoning = (
            f"Historical fill rate is low ({historical_fill_rate:.1f}%) with {days_until_slot} day(s) lead time. "
            f"Applying an early discount of {abs(adjustment_pct):.0f}% to ₹{suggested_price:,.0f} "
            f"incentivizes early-bird booking from price-conscious customers."
        )
    else:  # MEDIUM
        action = "OPTIMIZED BASE RATE + TARGETED OUTREACH"
        reasoning = (
            f"Healthy historical fill rate ({historical_fill_rate:.1f}%). "
            f"Retaining standard rate of ₹{base_price:,.0f} protects profit margins "
            f"(₹{profit:,.0f}, {margin:.1f}%). Focus on direct outreach to matching players."
        )

    # 5. Customer Segmentation & Targeting
    target_df = get_target_customers(slot, limit=5)
    target_customers = []
    if not target_df.empty:
        for _, cust in target_df.iterrows():
            target_customers.append({
                "customer_id": int(cust["customer_id"]),
                "name": str(cust["name"]),
                "email": str(cust["email"]),
                "customer_type": str(cust["customer_type"]),
                "booking_frequency": int(cust["booking_frequency"]),
                "score": float(cust.get("score", 0))
            })

    # 6. Contextual Promotional Offer Message
    if adjustment_pct < 0:
        offer_headline = f"🔥 Special Flash Offer: {abs(adjustment_pct):.0f}% OFF!"
        pricing_text = (
            f"Original Price: ₹{base_price:,.0f}\n"
            f"Dynamic Offer Price: ₹{suggested_price:,.0f}"
        )
    elif adjustment_pct > 0:
        offer_headline = "⚡ High-Demand Prime Slot Available!"
        pricing_text = f"Prime Rate: ₹{suggested_price:,.0f}"
    else:
        offer_headline = "🏟️ Your Preferred Slot is Available!"
        pricing_text = f"Standard Rate: ₹{base_price:,.0f}"

    offer_message = (
        f"{offer_headline}\n\n"
        f"Hi there! {court_name} has an open slot for {sport}:\n"
        f"📅 Date: {slot_date}\n"
        f"⏰ Time: {start_time} - {end_time}\n"
        f"{pricing_text}\n\n"
        f"Book now on SmartSports before it fills up!"
    )

    return {
        "slot_id": slot_id,
        "court_name": court_name,
        "sport": sport,
        "slot_date": slot_date,
        "start_time": start_time,
        "end_time": end_time,
        "base_price": base_price,
        "suggested_price": suggested_price,
        "adjustment_percentage": adjustment_pct,
        "demand_level": demand_level,
        "historical_fill_rate": historical_fill_rate,
        "hours_remaining": hours_remaining,
        "days_until_slot": days_until_slot,
        "urgency": urgency,
        "action": action,
        "reasoning": reasoning,
        "estimated_profit": profit,
        "profit_margin": margin,
        "target_customers": target_customers,
        "offer_message": offer_message
    }
