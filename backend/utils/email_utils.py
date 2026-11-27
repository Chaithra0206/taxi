import os, smtplib
from email.message import EmailMessage

def send_booking_email(booking):
    recipient = os.getenv('OWNER_EMAIL', '').strip()
    user = os.getenv('SMTP_USER', '').strip()
    password = os.getenv('SMTP_PASSWORD', '').strip()
    if not all([recipient, user, password]):
        return False, 'Email is not configured; booking was saved.'
    msg = EmailMessage()
    msg['Subject'] = f"New taxi booking: {booking['booking_id']}"
    msg['From'] = user
    msg['To'] = recipient
    msg.set_content(
        f"New booking received\nBooking ID: {booking['booking_id']}\n"
        f"Customer: {booking['customer_name']}\nPhone: {booking['phone']}\n"
        f"Route: {booking['pickup']} to {booking['drop']}\n"
        f"Date/time: {booking['travel_date']} {booking['pickup_time']}\n"
        f"Vehicle: {booking['vehicle']}\nTrip: {booking['trip_type']}"
    )
    try:
        with smtplib.SMTP(os.getenv('SMTP_HOST', 'smtp.gmail.com'), int(os.getenv('SMTP_PORT', '587')), timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True, 'Notification email sent.'
    except Exception as exc:
        return False, f'Email notification failed: {exc}'
