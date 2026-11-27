import os
from supabase import create_client, Client

_client: Client | None = None


def connect_db() -> Client:
    """Create and return a Supabase client using env vars."""
    global _client
    url = os.getenv('SUPABASE_URL', '').strip()
    key = os.getenv('SUPABASE_SECRET_KEY', '').strip()

    if not url or '<' in url:
        raise RuntimeError(
            'SUPABASE_URL is not configured. Set it in backend/.env.'
        )
    if not key or 'PASTE' in key or not key.startswith('sb_'):
        raise RuntimeError(
            'SUPABASE_SECRET_KEY is not configured. Set it in backend/.env.'
        )

    _client = create_client(url, key)
    return _client


def get_db() -> Client:
    if _client is None:
        raise RuntimeError('Supabase client is not connected.')
    return _client
