-- ============================================================
-- Complete Clean Setup for Mangalore Taxi Corporation
-- Run this in Supabase Dashboard -> SQL Editor
-- ============================================================

-- 1. DROP EXISTING CONFLICTING TABLES
DROP TABLE IF EXISTS public.bookings CASCADE;
DROP TABLE IF EXISTS public.inquiries CASCADE;
DROP TABLE IF EXISTS public.reviews CASCADE;
DROP TABLE IF EXISTS public.admin_users CASCADE;

-- 2. CREATE BOOKINGS TABLE
CREATE TABLE public.bookings (
    id                      BIGSERIAL PRIMARY KEY,
    booking_id              TEXT UNIQUE NOT NULL,
    customer_name           TEXT NOT NULL,
    phone                   TEXT NOT NULL,
    email                   TEXT,
    pickup                  TEXT NOT NULL,
    drop                    TEXT NOT NULL,
    travel_date             DATE NOT NULL,
    pickup_time             TIME NOT NULL,
    trip_type               TEXT NOT NULL,
    vehicle                 TEXT NOT NULL,
    passengers              INTEGER NOT NULL DEFAULT 1,
    luggage                 TEXT,
    rental_duration         TEXT,
    additional_requirements TEXT,
    special_instructions    TEXT,
    status                  TEXT NOT NULL DEFAULT 'Pending',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. CREATE INQUIRIES TABLE
CREATE TABLE public.inquiries (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    contact    TEXT NOT NULL,
    message    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. CREATE REVIEWS TABLE
CREATE TABLE public.reviews (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    rating     INTEGER NOT NULL DEFAULT 5,
    comment    TEXT NOT NULL,
    approved   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. CREATE ADMIN USERS TABLE
CREATE TABLE public.admin_users (
    id            BIGSERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. INSERT INITIAL ADMIN USER (Password: Shiva@5867 hashed with scrypt)
INSERT INTO public.admin_users (username, email, password_hash) VALUES
('mangaloretaxi', 'shivakumarkapali01@gmail.com', 'scrypt:32768:8:1$dxNuxS7p0PFakv0E$00715ab86c42e015e61645d37bb6bd88306d7fc05124734c24a487e13a8f135f56f41cccfcbd51b6db0f998f758726ff77ea5759991aa4e67e9587139d856d2f');

-- 7. INSERT INITIAL REVIEWS
INSERT INTO public.reviews (name, rating, comment, approved) VALUES
('Ravi Kumar', 5, 'Easy booking and a very comfortable journey. Highly recommended!', true),
('Priya Family', 5, 'Helpful driver and a smooth trip to Coorg. Will book again.', true),
('Airport Passenger', 5, 'On-time pickup and very friendly service. Stress-free travel.', true);

-- 8. GRANT PRIVILEGES
GRANT ALL ON TABLE public.bookings TO postgres, service_role, anon, authenticated;
GRANT ALL ON TABLE public.inquiries TO postgres, service_role, anon, authenticated;
GRANT ALL ON TABLE public.reviews TO postgres, service_role, anon, authenticated;
GRANT ALL ON TABLE public.admin_users TO postgres, service_role;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role, anon, authenticated;

-- 9. ENABLE ROW LEVEL SECURITY
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_bookings" ON public.bookings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_inquiries" ON public.inquiries FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_reviews" ON public.reviews FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_service_role_admin_users" ON public.admin_users FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 10. RELOAD SCHEMA CACHE
NOTIFY pgrst, 'reload schema';
