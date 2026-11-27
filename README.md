# Mangalore Taxi Corporation

A responsive taxi booking website with a Flask/PyMongo backend, MongoDB Atlas persistence, MongoDB-backed booking storage and optional Gmail SMTP notifications.

## 1. Requirements

- Windows 10/11
- Python 3.10 or newer (Python 3.12 is a safe choice)
- MongoDB Atlas account and a database user
- Modern browser

## 2. MongoDB Atlas setup

1. Sign in at https://www.mongodb.com/atlas and create a free shared cluster.
2. In **Database Access**, create a database username and password. Do not use your Atlas website login.
3. In **Network Access**, add your current public IP address. For a temporary development-only test you can allow `0.0.0.0/0`; restrict it again afterwards.
4. Open **Database > Connect > Drivers**, choose Python, and copy the connection string.
5. Replace the username, password and cluster host in the connection string. URL-encode special characters in the password (for example `@` becomes `%40`).
6. The app creates the database `mangalore_taxi_corporation`, its collections and indexes when it connects. You can inspect them in Atlas or MongoDB Compass.

## 3. Configure environment

Open PowerShell in the project folder:

```powershell
cd .\backend
Copy-Item .env.example .env
notepad .env
```

Set `MONGODB_URI`, `MONGODB_DATABASE`, and a long random `SECRET_KEY`. The included `.env` is only a template; replace all placeholders. Never publish `.env` or share your database password.

Optional Gmail notifications:

1. Enable 2-Step Verification on the Gmail account used to send notifications.
2. Create a Google App Password in your Google Account security settings.
3. Set `SMTP_USER`, `SMTP_PASSWORD`, and `OWNER_EMAIL` in `.env`. The owner receives new booking alerts. Email failure does not cancel or roll back a saved booking.

Update company phone, WhatsApp number, email and address in `backend/.env` and the matching contact links/config in `frontend/index.html` and `frontend/js/config.js` before publishing.

## 4. Install and run on Windows

Use PowerShell from the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\backend\requirements.txt
```

If PowerShell blocks activation, run this once in that terminal, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Start the website:

```powershell
cd .\backend
python app.py
```

Open **http://127.0.0.1:5000** in your browser. Flask serves the frontend and API together. Do not double-click `index.html`.

## 6. API overview

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/bookings` | Public | Validate and save booking |
| GET | `/api/reviews` | Public | Approved reviews (sample fallback until reviews are added) |
| GET | `/health` | Public | App/database health |

## 7. Test checklist

- [ ] `/health` reports `database: connected`.
- [ ] Submit a valid booking and note its booking ID.
- [ ] Verify the document exists in Atlas under `mangalore_taxi_corporation.bookings`.
- [ ] Try invalid phone/email and confirm validation errors.
- [ ] Sign in as admin; confirm dashboard counts reflect database records.
- [ ] Search by customer name, phone or booking ID; test date, vehicle, trip and status filters.
- [ ] Change a status and verify it persists after refreshing.
- [ ] Delete a test booking and verify it is removed.
- [ ] Download and open the Excel report.
- [ ] Configure Gmail and verify an owner notification; also test with email settings blank to confirm booking still saves.
- [ ] Sign out and verify protected endpoints return HTTP 401.

## 8. Important production notes

This project is a beginner-friendly local deployment starter, not a production-hardened public service. Before public launch, deploy behind HTTPS with a production WSGI server, set `SESSION_COOKIE_SECURE=true`, use a strong secret, add CSRF protection for cookie-authenticated state-changing routes, use a persistent rate-limit store (Redis), add CAPTCHA/abuse controls and monitoring, and review privacy/retention requirements. The Flask-Limiter default store is in-memory and resets on restart. Do not expose the development server to the public internet.

The sample review cards shown by the site are generic fallback content when no approved review documents exist. The project does not currently provide public review submission or review moderation UI. This version has no admin page or admin API routes. Vehicle cards use representative remote image URLs; replace them with licensed local assets if required for deployment.


## Brand and vehicle imagery update

This project is branded as **Mangalore Taxi Corporation**. The homepage hero uses the fleet photograph supplied by the project owner. Vehicle cards use real-world model photographs hosted by third-party automotive/news websites (Swift, Dzire, Brezza, E-Class, Innova Crysta, Ertiga and Force Traveller). Those remote image URLs require an internet connection and remain subject to their respective owners’ image rights and hosting terms. Obtain permission or replace them with company-owned/licensed photographs before commercial publication.

## Admin portal (added)

1. Open `backend/.env` and set your real MongoDB Atlas connection string in `MONGODB_URI`.
2. Set a private, strong `SECRET_KEY` and a strong `ADMIN_PASSWORD`. Keep these values secret.
3. Keep `ADMIN_EMAIL` as the email address you want to use for administrator sign-in.
4. Start the Flask backend using the existing project instructions.
5. Open `http://127.0.0.1:5000/admin.html` and sign in with `ADMIN_EMAIL` and `ADMIN_PASSWORD`.

The admin portal displays customer bookings and contact enquiries, lets the administrator update booking status, and exports bookings to an Excel file. Customer booking requests and contact enquiries are saved in MongoDB. The main website design has been retained.

**Security:** Change the sample admin password and secret key before use. Do not publish your `.env` file or share its credentials. Use HTTPS when deploying publicly.
