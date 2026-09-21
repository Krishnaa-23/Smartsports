import os
import time
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import errors

from agent.booking_tools import (
    search_slots,
    search_slots_by_time,
    book_slot
)


# -----------------------------------
# Load Environment Variables
# -----------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found in .env"
    )


# -----------------------------------
# Gemini Client
# -----------------------------------

client = genai.Client(
    api_key=api_key
)


# -----------------------------------
# Create Customer Chat
# -----------------------------------

def create_customer_chat(customer_id):
    """
    Create a Gemini chat session for a customer.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")

    system_instruction = f"""
You are SmartSports AI, an intelligent sports
facility booking assistant.

Your job is to help customers find available
sports slots and book them.

Today's date is {current_date}.

Customer ID:
{customer_id}

AVAILABLE TOOLS
---------------

search_slots:
Use this to find available sports slots.

search_slots_by_time:
Use this when the customer specifies
morning, afternoon, or evening.

book_slot:
Use this only when the customer explicitly
asks to book a specific slot.

Provide:
- customer_id
- slot_id

The database determines the actual price.
Never invent or modify the price.

IMPORTANT RULES
---------------

1. Never invent a slot.

2. Never invent a price.

3. Only recommend slots returned by the tools.

4. Respect the customer's:
   - sport
   - date
   - preferred time
   - maximum budget

5. If the customer says "tomorrow", calculate
   tomorrow's date from today's date.

6. If the customer specifies morning,
   afternoon, or evening, use
   search_slots_by_time.

7. If the customer gives a maximum price,
   never recommend a slot above that price.

8. Do not book a slot just because the
   customer asks what is available.

9. Before booking, the customer must clearly
   select a specific slot.

10. If you suggest a specific available slot
    and the customer later says "yes", "book it",
    "that one", or another clear confirmation,
    you may book the previously suggested slot.

11. Never claim that a booking succeeded unless
    the book_slot tool actually confirms it.

12. After a successful booking, clearly tell
    the customer that the booking is confirmed.

13. If no slot matches the customer's request,
    you may suggest a different available slot
    returned by the tools.

14. Keep responses concise and friendly.

When showing a slot, include:

🏟️ Court
🏅 Sport
📅 Date
⏰ Time
💰 Price
"""

MODELS_PRIORITY = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.6-flash",
]

def create_customer_chat(customer_id, preferred_model=None):
    """
    Create a Gemini chat session for a customer.
    Tries the resilient model pool in priority order.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")

    system_instruction = f"""
You are SmartSports AI, an intelligent sports facility booking assistant.

Your job is to help customers find available sports slots and book them.

Today's date is {current_date}.

Customer ID: {customer_id}

AVAILABLE TOOLS:
- search_slots: Use this to find available sports slots with optional sport, slot_date, and max_price.
- search_slots_by_time: Use this when the customer specifies morning, afternoon, or evening.
- book_slot: Use this only when the customer explicitly confirms they want to book a specific slot.

IMPORTANT GUIDELINES:
1. If the customer sends a simple greeting (e.g., 'hi', 'hello'), greet them warmly and ask how you can help them with their sports bookings today.
2. If the customer asks for slots (e.g., 'find me a football slot tomorrow' or 'day after tomorrow'), calculate the date accurately from today's date ({current_date}) and use search_slots.
3. Always display court name, sport, date, time, and price.
4. If no slots are available for a requested date, suggest other upcoming dates.
5. Only call book_slot after the customer clearly confirms.
"""

    models_to_try = [preferred_model] if preferred_model else MODELS_PRIORITY
    for model_name in models_to_try:
        try:
            chat = client.chats.create(
                model=model_name,
                config={
                    "system_instruction": system_instruction,
                    "tools": [
                        search_slots,
                        search_slots_by_time,
                        book_slot
                    ]
                }
            )
            chat._active_model_name = model_name
            chat._customer_id = customer_id
            return chat
        except Exception as e:
            print(f"Could not initialize model {model_name}: {e}")
            continue

    return None


# -----------------------------------
# Send Message & Robust Fallback
# -----------------------------------

