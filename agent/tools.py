"""Deterministic business rules over fictional, fixed-date demo data."""
from datetime import date
from uuid import uuid4
from langchain.tools import tool

DEMO_DATE = date(2026, 9, 25)
RETURN_POLICY_DAYS = 30
ORDERS = {
    "HT-1001": {"item": "Wireless headphones", "status": "delivered", "delivered_on": "2026-09-05", "price": 79.99},
    "HT-1002": {"item": "Mechanical keyboard", "status": "shipped", "eta": "2026-09-28", "price": 129.00},
    "HT-1003": {"item": "USB-C dock", "status": "processing", "price": 59.50},
    "HT-1004": {"item": "Webcam", "status": "delivered", "delivered_on": "2026-08-01", "price": 49.00},
}
FAQ = {
    "shipping": "Standard shipping takes 3–5 business days. Orders over $50 ship free.",
    "return": "Items can be returned within 30 days of delivery for a full refund.",
    "warranty": "All electronics include a one-year manufacturer warranty.",
    "hours": "Support hours are Monday–Friday, 9am–6pm ET.",
}

@tool
def look_up_order(order_id: str) -> dict:
    """Look up a fictional order by ID, such as HT-1001."""
    order_id = order_id.strip().upper()
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": "Order not found. Ask the customer to double-check the ID."}
    return {"order_id": order_id, "demo_date": DEMO_DATE.isoformat(), **order}

@tool
def check_return_eligibility(order_id: str) -> dict:
    """Check an order against the 30-day return policy using the fixed demo date."""
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"eligible": False, "reason": "Order not found."}
    if order["status"] != "delivered":
        return {"eligible": False, "reason": "Not delivered; the return window has not started."}
    days = (DEMO_DATE - date.fromisoformat(order["delivered_on"])).days
    return {"eligible": 0 <= days <= RETURN_POLICY_DAYS, "days_since_delivery": days,
            "window_days": RETURN_POLICY_DAYS, "demo_date": DEMO_DATE.isoformat()}

@tool
def search_faq(question: str) -> dict:
    """Find policy answers by keyword: shipping, returns, warranty, or support hours."""
    query = question.lower()
    aliases = {"shipping": ("ship", "delivery"), "return": ("return", "refund"),
               "warranty": ("warranty", "guarantee"), "hours": ("hour", "open", "support")}
    matches = {topic: FAQ[topic] for topic, words in aliases.items() if any(w in query for w in words)}
    return matches or {"message": "No matching policy. Available topics: shipping, returns, warranty, hours."}

@tool
def escalate_to_human(reason: str) -> dict:
    """Create a simulated escalation receipt in the conversation; no human is contacted."""
    return {"ticket_id": "ESC-" + uuid4().hex[:12], "reason": reason,
            "status": "simulated", "notice": "Demo only. No human has been contacted."}

TOOLS = [look_up_order, check_return_eligibility, search_faq, escalate_to_human]
