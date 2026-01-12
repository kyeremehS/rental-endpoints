import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Prime Event Rentals – Tool API",
    description="External-ready API for event equipment rental",
    version="1.1.0"
)

# -------------------------
# 1. CORS CONFIGURATION (Crucial for External Access)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. For production, replace ["*"] with ["https://your-site.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],
)

# -------------------------
# MOCK DATA & CONFIG
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
# ENDPOINTS
# -------------------------

@app.get("/")
def health():
    return {"status": "ok", "service": "Prime Event Rentals Tools"}

@app.post("/tools/check-availability")
async def check_availability(payload: AvailabilityRequest):
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

@app.post("/tools/calculate-price")
async def calculate_price(payload: PriceRequest):
    item = payload.item.lower()
    if item not in EQUIPMENT_DB:
        return {"available": False, "reason": "Item not found"}

    unit_price = EQUIPMENT_DB[item]["price"]
    subtotal = unit_price * payload.quantity * payload.days
    total = subtotal + DELIVERY_FEE

    return {
        "item": item,
        "total_price": total,
        "currency": "GHS",
        "breakdown": {"subtotal": subtotal, "delivery": DELIVERY_FEE}
    }

@app.post("/tools/create-booking")
async def create_booking(payload: BookingRequest):
    item = payload.item.lower()
    if item not in EQUIPMENT_DB:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "status": "pending",
        "message": "Booking received externally.",
        "booking_details": payload.dict()
    }

@app.post("/tools/handoff")
async def human_handoff(payload: HandoffRequest):
    return {
        "status": "received",
        "message": f"Team member will contact {payload.name} shortly."
    }
