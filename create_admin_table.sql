CREATE TABLE IF NOT EXISTS public.admin_users (
    id            BIGSERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO public.admin_users (username, email, password_hash) VALUES
('mangaloretaxi', 'shivakumarkapali01@gmail.com', 'scrypt:32768:8:1$dxNuxS7p0PFakv0E$00715ab86c42e015e61645d37bb6bd88306d7fc05124734c24a487e13a8f135f56f41cccfcbd51b6db0f998f758726ff77ea5759991aa4e67e9587139d856d2f')
ON CONFLICT (username) DO NOTHING;

GRANT ALL ON TABLE public.admin_users TO postgres, service_role;
GRANT USAGE, SELECT ON SEQUENCE admin_users_id_seq TO postgres, service_role;

ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_service_role_admin_users" ON public.admin_users;
CREATE POLICY "allow_service_role_admin_users" ON public.admin_users FOR ALL TO service_role USING (true) WITH CHECK (true);

NOTIFY pgrst, 'reload schema';
