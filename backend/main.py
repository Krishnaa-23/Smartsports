"""
SmartSports Production REST API (FastAPI)
Exposes endpoints for Slots, Bookings, AI Customer Agent, Dynamic Pricing, and Revenue Optimization.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from utils.slot_optimizer import get_available_slots, analyze_slot
from utils.dynamic_pricing import get_slot_dynamic_price
from agent.revenue_agent import optimize_slot_revenue
from agent.customer_agent import (
    create_customer_chat,
    ask_customer_agent
)
from agent.booking_tools import book_slot
from database.database import (
    get_customer_available_slots,
    create_booking,
    apply_dynamic_price,
    get_dynamic_price_history,
    dispatch_notifications,
    get_notification_history,
    get_customer_bookings,
    cancel_booking,
    save_agent_decision,
    get_agent_decisions
)
from analytics.demand_analysis import (
    get_overall_fill_rate,
    get_fill_rate_by_court,
    get_fill_rate_by_time
)
from analytics.revenue_analysis import (
    get_revenue_by_court,
    get_revenue_by_time
)

# Initialize FastAPI App
app = FastAPI(
    title="SmartSports Revenue & Booking API",
    version="2.0.0",
    description="Agentic AI Revenue Management and Sports Facility Booking Platform"
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory customer chat sessions
customer_chats: Dict[int, Any] = {}

# ---------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------

class BookingRequest(BaseModel):
    customer_id: int
    slot_id: int
    amount_paid: Optional[float] = None

class DynamicPriceApprovalRequest(BaseModel):
    slot_id: int
    approved_price: float
    base_price: float
    suggested_price: float
    adjustment_percentage: float
    demand: str
    status: str = "Approved"

class RevenueStrategyExecutionRequest(BaseModel):
    slot_id: int
    suggested_price: float
    base_price: float
    adjustment_percentage: float
    demand_level: str
    action: str
    reasoning: str
    offer_message: str
    target_customers: List[Dict[str, Any]]

class ChatMessageRequest(BaseModel):
    customer_id: int
    message: str


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "SmartSports Backend API",
        "status": "online",
        "frontend_app": "http://127.0.0.1:5173",
        "api_documentation": "http://127.0.0.1:8000/docs",
        "note": "Open http://127.0.0.1:5173 in your browser to view the SmartSports Web Application."
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "SmartSports API v2.0"}


@app.get("/api/slots")
def get_slots(
    sport: Optional[str] = None,
    date: Optional[str] = None,
    preferred_time: Optional[str] = None
):
    """Fetch available slots for customers with optional sport, date, and preferred_time filters."""
    slots = get_customer_available_slots(sport=sport, slot_date=date)
    results = [
        {
            "slot_id": s[0],
            "court_name": s[1],
            "sport": s[2],
            "date": s[3],
            "start_time": s[4],
            "end_time": s[5],
            "base_price": s[6]
        }
        for s in slots
    ]

    if preferred_time and preferred_time.lower() != "all":
        filtered = []
        for s in results:
            hour = int(s["start_time"].split(":")[0])
            if preferred_time.lower() == "morning" and 6 <= hour < 12:
                filtered.append(s)
            elif preferred_time.lower() == "afternoon" and 12 <= hour < 17:
                filtered.append(s)
            elif preferred_time.lower() == "evening" and 17 <= hour <= 23:
                filtered.append(s)
        return filtered

    return results


@app.get("/api/admin/slots")
def get_admin_available_slots():
    """Fetch future vacant slots for facility administration."""
    slots_df = get_available_slots()
    if slots_df.empty:
        return []
    return slots_df.to_dict(orient="records")


@app.post("/api/bookings")
def make_booking(req: BookingRequest):
    """Book a slot transactionally."""
    if req.amount_paid is None:
        # Fetch current slot price
        slots_df = get_available_slots()
        matching = slots_df[slots_df["slot_id"] == req.slot_id]
        if matching.empty:
            raise HTTPException(status_code=404, detail="Slot not found or already booked.")
        req.amount_paid = float(matching.iloc[0]["base_price"])

    success, message = create_booking(
        customer_id=req.customer_id,
        slot_id=req.slot_id,
        amount_paid=req.amount_paid
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message, "slot_id": req.slot_id}


@app.get("/api/customers/{customer_id}/bookings")
def get_customer_booking_history(customer_id: int):
    """Get all past and active bookings for a customer."""
    bookings, cols = get_customer_bookings(customer_id)
    return [
        {
            "booking_id": b[0],
            "slot_id": b[1],
            "court_name": b[2],
            "sport": b[3],
            "date": b[4],
            "start_time": b[5],
            "end_time": b[6],
            "amount_paid": b[7],
            "status": b[8],
            "booking_date": b[9]
        }
        for b in bookings
    ]


@app.delete("/api/bookings/{booking_id}")
def cancel_customer_booking(booking_id: int):
    """Cancel a booking and free up the slot."""
    success, message = cancel_booking(booking_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@app.get("/api/pricing/recommendations")
def get_pricing_recommendations():
    """Calculate real-time dynamic pricing for all future vacant slots."""
    slots_df = get_available_slots()
    if slots_df.empty:
        return []

    recommendations = []
    for _, slot in slots_df.iterrows():
        dyn = get_slot_dynamic_price(slot["slot_id"])
        if dyn:
            recommendations.append(dyn)
    return recommendations


@app.post("/api/pricing/approve")
def approve_price(req: DynamicPriceApprovalRequest):
    """Approve or customize a dynamic slot price."""
    success, message = apply_dynamic_price(
        slot_id=req.slot_id,
        approved_price=req.approved_price,
        base_price=req.base_price,
        suggested_price=req.suggested_price,
        adjustment_percentage=req.adjustment_percentage,
        demand=req.demand,
        status=req.status
    )
    return {"success": success, "message": message}


@app.get("/api/pricing/history")
def get_pricing_audit_log():
    """Retrieve historical dynamic pricing approvals."""
    records, cols = get_dynamic_price_history()
    return [
        {
            "price_id": r[0],
            "slot_id": r[1],
            "court_name": r[2],
            "sport": r[3],
            "date": r[4],
            "start_time": r[5],
            "end_time": r[6],
            "base_price": r[7],
            "suggested_price": r[8],
            "approved_price": r[9],
            "adjustment_percentage": r[10],
            "demand": r[11],
            "status": r[12],
            "created_at": r[13]
        }
        for r in records
    ]


@app.get("/api/revenue/optimize/{slot_id}")
def run_revenue_optimization(slot_id: int):
    """Run the Unified Revenue Optimization Agent on a slot."""
    slots_df = get_available_slots()
    matching = slots_df[slots_df["slot_id"] == slot_id]
    if matching.empty:
        raise HTTPException(status_code=404, detail="Slot not found or not vacant.")

    result = optimize_slot_revenue(matching.iloc[0])
    return result


@app.post("/api/revenue/execute")
def execute_revenue_strategy(req: RevenueStrategyExecutionRequest):
    """One-click execution of a revenue strategy."""
    # 1. Apply price
    apply_dynamic_price(
        slot_id=req.slot_id,
        approved_price=req.suggested_price,
        base_price=req.base_price,
        suggested_price=req.suggested_price,
        adjustment_percentage=req.adjustment_percentage,
        demand=req.demand_level,
        status="Approved"
    )

    # 2. Save decision
    save_agent_decision(
        slot_id=req.slot_id,
        decision=req.action,
        discount_percentage=abs(req.adjustment_percentage),
        reason=req.reasoning,
        offer_message=req.offer_message
    )

    # 3. Dispatch notifications
    notif_count = dispatch_notifications(
        slot_id=req.slot_id,
        target_customers=req.target_customers,
        message=req.offer_message
    )

    return {
        "success": True,
        "message": f"Strategy executed! Dynamic price updated to ₹{req.suggested_price:,.0f} and {notif_count} notifications dispatched.",
        "notifications_dispatched": notif_count
    }


@app.get("/api/notifications/history")
def get_notification_log():
    """Retrieve logged notification dispatches."""
    records, cols = get_notification_history()
    return [
        {
            "notification_id": r[0],
            "slot_id": r[1],
            "court_name": r[2],
            "sport": r[3],
            "date": r[4],
            "start_time": r[5],
            "end_time": r[6],
            "recipient_name": r[7],
            "channel": r[8],
            "message": r[9],
            "sent_at": r[10]
        }
        for r in records
    ]


@app.post("/api/chat")
def chat_with_agent(req: ChatMessageRequest):
    """Customer chat with Gemini AI Agent with zero-crash fallback."""
    if req.customer_id not in customer_chats:
        customer_chats[req.customer_id] = create_customer_chat(req.customer_id)

    chat_session = customer_chats[req.customer_id]
    response = ask_customer_agent(
        chat=chat_session,
        message=req.message,
        customer_id=req.customer_id
    )
    return {"reply": response, "response": response}


@app.get("/api/analytics/summary")
def get_analytics_summary():
    """Facility analytics summary."""
    overall_fill_rate = get_overall_fill_rate()
    revenue_by_court_df = get_revenue_by_court()
    fill_rate_court_df = get_fill_rate_by_court()
    fill_rate_time_df = get_fill_rate_by_time()
    revenue_time_df = get_revenue_by_time()

    return {
        "overall_fill_rate": overall_fill_rate,
        "total_revenue": float(revenue_by_court_df["revenue"].sum()),
        "revenue_by_court": revenue_by_court_df.to_dict(orient="records"),
        "fill_rate_by_court": fill_rate_court_df.to_dict(orient="records"),
        "fill_rate_by_time": fill_rate_time_df.to_dict(orient="records"),
        "revenue_by_time": revenue_time_df.to_dict(orient="records")
    }
