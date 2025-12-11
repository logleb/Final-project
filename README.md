# Trip Reservation System

Flask app for managing bus reservations. Uses the provided `reservations.db` and `schema.sql`.

## Setup

1. Create a virtualenv (optional): `python3 -m venv .venv && source .venv/bin/activate`
2. Install deps: `pip install -r requirements.txt`
3. Run the app: `python app.py`
4. Open the app at `http://127.0.0.1:5000`

The SQLite file already includes sample admins (`admin1`/`12345`, etc.) and some seeded reservations.

## Features

- Main menu with seating chart
- Reserve seats with generated reservation code
- Admin login to view chart, total sales, and remove reservations
- Uses SQLAlchemy models tied to the provided schema