def _deterministic_booking_fallback(customer_id, message, chat_obj=None):
    """
    Zero-Crash Fallback: Deterministic natural language processor
    that accurately resolves greetings, dates, sports, and times
    if Gemini API quota or network limits occur.
    """
    import re
    from datetime import datetime, timedelta

    msg_lower = message.lower().strip()

    # 1. Greetings
    greetings = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon", "hola", "greetings"}
    if msg_lower in greetings or msg_lower.startswith(("hi ", "hello ", "hey ")):
        return (
            "Hello! I am your SmartSports booking assistant. 🎾⚽\n\n"
            "How can I help you today? You can ask me to find football or badminton courts "
            "for today, tomorrow, or any preferred time (morning, afternoon, evening)!"
        )

    # 2. Rejection / Cancel intent
    if msg_lower in {"no", "nope", "cancel", "not this", "neither", "none", "no thanks"}:
        if chat_obj:
            chat_obj._last_suggested_slot = None
        return (
            "No problem at all! Let me know what date, sport, or time slot you'd prefer instead, "
            "and I'll find available courts for you."
        )

    # 3. Confirmation / booking intent
    last_slot = getattr(chat_obj, "_last_suggested_slot", None) if chat_obj else None
    if last_slot and any(w in msg_lower for w in ["yes", "book", "confirm", "that one", "please", "okay", "sure", "yep", "book it"]):
        result = book_slot(customer_id=customer_id, slot_id=last_slot["slot_id"])
        if result.get("success"):
            if chat_obj:
                chat_obj._last_suggested_slot = None
            return (
                f"🎉 **Booking Confirmed!**\n\n"
                f"🏟️ **Court**: {result['court']}\n"
                f"🏅 **Sport**: {result['sport']}\n"
                f"📅 **Date**: {result['date']}\n"
                f"⏰ **Time**: {result['start_time']} - {result['end_time']}\n"
                f"💰 **Amount Paid**: ₹{result['price']:,.0f}\n\n"
                f"Your slot is confirmed in the system. Enjoy your game!"
            )
        else:
            return f"❌ Booking issue: {result.get('message', 'Could not complete booking.')}"

    # 4. Extract Sport
    sport = ""
    if "football" in msg_lower or "turf" in msg_lower:
        sport = "Football"
    elif "badminton" in msg_lower or "court" in msg_lower or "shuttle" in msg_lower:
        sport = "Badminton"

    # 5. Extract Date accurately
    today = datetime.now()
    slot_date = ""
    if "day after tomorrow" in msg_lower:
        slot_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
    elif "tomorrow" in msg_lower:
        slot_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "today" in msg_lower:
        slot_date = today.strftime("%Y-%m-%d")
    else:
        date_match = re.search(r'\b(202[0-9]-[0-1][0-9]-[0-3][0-9])\b', msg_lower)
        if date_match:
            slot_date = date_match.group(1)
        else:
            month_match = re.search(r'\b(?:sep|september)\s*(\d{1,2})\b', msg_lower)
            if month_match:
                day_num = int(month_match.group(1))
                slot_date = f"2026-09-{day_num:02d}"

    # 6. Extract Time Preference
    pref_time = ""
    if "morning" in msg_lower:
        pref_time = "morning"
    elif "afternoon" in msg_lower:
        pref_time = "afternoon"
    elif "evening" in msg_lower or "night" in msg_lower:
        pref_time = "evening"

    # 7. Extract Budget
    max_price = 0.0
    price_match = re.search(r'(?:under|below|max|budget of|less than|rs\.?|₹)\s*(\d+)', msg_lower)
    if price_match:
        try:
            max_price = float(price_match.group(1))
        except Exception:
            max_price = 0.0

    # 8. Search Available Slots
    if pref_time:
        slots = search_slots_by_time(sport=sport, slot_date=slot_date, preferred_time=pref_time, max_price=max_price)
    else:
        slots = search_slots(sport=sport, slot_date=slot_date, max_price=max_price)

    if not slots:
        date_str = f" for {slot_date}" if slot_date else ""
        sport_str = f" {sport}" if sport else " sports"
        time_str = f" in the {pref_time}" if pref_time else ""
        return (
            f"I couldn't find any available{sport_str} slots{date_str}{time_str} matching your request. "
            f"Would you like me to check a different date or time?"
        )

    # Pick top match
    best_slot = slots[0]
    if chat_obj:
        chat_obj._last_suggested_slot = best_slot

    date_label = best_slot['date']
    if slot_date == (today + timedelta(days=2)).strftime("%Y-%m-%d"):
        date_label += " (Day after tomorrow)"
    elif slot_date == (today + timedelta(days=1)).strftime("%Y-%m-%d"):
        date_label += " (Tomorrow)"
    elif slot_date == today.strftime("%Y-%m-%d"):
        date_label += " (Today)"

    return (
        f"I found a great available slot for you:\n\n"
        f"🏟️ **Court**: {best_slot['court_name']}\n"
        f"🏅 **Sport**: {best_slot['sport']}\n"
        f"📅 **Date**: {date_label}\n"
        f"⏰ **Time**: {best_slot['start_time']} - {best_slot['end_time']}\n"
        f"💰 **Price**: ₹{best_slot['price']:,.0f}\n\n"
        f"Would you like me to book this slot for you? Just reply with **'Yes, book it'**!"
    )


def ask_customer_agent(chat, message, customer_id=1):
    """
    Send a message to an existing Gemini customer chat session.
    Automatically switches to alternate models if quota limits occur,
    and falls back seamlessly to deterministic natural language processing.
    """
    if chat is not None:
        try:
            response = chat.send_message(message)
            if response.text:
                return response.text
            if hasattr(response, "candidates") and response.candidates:
                parts = response.candidates[0].content.parts
                texts = [p.text for p in parts if hasattr(p, "text") and p.text]
                if texts:
                    return "\n".join(texts)
        except Exception as e:
            print(f"Gemini API Exception (activating model pool failover): {e}")
            for alt_model in MODELS_PRIORITY:
                if alt_model == getattr(chat, "_active_model_name", None):
                    continue
                try:
                    alt_chat = create_customer_chat(customer_id, preferred_model=alt_model)
                    if alt_chat:
                        res = alt_chat.send_message(message)
                        if res.text:
                            chat._active_model_name = alt_model
                            return res.text
                except Exception:
                    continue

    return _deterministic_booking_fallback(customer_id, message, chat)


# -----------------------------------
# Terminal Test
# -----------------------------------

if __name__ == "__main__":

    print()
    print("🏟️ SmartSports AI Customer Agent")
    print("=" * 45)

    customer_id = 1

    chat = create_customer_chat(
        customer_id
    )

    message = (
        "Find me a football slot in the evening "
        "under 1000 rupees."
    )

    print()
    print("Customer:")
    print(message)

    print()
    print("SmartSports AI:")

    answer = ask_customer_agent(
        chat=chat,
        message=message
    )

    print(answer)