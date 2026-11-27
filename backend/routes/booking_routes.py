import re, uuid, json
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from utils.email_utils import send_booking_email

booking_bp = Blueprint('booking', __name__)

VEHICLES = ['Hatchback', 'Sedan', 'SUV', 'Luxury Cars', 'Innova', 'Innova / Innova Crysta', 'Ertiga', 'Tempo Traveller']
TRIPS = ['Local City Taxi', 'Airport Pickup and Drop', 'Outstation', 'One-Way', 'Round-Trip', 'Corporate Travel', 'Family Trip']

# JSON file storage paths (used when Supabase is unavailable)
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
BOOKINGS_FILE = DATA_DIR / 'bookings.json'
INQUIRIES_FILE = DATA_DIR / 'inquiries.json'


def clean(value, limit=500):
    return str(value or '').strip()[:limit]


def load_json(filepath):
    """Load list from a JSON file, returning empty list if missing or corrupt."""
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_json(filepath, data):
    """Save list to a JSON file, creating parent dirs as needed."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
# POST /api/bookings – submit a booking request
# ──────────────────────────────────────────────
@booking_bp.route('/api/bookings', methods=['POST', 'OPTIONS'])
def create_booking():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json(silent=True) or {}
    required = ['customer_name', 'phone', 'pickup', 'drop', 'travel_date', 'pickup_time', 'trip_type', 'vehicle']
    missing = [key for key in required if not clean(data.get(key))]
    if missing:
        return jsonify(error='Please complete all required fields.', fields=missing), 400

    phone = re.sub(r'[\s()+-]', '', clean(data['phone'], 25))
    if not re.fullmatch(r'\d{10,15}', phone):
        return jsonify(error='Enter a valid phone number (10–15 digits).'), 400

    if data['vehicle'] not in VEHICLES:
        return jsonify(error='Select a valid vehicle category.'), 400

    if data['trip_type'] not in TRIPS:
        return jsonify(error='Select a valid trip type.'), 400

    try:
        passengers = int(data.get('passengers', 1))
    except (TypeError, ValueError):
        passengers = 0
    if not 1 <= passengers <= 30:
        return jsonify(error='Passengers must be between 1 and 30.'), 400

    try:
        datetime.strptime(clean(data['travel_date']), '%Y-%m-%d')
    except ValueError:
        return jsonify(error='Travel date must be valid (YYYY-MM-DD).'), 400

    email = clean(data.get('email'), 120)
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return jsonify(error='Enter a valid email address.'), 400

    booking = {
        'booking_id': 'MTC-' + datetime.now(timezone.utc).strftime('%y%m%d') + '-' + uuid.uuid4().hex[:6].upper(),
        'customer_name': clean(data['customer_name'], 100),
        'phone': phone,
        'email': email,
        'pickup': clean(data['pickup']),
        'drop': clean(data['drop']),
        'travel_date': clean(data['travel_date'], 10),
        'pickup_time': clean(data['pickup_time'], 10),
        'trip_type': data['trip_type'],
        'vehicle': data['vehicle'],
        'passengers': passengers,
        'luggage': clean(data.get('luggage'), 200),
        'rental_duration': clean(data.get('rental_duration'), 100),
        'additional_requirements': clean(data.get('additional_requirements'), 500),
        'special_instructions': clean(data.get('special_instructions'), 1000),
        'status': 'Pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    # Try Supabase first; fall back to JSON file
    if current_app.db is not None:
        try:
            result = current_app.db.table('bookings').insert(booking).execute()
            if result.data is None:
                raise RuntimeError('Supabase insert returned no data.')
        except Exception:
            current_app.logger.exception('Booking database insert failed')
            return jsonify(error='Unable to save booking right now. Please try again.'), 503
    else:
        try:
            bookings = load_json(BOOKINGS_FILE)
            bookings.append(booking)
            save_json(BOOKINGS_FILE, bookings)
        except Exception:
            current_app.logger.exception('Booking file save failed')
            return jsonify(error='Unable to save booking. Please try again.'), 503

    # Send confirmation email (best-effort)
    try:
        send_booking_email(booking)
    except Exception:
        pass

    return jsonify(
        message='Your booking request has been received! Our team will contact you shortly to confirm.',
        booking_id=booking['booking_id']
    ), 201


# ──────────────────────────────────────────────
# GET /api/reviews
# ──────────────────────────────────────────────
@booking_bp.route('/api/reviews', methods=['GET'])
def get_reviews():
    default_reviews = [
        {'name': 'Ravi Kumar', 'rating': 5, 'comment': 'Easy booking and a very comfortable journey. Highly recommended!'},
        {'name': 'Priya Family', 'rating': 5, 'comment': 'Helpful driver and a smooth trip to Coorg. Will book again.'},
        {'name': 'Airport Passenger', 'rating': 5, 'comment': 'On-time pickup and very friendly service. Stress-free travel.'},
    ]
    if current_app.db is not None:
        try:
            result = (
                current_app.db.table('reviews')
                .select('name, rating, comment')
                .eq('approved', True)
                .order('created_at', desc=True)
                .limit(12)
                .execute()
            )
            items = result.data or []
            return jsonify(reviews=items if items else default_reviews)
        except Exception:
            pass
    return jsonify(reviews=default_reviews)


# ──────────────────────────────────────────────
# POST /api/inquiries – submit a contact enquiry
# ──────────────────────────────────────────────
@booking_bp.route('/api/inquiries', methods=['POST', 'OPTIONS'])
def create_inquiry():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json(silent=True) or {}
    name = clean(data.get('name'), 100)
    contact = clean(data.get('contact'), 150)
    message = clean(data.get('message'), 2000)

    if not name or not contact or not message:
        return jsonify(error='Please complete all enquiry fields.'), 400

    inquiry = {
        'name': name,
        'contact': contact,
        'message': message,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    if current_app.db is not None:
        try:
            result = current_app.db.table('inquiries').insert(inquiry).execute()
            if result.data is None:
                raise RuntimeError('Supabase insert returned no data.')
        except Exception:
            current_app.logger.exception('Enquiry database insert failed')
            return jsonify(error='Unable to save enquiry. Please try again.'), 503
    else:
        try:
            inquiries = load_json(INQUIRIES_FILE)
            inquiries.append(inquiry)
            save_json(INQUIRIES_FILE, inquiries)
        except Exception:
            current_app.logger.exception('Enquiry file save failed')
            return jsonify(error='Unable to save enquiry. Please try again.'), 503

    return jsonify(message='Your enquiry has been saved. Our team will contact you shortly.'), 201
