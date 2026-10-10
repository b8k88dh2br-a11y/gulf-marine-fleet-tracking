# Gulf Marine Fleet Tracking

A fleet monitoring system for Gulf Marine. It tracks trucks, monitor geofences, logs alerts, and sends email notifications to the manager and secondary manager when a truck arrives, departs, or enters/exits a defined zone.

## Features
- Truck registration and status tracking
- GPS location updates
- Geofence monitoring for entry/exit events
- Manager email alerting
- Secondary email alerting support
- SQLite database storage
- Dashboard for trucks and alerts

## Tech Stack
- Python 3.11+
- FastAPI
- SQLite
- Jinja2 templates
- Gmail SMTP

## Run locally

1. Clone the repo:
   ```bash
   git clone https://github.com/b8k88dh2br-a11y/gulf-marine-fleet-tracking.git
   cd gulf-marine-fleet-tracking
   ```

2. Create virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create `.env` from example:
   ```bash
   cp .env.example .env
   ```

4. Update `.env` with valid Gmail credentials:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   MANAGER_EMAIL=manager@gulfmarine.sa
   SECONDARY_MANAGER_EMAIL=operations@gulfmarine.sa
   ```

5. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Visit:
   - http://127.0.0.1:8000/docs
   - http://127.0.0.1:8000/dashboard

## Example requests

Create a truck:
```bash
curl -X POST "http://127.0.0.1:8000/trucks" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Truck-01",
    "plate_number":"KSA-1800",
    "driver_name":"Ali Hassan",
    "manager_email":"manager@gulfmarine.sa",
    "secondary_email":"operations@gulfmarine.sa"
  }'
```

Create geofence:
```bash
curl -X POST "http://127.0.0.1:8000/geofences" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Dammam Port",
    "latitude":26.4207,
    "longitude":50.0888,
    "radius_meters":200
  }'
```

Update GPS:
```bash
curl -X POST "http://127.0.0.1:8000/trucks/1/location" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude":26.4207,
    "longitude":50.0888,
    "status":"ARRIVED"
  }'
```

## Gmail setup
To send real emails through Gmail, generate an App Password in your Google account and use it in `.env`.

## Notes
This project is a working prototype for fleet tracking and alerting and is ready for enhancement with real GPS feed integration, map visualization, and more advanced admin features.
