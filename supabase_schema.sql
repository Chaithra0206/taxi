-- ============================================================
-- Complete Clean Setup for Mangalore Taxi Corporation
-- Run this in Supabase Dashboard -> SQL Editor
-- ============================================================

-- 1. DROP EXISTING CONFLICTING TABLES
DROP TABLE IF EXISTS public.bookings CASCADE;
DROP TABLE IF EXISTS public.inquiries CASCADE;
DROP TABLE IF EXISTS public.reviews CASCADE;

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

-- 5. INSERT INITIAL REVIEWS
INSERT INTO public.reviews (name, rating, comment, approved) VALUES
('Ravi Kumar', 5, 'Easy booking and a very comfortable journey. Highly recommended!', true),
('Priya Family', 5, 'Helpful driver and a smooth trip to Coorg. Will book again.', true),
('Airport Passenger', 5, 'On-time pickup and very friendly service. Stress-free travel.', true);

-- 6. GRANT ALL PRIVILEGES
GRANT ALL ON TABLE public.bookings TO postgres, service_role, anon, authenticated;
GRANT ALL ON TABLE public.inquiries TO postgres, service_role, anon, authenticated;
GRANT ALL ON TABLE public.reviews TO postgres, service_role, anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role, anon, authenticated;

-- 7. ENABLE ROW LEVEL SECURITY WITH PERMISSIVE POLICIES
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_bookings" ON public.bookings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_inquiries" ON public.inquiries FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_reviews" ON public.reviews FOR ALL USING (true) WITH CHECK (true);

-- 8. RELOAD SCHEMA CACHE
NOTIFY pgrst, 'reload schema';
