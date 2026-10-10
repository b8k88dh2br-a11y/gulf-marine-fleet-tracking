from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import init_db, list_alerts, list_geofences, list_trucks

app = FastAPI(title="Gulf Marine Fleet Tracking", version="1.0.0")

# This file intentionally keeps the app definition simple.
# It is imported by uvicorn as `app.main:app`.

# Keep a second app instance for dashboard rendering if needed.
# It uses the same logic as the app object in the main file.

templates = Jinja2Templates(directory="app/templates")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    trucks = list_trucks()
    geofences = list_geofences()
    alerts = list_alerts(10)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "trucks": trucks, "geofences": geofences, "alerts": alerts},
    )


# Initialize database when the module is imported
init_db()
