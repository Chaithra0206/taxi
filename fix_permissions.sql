-- ============================================================
-- Fix Permissions & Schema Cache for Supabase
-- Run this in Supabase Dashboard -> SQL Editor -> New Query
-- ============================================================

-- Grant complete permissions to service_role, anon, and authenticated
GRANT ALL ON TABLE public.bookings TO postgres, service_role, anon, authenticated;
GRANT ALL ON TABLE public.inquiries TO postgres, service_role, anon, authenticated;
GRANT ALL ON TABLE public.reviews TO postgres, service_role, anon, authenticated;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role, anon, authenticated;

-- Ensure RLS doesn't block service_role
ALTER TABLE public.bookings FORCE ROW LEVEL SECURITY;
ALTER TABLE public.inquiries FORCE ROW LEVEL SECURITY;
ALTER TABLE public.reviews FORCE ROW LEVEL SECURITY;

-- Service role bypass policy (covers all actions)
DROP POLICY IF EXISTS "service_role_all_bookings" ON public.bookings;
CREATE POLICY "service_role_all_bookings" ON public.bookings
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_inquiries" ON public.inquiries;
CREATE POLICY "service_role_all_inquiries" ON public.inquiries
    FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_reviews" ON public.reviews;
CREATE POLICY "service_role_all_reviews" ON public.reviews
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Reload PostgREST schema cache immediately
NOTIFY pgrst, 'reload schema';
