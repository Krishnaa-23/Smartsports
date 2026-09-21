import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path


# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Output files
CUSTOMERS_FILE = BASE_DIR / "data" / "customers.csv"
BOOKINGS_FILE = BASE_DIR / "data" / "bookings.csv"
SLOTS_FILE = BASE_DIR / "data" / "slots.csv"


random.seed(42)


# -----------------------------
# 1. Generate Customers
# -----------------------------

customers = []

names = [
    "Arjun Nair", "Rahul Menon", "Vishnu Kumar", "Adithya Raj",
    "Neeraj S", "Akshay Thomas", "Anand Krishnan", "Sanjay P",
    "Manu Joseph", "Abhinav K", "Joel Mathew", "Nikhil Das",
    "Farhan Ali", "Rohan B", "Kiran Mohan", "Akhil Raj",
    "Sreehari V", "Vivek Kumar", "Naveen P", "Rishabh S",
    "Amal Joseph", "Hari Krishnan", "Jithin M", "Anoop S",
    "Siddharth R", "Kevin Thomas", "Rakesh P", "Midhun K",
    "Shyam Das", "Gokul N"
]

customer_types = ["Regular", "Occasional", "Inactive"]

for i, name in enumerate(names, start=1):

    customer_type = random.choices(
        customer_types,
        weights=[50, 35, 15]
    )[0]

    if customer_type == "Regular":
        frequency = random.randint(8, 20)
    elif customer_type == "Occasional":
        frequency = random.randint(3, 7)
    else:
        frequency = random.randint(0, 2)

    last_booking = datetime(2026, 9, 15) - timedelta(
        days=random.randint(1, 60)
    )

    customers.append({
        "customer_id": i,
        "name": name,
        "email": f"{name.lower().replace(' ', '.')}@gmail.com",
        "phone": f"98765{43210 + i}",
        "customer_type": customer_type,
        "booking_frequency": frequency,
        "last_booking_date": last_booking.strftime("%Y-%m-%d")
    })


customers_df = pd.DataFrame(customers)
customers_df.to_csv(CUSTOMERS_FILE, index=False)


# -----------------------------
# 2. Generate Slots
# -----------------------------

courts = [
    (1, "Turf 1", "Football", 1200),
    (2, "Court 2", "Badminton", 500),
    (3, "Turf 2", "Football", 900)
]

slots = []
slot_id = 1

start_date = datetime(2026, 8, 1)
end_date = datetime(2026, 9, 30)

current_date = start_date

while current_date <= end_date:

    # Comprehensive operating hours (Morning, Afternoon, Evening)
    time_slots = [
        ("06:00", "07:00"),
        ("07:00", "08:00"),
        ("08:00", "09:00"),
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("11:00", "12:00"),
        ("13:00", "14:00"),
        ("14:00", "15:00"),
        ("15:00", "16:00"),
        ("16:00", "17:00"),
        ("17:00", "18:00"),
        ("18:00", "19:00"),
        ("19:00", "20:00"),
        ("20:00", "21:00"),
        ("21:00", "22:00")
    ]

    for court_id, court_name, sport, price in courts:

        for start_time, end_time in time_slots:

            hour = int(start_time.split(":")[0])

            # Balanced realistic booking distributions ensuring ample availability across all periods
            if 13 <= hour < 17:
                # Afternoon: off-peak (approx 35% booked)
                booking_probability = 0.35
            elif 6 <= hour < 12:
                # Morning: moderate (approx 45% booked)
                booking_probability = 0.45
            else:
                # Evening: popular (approx 55% booked, leaving 45% available)
                booking_probability = 0.55

            is_booked = random.random() < booking_probability

            status = "Booked" if is_booked else "Available"

            slots.append({
                "slot_id": slot_id,
                "court_id": court_id,
                "slot_date": current_date.strftime("%Y-%m-%d"),
                "start_time": start_time,
                "end_time": end_time,
                "status": status,
                "base_price": price
            })

            slot_id += 1

    current_date += timedelta(days=1)


slots_df = pd.DataFrame(slots)
slots_df.to_csv(SLOTS_FILE, index=False)


# -----------------------------
# 3. Generate Bookings
# -----------------------------

booked_slots = slots_df[slots_df["status"] == "Booked"]

bookings = []
booking_id = 1

today_str = "2026-09-21"

for _, slot in booked_slots.iterrows():

    slot_date = slot["slot_date"]

    # For future slots (>= today), assign exclusively to other customers (2 to 30)
    # This keeps Customer #1 (the active demo user) clean so they only see bookings they actually make!
    if slot_date >= today_str:
        customer_id = random.randint(2, len(customers))
    else:
        customer_id = random.randint(1, len(customers))

    bookings.append({
        "booking_id": booking_id,
        "customer_id": customer_id,
        "slot_id": int(slot["slot_id"]),
        "booking_date": slot["slot_date"],
        "amount_paid": slot["base_price"],
        "status": "Confirmed"
    })

    booking_id += 1


bookings_df = pd.DataFrame(bookings)
bookings_df.to_csv(BOOKINGS_FILE, index=False)


print("Realistic sports facility data generated successfully!")
print(f"Customers: {len(customers_df)}")
print(f"Slots: {len(slots_df)}")
print(f"Bookings: {len(bookings_df)}")