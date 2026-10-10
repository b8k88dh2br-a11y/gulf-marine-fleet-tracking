from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.database import init_db, list_geofences, list_trucks, list_alerts, create_truck, create_geofence, get_truck, update_truck_location, create_alert
from app.services.email_service import send_manager_email

app = FastAPI(title="Gulf Marine Fleet Tracking", version="1.0.0")


class TruckCreate(BaseModel):
    name: str = Field(..., min_length=2)
    plate_number: str = Field(..., min_length=2)
    driver_name: str = Field(..., min_length=2)
    manager_email: Optional[str] = None


class GeofenceCreate(BaseModel):
    name: str = Field(..., min_length=2)
    latitude: float
    longitude: float
    radius_meters: float = 200.0


class TruckLocationUpdate(BaseModel):
    latitude: float
    longitude: float
    status: str = "IN_TRANSIT"


init_db()


@app.get("/")
async def root():
    return {
        "message": "Gulf Marine Fleet Tracking API is running",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/trucks")
async def get_trucks():
    return list_trucks()


@app.post("/trucks")
async def add_truck(payload: TruckCreate):
    truck = create_truck(payload.name, payload.plate_number, payload.driver_name, payload.manager_email)
    return {"message": "Truck created successfully", "truck": truck}


@app.get("/geofences")
async def get_geofences():
    return list_geofences()


@app.post("/geofences")
async def add_geofence(payload: GeofenceCreate):
    geofence = create_geofence(payload.name, payload.latitude, payload.longitude, payload.radius_meters)
    return {"message": "Geofence created successfully", "geofence": geofence}


@app.get("/alerts")
async def get_alerts():
    return list_alerts()


@app.post("/trucks/{truck_id}/location")
async def update_location(truck_id: int, payload: TruckLocationUpdate):
    truck = get_truck(truck_id)
    if truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")

    previous_status = truck["status"]
    previous_geofence = truck["last_geofence"]

    current_geofence = None
    geofences = list_geofences()
    for geofence in geofences:
        distance = haversine(payload.latitude, payload.longitude, geofence["latitude"], geofence["longitude"])
        if distance <= geofence["radius_meters"]:
            current_geofence = geofence["name"]
            break

    if payload.status.upper() in {"ARRIVED", "DEPARTED", "IN_TRANSIT", "IDLE"}:
        new_status = payload.status.upper()
    else:
        new_status = "IN_TRANSIT"

    if payload.status.upper() == "ARRIVED" and previous_status != "ARRIVED":
        subject = f"Gulf Marine Fleet - {truck['name']} has arrived"
        message = (
            f"Truck {truck['name']} ({truck['plate_number']}) has arrived at location "
            f"{payload.latitude}, {payload.longitude}. Driver: {truck['driver_name']}."
        )
        send_manager_email(subject, message, truck["manager_email"])

    if payload.status.upper() == "DEPARTED" and previous_status != "DEPARTED":
        subject = f"Gulf Marine Fleet - {truck['name']} has departed"
        message = (
            f"Truck {truck['name']} ({truck['plate_number']}) has departed from the location "
            f"{payload.latitude}, {payload.longitude}. Driver: {truck['driver_name']}."
        )
        send_manager_email(subject, message, truck["manager_email"])

    if current_geofence and previous_geofence != current_geofence:
        subject = f"Gulf Marine Fleet - {truck['name']} entered geofence: {current_geofence}"
        message = (
            f"Truck {truck['name']} entered geofence '{current_geofence}' at "
            f"{payload.latitude}, {payload.longitude}."
        )
        create_alert(
            truck_id=truck_id,
            truck_name=truck["name"],
            alert_type="GEOFENCE_ENTERED",
            message=message,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        send_manager_email(subject, message, truck["manager_email"])

    if previous_geofence and current_geofence is None and previous_geofence != current_geofence:
        subject = f"Gulf Marine Fleet - {truck['name']} left geofence: {previous_geofence}"
        message = (
            f"Truck {truck['name']} left geofence '{previous_geofence}' at "
            f"{payload.latitude}, {payload.longitude}."
        )
        create_alert(
            truck_id=truck_id,
            truck_name=truck["name"],
            alert_type="GEOFENCE_LEFT",
            message=message,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        send_manager_email(subject, message, truck["manager_email"])

    update_truck_location(
        truck_id=truck_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=new_status,
        last_geofence=current_geofence,
    )

    return {
        "message": "Truck location updated successfully",
        "truck": get_truck(truck_id),
    }


# Helper function for distance calculation

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    earth_radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius * c
