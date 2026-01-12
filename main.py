import os
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError
from typing import Optional

app = FastAPI(
    title="Prime Event Rentals – Tool API",
    description="Tool endpoints for event equipment rental",
    version="1.0.0"
)

API_KEY = os.environ.get("API_KEY", "dev-key")

# -------------------------
# MOCK DATA
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
# UTIL: SAFE BODY PARSER
# -------------------------

async def parse_body(request: Request, model: BaseModel):
    try:
        raw = await request.body()
        data = json.loads(raw.decode())
        return model(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())


# -------------------------
# HEALTH CHECK
# -------------------------

@app.get("/")
def health():
    return {"status": "ok", "service": "Prime Event Rentals Tools"}


# -------------------------
# CHECK AVAILABILITY
# -------------------------

@app.post("/tools/check-availability")
async def check_availability(request: Request):
    payload = await parse_body(request, AvailabilityRequest)
    item = payload.item.lower()

    if item not in EQUIPMENT_DB:
        return {"available": False, "reason": "Item not found"}

    available_qty = EQUIPMENT_DB[item]["available"]

    return {
        "item": item,
        "requested_quantity": payload.quantity,
        "available": payload.quantity <= available_qty,
        "available_quantity": available_qty
    }


# -------------------------
# GET UNIT PRICE
# -------------------------

@app.post("/tools/get-price")
async def get_price(request: Request):
    payload = await parse_body(request, PriceRequest)
    item = payload.item.lower()

    if item not in EQUIPMENT_DB:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "item": item,
        "unit_price_per_day": EQUIPMENT_DB[item]["price"],
        "currency": "GHS"
    }


# -------------------------
# CALCULATE TOTAL COST
# -------------------------

@app.post("/tools/calculate-price")
async def calculate_price(request: Request):
    payload = await parse_body(request, PriceRequest)
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
# CREATE BOOKING
# -------------------------

@app.post("/tools/create-booking")
async def create_booking(request: Request):
    payload = await parse_body(request, BookingRequest)
    item = payload.item.lower()

    if item not in EQUIPMENT_DB:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "status": "pending",
        "message": "Booking request received. Availability and pricing will be confirmed.",
        "booking_details": payload.dict()
    }


# -------------------------
# HUMAN HANDOFF
# -------------------------

@app.post("/tools/handoff")
async def human_handoff(request: Request):
    payload = await parse_body(request, HandoffRequest)

    return {
        "status": "received",
        "message": "A team member will contact you shortly.",
        "contact": {
            "name": payload.name,
            "phone": payload.phone
        }
    }
