import os
import json
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, ValidationError
from typing import Optional

app = FastAPI(
    title="Prime Event Rentals – Tool API",
    description="Tool endpoints for event equipment rental",
    version="1.0.0"
)

# -------------------------
# CONFIG
# -------------------------

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
# UTILS
# -------------------------

async def parse_body(request: Request, model: BaseModel):
    try:
        raw = await request.body()
        if not raw:
            raise HTTPException(status_code=400, detail="Empty request body")
        data = json.loads(raw.decode())
        return model(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())


# -------------------------
# HEALTH
# -------------------------

@app.get("/")
@app.get("")
def health():
    return {"status": "ok", "service": "Prime Event Rentals Tools"}


# -------------------------
# TOOL: CHECK AVAILABILITY
# -------------------------

@app.api_route(
    "/tools/check-availability",
    methods=["POST", "GET", "OPTIONS"]
)
@app.api_route(
    "/tools/check-availability/",
    methods=["POST", "GET", "OPTIONS"],
    include_in_schema=False
)
async def check_availability(request: Request):

    if request.method != "POST":
        return {
            "status": "ok",
            "note": "Use POST with a JSON body to check availability"
        }

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
# TOOL: GET UNIT PRICE
# -------------------------

@app.api_route(
    "/tools/get-price",
    methods=["POST", "GET", "OPTIONS"]
)
@app.api_route(
    "/tools/get-price/",
    methods=["POST", "GET", "OPTIONS"],
    include_in_schema=False
)
async def get_price(request: Request):

    if request.method != "POST":
        return {
            "status": "ok",
            "note": "Use POST with a JSON body to get pricing"
        }

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
# TOOL: CALCULATE PRICE
# -------------------------

@app.api_route(
    "/tools/calculate-price",
    methods=["POST", "GET", "OPTIONS"]
)
@app.api_route(
    "/tools/calculate-price/",
    methods=["POST", "GET", "OPTIONS"],
    include_in_schema=False
)
async def calculate_price(request: Request):

    if request.method != "POST":
        return {
            "status": "ok",
            "note": "Use POST with a JSON body to calculate price"
        }

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
# TOOL: CREATE BOOKING
# -------------------------

@app.api_route(
    "/tools/create-booking",
    methods=["POST", "GET", "OPTIONS"]
)
@app.api_route(
    "/tools/create-booking/",
    methods=["POST", "GET", "OPTIONS"],
    include_in_schema=False
)
async def create_booking(request: Request):

    if request.method != "POST":
        return {
            "status": "ok",
            "note": "Use POST with a JSON body to create a booking"
        }

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
# TOOL: HUMAN HANDOFF
# -------------------------

@app.api_route(
    "/tools/handoff",
    methods=["POST", "GET", "OPTIONS"]
)
@app.api_route(
    "/tools/handoff/",
    methods=["POST", "GET", "OPTIONS"],
    include_in_schema=False
)
async def human_handoff(request: Request):

    if request.method != "POST":
        return {
            "status": "ok",
            "note": "Use POST with a JSON body to request human handoff"
        }

    payload = await parse_body(request, HandoffRequest)

    return {
        "status": "received",
        "message": "A team member will contact you shortly.",
        "contact": {
            "name": payload.name,
            "phone": payload.phone
        }
    }
