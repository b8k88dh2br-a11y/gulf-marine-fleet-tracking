from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.database import (
    create_alert,
    create_geofence,
    create_truck,
    get_truck,
    init_db,
    list_alerts,
    list_geofences,
    list_trucks,
    update_truck_location,
)
from app.services.email_service import send_manager_email

app = FastAPI(title="Gulf Marine Fleet Tracking", version="1.0.0")


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math

    earth_radius = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius * c


templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


class TruckCreate(BaseModel):
    name: str = Field(..., min_length=2)
    plate_number: str = Field(..., min_length=2)
    driver_name: str = Field(..., min_length=2)
    manager_email: Optional[str] = None
    secondary_email: Optional[str] = None


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


@app.get("/trucks/{truck_id}")
async def get_truck_by_id(truck_id: int):
    truck = get_truck(truck_id)
    if truck is None:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck


@app.post("/trucks")
async def add_truck(payload: TruckCreate):
    truck = create_truck(
        payload.name,
        payload.plate_number,
        payload.driver_name,
        payload.manager_email,
        payload.secondary_email,
    )
    if truck is None:
        raise HTTPException(status_code=400, detail="Unable to create truck")
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

    for geofence in list_geofences():
        distance = haversine(payload.latitude, payload.longitude, geofence["latitude"], geofence["longitude"])
        if distance <= geofence["radius_meters"]:
            current_geofence = geofence["name"]
            break

    normalized_status = payload.status.upper()
    if normalized_status not in {"ARRIVED", "DEPARTED", "IN_TRANSIT", "IDLE"}:
        normalized_status = "IN_TRANSIT"

    if normalized_status == "ARRIVED" and previous_status != "ARRIVED":
        subject = f"Gulf Marine Fleet - {truck['name']} has arrived"
        body = (
            f"Truck {truck['name']} ({truck['plate_number']}) has arrived at location "
            f"{payload.latitude}, {payload.longitude}. Driver: {truck['driver_name']}."
        )
        send_manager_email(subject, body, truck["manager_email"], truck.get("secondary_email"))

    if normalized_status == "DEPARTED" and previous_status != "DEPARTED":
        subject = f"Gulf Marine Fleet - {truck['name']} has departed"
        body = (
            f"Truck {truck['name']} ({truck['plate_number']}) has departed from location "
            f"{payload.latitude}, {payload.longitude}. Driver: {truck['driver_name']}."
        )
        send_manager_email(subject, body, truck["manager_email"], truck.get("secondary_email"))

    if current_geofence and previous_geofence != current_geofence:
        subject = f"Gulf Marine Fleet - {truck['name']} entered geofence: {current_geofence}"
        body = (
            f"Truck {truck['name']} entered geofence '{current_geofence}' at "
            f"{payload.latitude}, {payload.longitude}."
        )
        create_alert(
            truck_id=truck_id,
            truck_name=truck["name"],
            alert_type="GEOFENCE_ENTERED",
            message=body,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        send_manager_email(subject, body, truck["manager_email"], truck.get("secondary_email"))

    if previous_geofence and current_geofence is None and previous_geofence != current_geofence:
        subject = f"Gulf Marine Fleet - {truck['name']} left geofence: {previous_geofence}"
        body = (
            f"Truck {truck['name']} left geofence '{previous_geofence}' at "
            f"{payload.latitude}, {payload.longitude}."
        )
        create_alert(
            truck_id=truck_id,
            truck_name=truck["name"],
            alert_type="GEOFENCE_LEFT",
            message=body,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        send_manager_email(subject, body, truck["manager_email"], truck.get("secondary_email"))

    truck = update_truck_location(
        truck_id=truck_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=normalized_status,
        last_geofence=current_geofence,
    )

    return {"message": "Truck location updated successfully", "truck": truck}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    trucks = list_trucks()
    geofences = list_geofences()
    alerts = list_alerts(10)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "trucks": trucks, "geofences": geofences, "alerts": alerts},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
