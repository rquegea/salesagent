-- T&T Outreach Agent — Supabase Schema
-- Este archivo es para referencia. Las tablas se crean automáticamente
-- al ejecutar: python -c "from db import init_db; init_db()"

CREATE TABLE IF NOT EXISTS prospects (
    id SERIAL PRIMARY KEY,
    -- Contact data
    apollo_id TEXT UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    linkedin_url TEXT,
    job_title TEXT,
    company_name TEXT,
    company_domain TEXT,
    country TEXT,
    city TEXT,
    -- Internal data
    product_target TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    touchpoints INTEGER DEFAULT 0,
    last_contact_at TIMESTAMPTZ,
    next_contact_at TIMESTAMPTZ,
    -- Generated content
    draft_subject TEXT,
    draft_body TEXT,
    draft_channel TEXT,
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
CREATE INDEX IF NOT EXISTS idx_prospects_product ON prospects(product_target);
CREATE INDEX IF NOT EXISTS idx_prospects_next_contact ON prospects(next_contact_at);
CREATE INDEX IF NOT EXISTS idx_prospects_email ON prospects(email);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Status values for reference
-- new → drafted → sent → followed_up_1 → followed_up_2 → replied → meeting → closed
-- exhausted (no más intentos)

-- Sample queries

-- View all prospects
-- SELECT id, first_name, email, status, touchpoints, next_contact_at
-- FROM prospects
-- ORDER BY created_at DESC;

-- View prospects by status
-- SELECT * FROM prospects WHERE status = 'replied' ORDER BY last_contact_at DESC;

-- View pending follow-ups
-- SELECT id, first_name, email, status, touchpoints, next_contact_at
-- FROM prospects
-- WHERE status IN ('sent', 'followed_up_1')
-- AND next_contact_at <= NOW()
-- AND touchpoints < 4
-- ORDER BY next_contact_at;

-- View statistics
-- SELECT
--   COUNT(*) as total,
--   SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new,
--   SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
--   SUM(CASE WHEN status = 'replied' THEN 1 ELSE 0 END) as replied
-- FROM prospects;
