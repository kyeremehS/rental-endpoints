import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Prime Event Rentals – Tool API",
    description="Tool endpoints for event equipment rental",
    version="1.0.0"
)

# -------------------------
# SIMPLE API KEY SECURITY
# -------------------------

API_KEY = os.environ.get("API_KEY", "dev-key")

def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# -------------------------
# MOCK DATA (replace later)
# -------------------------

EQUIPMENT_DB = {
    "chairs": {"price": 5, "available": 300},
    "tables": {"price": 15, "available": 80},
    "canopy": {"price": 250, "available": 10},
    "sound_system": {"price": 400, "available": 5},
    "generator": {"price": 350, "available": 4}
}

DELIVERY_FEE = 100


# -------------------------
# MODELS
# -------------------------

class AvailabilityRequest(BaseModel):
    item: str
    quantity: int
    event_date: str


class PriceRequest(BaseModel):
    item: str
    quantity: int
    days: int


class BookingRequest(BaseModel):
    customer_name: str
    phone: str
    item: str
    quantity: int
    event_date: str
    location: str


class HandoffRequest(BaseModel):
    name: str
    phone: str
    message: Optional[str] = None


# -------------------------
# HEALTH CHECK
# -------------------------

@app.get("/")
def health():
    return {"status": "ok", "service": "Prime Event Rentals Tools"}


# -------------------------
# TOOL: CHECK AVAILABILITY
# -------------------------

@app.post("/tools/check-availability")
def check_availability(
    payload: AvailabilityRequest,
    x_api_key: str = Header(...)
):
    verify_key(x_api_key)

    item = payload.item.lower()

    if item not in EQUIPMENT_DB:
        return {
            "available": False,
            "reason": "Item not found"
        }

    available_qty = EQUIPMENT_DB[item]["available"]

    return {
        "item": item,
        "requested_quantity": payload.quantity,
        "available": payload.quantity <= available_qty,
        "available_quantity": available_qty
    }


# -------------------------
# TOOL: GET UNIT PRICE
# -------------------------

@app.post("/tools/get-price")
def get_price(
    payload: PriceRequest,
    x_api_key: str = Header(...)
):
    verify_key(x_api_key)

    item = payload.item.lower()

    if item not in EQUIPMENT_DB:
        raise HTTPException(status_code=404, detail="Item not found")

    unit_price = EQUIPMENT_DB[item]["price"]

    return {
        "item": item,
        "unit_price_per_day": unit_price,
        "currency": "GHS"
    }


# -------------------------
# TOOL: CALCULATE TOTAL COST
# -------------------------

@app.post("/tools/calculate-price")
def calculate_price(
    payload: PriceRequest,
    x_api_key: str = Header(...)
):
    verify_key(x_api_key)

    item = payload.item.lower()

    if item not in EQUIPMENT_DB:
        raise HTTPException(status_code=404, detail="Item not found")

    unit_price = EQUIPMENT_DB[item]["price"]
    subtotal = unit_price * payload.quantity * payload.days
    total = subtotal + DELIVERY_FEE

    return {
        "item": item,
        "quantity": payload.quantity,
        "days": payload.days,
        "unit_price": unit_price,
        "subtotal": subtotal,
        "delivery_fee": DELIVERY_FEE,
        "total_price": total,
        "currency": "GHS"
    }


# -------------------------
# TOOL: CREATE BOOKING REQUEST
# (NOT auto-confirmed)
# -------------------------

@app.post("/tools/create-booking")
def create_booking(
    payload: BookingRequest,
    x_api_key: str = Header(...)
):
    verify_key(x_api_key)

    item = payload.item.lower()

    if item not in EQUIPMENT_DB:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "status": "pending",
        "message": "Booking request received. Availability and pricing will be confirmed.",
        "booking_details": payload.dict()
    }


# -------------------------
# TOOL: HUMAN HANDOFF
# -------------------------

@app.post("/tools/handoff")
def human_handoff(
    payload: HandoffRequest,
    x_api_key: str = Header(...)
):
    verify_key(x_api_key)

    return {
        "status": "received",
        "message": "A team member will contact you shortly.",
        "contact": {
            "name": payload.name,
            "phone": payload.phone
        }
    }
