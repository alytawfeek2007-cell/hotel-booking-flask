# Hotel Booking App

A full-stack hotel reservation system built with Flask, ported and extended from an earlier Java (Swing/JavaFX) academic project into a deployable web application.

**Live demo:** https://hotel-booking-flask-x4rv.onrender.com
**Source:** https://github.com/alytawfeek2007-cell/hotel-booking-flask

> Note: the free hosting tier used for this demo may take up to 50 seconds to "wake up" after inactivity — this is a known limitation of free-tier hosting, not the app itself.

## What it does

- Guests can register, log in, browse and filter available rooms, book a room, view their own bookings, and cancel a booking
- Admins have a separate dashboard: view all bookings and their status (active/cancelled), see total bookings and the most-booked room type, free up a room, or book a room on a guest's behalf (creating a new guest account on the fly if needed)
- Email confirmation on booking (enabled locally; disabled on this free-tier host, see below)

## Tech stack

Python, Flask, SQLite, Jinja2, Flask-Mail, Werkzeug (password hashing), HTML/CSS. Deployed on Render with Gunicorn.

## Notable design decisions

- **Password hashing**, not plain text or reversible encryption (`werkzeug.security`)
- **Role-based access control** — guest and admin routes are enforced server-side, not just hidden in the UI
- **Race condition mitigation** on booking — availability check and update happen in a single atomic SQL statement (`UPDATE ... WHERE isAvailable = 1`) instead of a separate read-then-write, preventing two users from booking the same room simultaneously
- **Booking status history** (active/cancelled) instead of hard-deleting cancelled bookings, so admins retain a full record
- **Secrets kept out of source control** via environment variables (`.env` locally, host-level env vars in production)
- **Known limitation:** this host's free tier blocks outbound SMTP (ports 25/465/587) to prevent spam abuse, so email confirmation is feature-flagged off in production and only runs locally. A production fix would use an HTTP-based email API (e.g. Brevo) instead of SMTP.

## Running locally

```
git clone https://github.com/alytawfeek2007-cell/hotel-booking-flask.git
cd hotel-booking-flask
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python setup_db.py
python app.py
```

Then create a `.env` file with `SECRET_KEY`, `MAIL_USERNAME`, `MAIL_PASSWORD`, and `SEND_EMAIL=true`.

Default admin login: `admin@hotel.com` / `AdminPass123`