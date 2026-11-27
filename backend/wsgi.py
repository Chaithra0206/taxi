import os
from app import app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    # Production-ready WSGI server using Waitress
    try:
        from waitress import serve
        print(f"==================================================")
        print(f" Mangalore Taxi Corporation - Production Server")
        print(f" Serving with Waitress on http://0.0.0.0:{port}")
        print(f"==================================================")
        serve(app, host='0.0.0.0', port=port, threads=6)
    except ImportError:
        print("Waitress not installed, falling back to Flask development server...")
        app.run(host='0.0.0.0', port=port, debug=False)
