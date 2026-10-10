# Gulf Marine Fleet Tracking

A simple fleet monitoring system for Gulf Marine. It tracks truck locations, monitors geofences, logs alerts, and sends email notifications to the manager when events occur.

Features:
- Truck registration and status tracking
- GPS update endpoint for latitude/longitude
- Geofence monitoring (entry/exit alerts)
- Email alerts for manager on arrival, departure, and geofence events
- SQLite database for local persistence
- Basic dashboard to view trucks, geofences, and alerts

Project layout:
- `app/main.py` — FastAPI app
- `app/database.py` — SQLite helpers
- `app/services/email_service.py` — email sending logic
- `app/templates/index.html` — simple dashboard UI

Quick start:

1. Clone the project:
   ```bash
   git clone https://github.com/b8k88dh2br-a11y/gulf-marine-fleet-tracking.git
   cd gulf-marine-fleet-tracking
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Update `.env` with your SMTP credentials and manager email.

5. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open the dashboard:
   - http://127.0.0.1:8000/dashboard
   - API docs: http://127.0.0.1:8000/docs

Example API flow:

- Create a truck:
  ```bash
  curl -X POST "http://127.0.0.1:8000/trucks" \
    -H "Content-Type: application/json" \
    -d '{"name":"Truck-01","plate_number":"KSA-2781","driver_name":"Ali Hassan","manager_email":"manager@gulfmarine.sa"}'
  ```

- Create a geofence:
  ```bash
  curl -X POST "http://127.0.0.1:8000/geofences" \
    -H "Content-Type: application/json" \
    -d '{"name":"Dammam Port","latitude":26.4207,"longitude":50.0888,"radius_meters":200}'
  ```

- Update truck location:
  ```bash
  curl -X POST "http://127.0.0.1:8000/trucks/1/location" \
    -H "Content-Type: application/json" \
    -d '{"latitude":26.4207,"longitude":50.0888,"status":"ARRIVED"}'
  ```

Email sending:
- The system uses Gmail SMTP by default.
- If you use Gmail, generate an App Password in your Google account and set it in `.env`.
- For testing, a manager email can be supplied per truck or in the main `.env` file.

Notes:
- This project is intentionally simple and ready for demo/learning use.
- It is suitable for a prototype and can later be expanded with a real GPS device API, job tracking, and a proper frontend.
