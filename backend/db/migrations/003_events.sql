-- FrameAI — Usage analytics events (replaces PostHog: reuse existing Supabase)
-- Run this in Supabase SQL editor (or via supabase CLI: supabase db push)

CREATE TABLE IF NOT EXISTS events (
  event_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event         TEXT NOT NULL,
  distinct_id   TEXT NOT NULL,
  properties    JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_event_created ON events(event, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_distinct_id ON events(distinct_id);

-- ponytail: no retention/cleanup policy yet — table grows unbounded on the free
-- Supabase plan (500MB). Add a scheduled `DELETE WHERE created_at < NOW() - INTERVAL '30 days'`
-- (Celery beat, same pattern as tasks/price_refresh.py) if row count becomes a problem.
