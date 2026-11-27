import hmac, json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, session, send_file

admin_bp = Blueprint('admin', __name__)
STATUSES = {'Pending', 'Confirmed', 'Completed', 'Cancelled'}

# JSON file storage paths (used when Supabase is unavailable)
DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
BOOKINGS_FILE = DATA_DIR / 'bookings.json'
INQUIRIES_FILE = DATA_DIR / 'inquiries.json'


def admin_required():
    if not session.get('mtc_admin'):
        return jsonify(error='Please log in as administrator.'), 401
    return None


def load_json(filepath):
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_json(filepath, data):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────
# POST /api/admin/login
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json(silent=True) or {}

    # Accept either 'username' or 'email' field from the login form
    username_input = str(data.get('username') or data.get('email') or '').strip().lower()
    password_input = str(data.get('password', ''))

    expected_username = current_app.config.get('ADMIN_USERNAME', 'mangaloretaxi').strip().lower()
    expected_password = current_app.config.get('ADMIN_PASSWORD', '')

    if (not expected_username or not expected_password
            or not hmac.compare_digest(username_input, expected_username)
            or not hmac.compare_digest(password_input, expected_password)):
        return jsonify(error='Invalid username or password.'), 401

    session.clear()
    session['mtc_admin'] = True
    session['mtc_admin_user'] = expected_username
    return jsonify(message='Login successful.', username=expected_username)


# ──────────────────────────────────────────────
# GET /api/admin/me
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/me', methods=['GET'])
def admin_me():
    if not session.get('mtc_admin'):
        return jsonify(authenticated=False), 401
    return jsonify(authenticated=True, username=session.get('mtc_admin_user', 'Admin'))


# ──────────────────────────────────────────────
# POST /api/admin/logout
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/logout', methods=['POST', 'OPTIONS'])
def admin_logout():
    if request.method == 'OPTIONS':
        return '', 200
    session.clear()
    return jsonify(message='Logged out successfully.')


# ──────────────────────────────────────────────
# GET /api/admin/bookings
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/bookings', methods=['GET'])
def admin_bookings():
    denied = admin_required()
    if denied:
        return denied

    if current_app.db is not None:
        try:
            result = (
                current_app.db.table('bookings')
                .select('*')
                .order('created_at', desc=True)
                .limit(1000)
                .execute()
            )
            records = result.data or []
            # Remove internal Supabase 'id' column from API response
            for rec in records:
                rec.pop('id', None)
            return jsonify(bookings=records)
        except Exception:
            current_app.logger.exception('Unable to load admin bookings')
            return jsonify(error='Unable to load bookings.'), 503
    else:
        records = load_json(BOOKINGS_FILE)
        records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify(bookings=records)


# ──────────────────────────────────────────────
# PATCH /api/admin/bookings/<booking_id>
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/bookings/<booking_id>', methods=['PATCH', 'OPTIONS'])
def update_booking(booking_id):
    if request.method == 'OPTIONS':
        return '', 200

    denied = admin_required()
    if denied:
        return denied

    data = request.get_json(silent=True) or {}
    status = str(data.get('status', ''))
    if status not in STATUSES:
        return jsonify(error='Invalid booking status.'), 400

    if current_app.db is not None:
        try:
            result = (
                current_app.db.table('bookings')
                .update({'status': status})
                .eq('booking_id', booking_id)
                .execute()
            )
            if not result.data:
                return jsonify(error='Booking not found.'), 404
            return jsonify(message='Booking status updated.')
        except Exception:
            current_app.logger.exception('Unable to update booking')
            return jsonify(error='Unable to update booking.'), 503
    else:
        records = load_json(BOOKINGS_FILE)
        updated = False
        for rec in records:
            if rec.get('booking_id') == booking_id:
                rec['status'] = status
                updated = True
                break
        if not updated:
            return jsonify(error='Booking not found.'), 404
        save_json(BOOKINGS_FILE, records)
        return jsonify(message='Booking status updated.')


# ──────────────────────────────────────────────
# DELETE /api/admin/bookings/<booking_id>
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/bookings/<booking_id>', methods=['DELETE', 'OPTIONS'])
def delete_booking(booking_id):
    if request.method == 'OPTIONS':
        return '', 200

    denied = admin_required()
    if denied:
        return denied

    if current_app.db is not None:
        try:
            result = (
                current_app.db.table('bookings')
                .delete()
                .eq('booking_id', booking_id)
                .execute()
            )
            if not result.data:
                return jsonify(error='Booking not found.'), 404
            return jsonify(message='Booking deleted.')
        except Exception:
            current_app.logger.exception('Unable to delete booking')
            return jsonify(error='Unable to delete booking.'), 503
    else:
        records = load_json(BOOKINGS_FILE)
        new_records = [r for r in records if r.get('booking_id') != booking_id]
        if len(new_records) == len(records):
            return jsonify(error='Booking not found.'), 404
        save_json(BOOKINGS_FILE, new_records)
        return jsonify(message='Booking deleted.')


# ──────────────────────────────────────────────
# GET /api/admin/inquiries
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/inquiries', methods=['GET'])
def admin_inquiries():
    denied = admin_required()
    if denied:
        return denied

    if current_app.db is not None:
        try:
            result = (
                current_app.db.table('inquiries')
                .select('*')
                .order('created_at', desc=True)
                .limit(1000)
                .execute()
            )
            records = result.data or []
            for rec in records:
                rec.pop('id', None)
            return jsonify(inquiries=records)
        except Exception:
            current_app.logger.exception('Unable to load enquiries')
            return jsonify(error='Unable to load enquiries.'), 503
    else:
        records = load_json(INQUIRIES_FILE)
        records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify(inquiries=records)


# ──────────────────────────────────────────────
# GET /api/admin/export  – download Excel
# ──────────────────────────────────────────────
@admin_bp.route('/api/admin/export', methods=['GET'])
def export_bookings():
    denied = admin_required()
    if denied:
        return denied

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        return jsonify(error='openpyxl not installed. Run: pip install openpyxl'), 500

    if current_app.db is not None:
        try:
            result = (
                current_app.db.table('bookings')
                .select('*')
                .order('created_at', desc=True)
                .execute()
            )
            records = result.data or []
            for rec in records:
                rec.pop('id', None)
        except Exception:
            current_app.logger.exception('Unable to export bookings')
            return jsonify(error='Unable to export bookings.'), 503
    else:
        records = load_json(BOOKINGS_FILE)
        records.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    fields = ['booking_id', 'customer_name', 'phone', 'email', 'pickup', 'drop',
              'travel_date', 'pickup_time', 'trip_type', 'vehicle',
              'passengers', 'luggage', 'rental_duration',
              'additional_requirements', 'special_instructions', 'status', 'created_at']

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Bookings'

    # Styled header row
    header = [f.replace('_', ' ').title() for f in fields]
    sheet.append(header)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='12304A')
        cell.alignment = Alignment(horizontal='center')

    for item in records:
        sheet.append([str(item.get(field, '') or '') for field in fields])

    # Auto-width columns + freeze header + filter
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = sheet.dimensions
    for col in sheet.columns:
        width = min(max(max(len(str(c.value or '')) for c in col) + 2, 12), 36)
        sheet.column_dimensions[get_column_letter(col[0].column)].width = width

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name='MTC_Bookings.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
