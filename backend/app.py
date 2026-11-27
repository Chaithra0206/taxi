import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory, request

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
load_dotenv(BASE / '.env')

app = Flask(__name__, static_folder=str(ROOT / 'frontend'), static_url_path='')

app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'unsafe-development-key'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
    MAX_CONTENT_LENGTH=1024 * 1024
)

# Admin credentials – username/password based
app.config['ADMIN_USERNAME'] = os.getenv('ADMIN_USERNAME', 'mangaloretaxi')
app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD', '')

# Rate limiting (optional – gracefully skip if package missing)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    Limiter(get_remote_address, app=app, default_limits=['200 per hour'], storage_uri='memory://')
except ImportError:
    pass

# Register blueprints
from routes.booking_routes import booking_bp
from routes.admin_routes import admin_bp
app.register_blueprint(booking_bp)
app.register_blueprint(admin_bp)

# Try Supabase; fall back to JSON file storage if unavailable
try:
    from database import connect_db
    app.db = connect_db()
    print('Supabase connected successfully.')
except Exception as exc:
    app.db = None
    print(f'Supabase not available ({exc}). Using local JSON file storage fallback.')

# Static page routes
@app.get('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.get('/admin.html')
def admin_page():
    return send_from_directory(app.static_folder, 'admin.html')

@app.get('/health')
def health():
    return jsonify(
        status='ok',
        database='supabase' if app.db is not None else 'json-file-fallback'
    )

if __name__ == '__main__':
    print('Mangalore Taxi Corporation running at http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
