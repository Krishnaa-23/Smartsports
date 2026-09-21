-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    customer_type TEXT,
    booking_frequency INTEGER DEFAULT 0,
    last_booking_date TEXT
);


-- Sports courts / turfs
CREATE TABLE IF NOT EXISTS courts (
    court_id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_name TEXT NOT NULL,
    sport TEXT NOT NULL,
    hourly_price REAL NOT NULL
);


-- Available booking slots
CREATE TABLE IF NOT EXISTS slots (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_id INTEGER NOT NULL,
    slot_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT DEFAULT 'Available',
    base_price REAL NOT NULL,

    FOREIGN KEY (court_id) REFERENCES courts(court_id)
);


-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    booking_date TEXT NOT NULL,
    amount_paid REAL DEFAULT 0,
    status TEXT DEFAULT 'Confirmed',

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (slot_id) REFERENCES slots(slot_id)
);


-- AI agent decisions
CREATE TABLE IF NOT EXISTS agent_decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL,
    decision TEXT NOT NULL,
    discount_percentage REAL DEFAULT 0,
    reason TEXT,
    offer_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (slot_id) REFERENCES slots(slot_id)
);


-- Dynamic pricing adjustments and approval audit log
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
);


-- Outbound notifications and customer dispatch log
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
);