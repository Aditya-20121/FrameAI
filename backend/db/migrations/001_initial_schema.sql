-- FrameAI — Initial Schema
-- Run this in Supabase SQL editor (or via supabase CLI: supabase db push)

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
  token              TEXT PRIMARY KEY,
  generations_used   INTEGER NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_active_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Jobs
CREATE TABLE IF NOT EXISTS jobs (
  job_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_token      TEXT REFERENCES sessions(token),
  photo_r2_key       TEXT NOT NULL,
  face_shape         TEXT,
  face_shape_conf    FLOAT,
  undertone          TEXT,
  undertone_conf     FLOAT,
  undertone_hex      TEXT,
  ipd_mm             FLOAT,
  size_band          TEXT,
  status             TEXT NOT NULL DEFAULT 'processing',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at         TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Frames catalogue
CREATE TABLE IF NOT EXISTS frames (
  frame_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              TEXT NOT NULL,
  style             TEXT NOT NULL,
  colour            TEXT NOT NULL,
  colour_hex        TEXT,
  material          TEXT,
  face_shape_tags   TEXT[],
  undertone_tags    TEXT[],
  gender_tag        TEXT,
  lens_width_mm     INTEGER,
  bridge_width_mm   INTEGER,
  temple_length_mm  INTEGER,
  vibe_tags         TEXT[],
  retailer          TEXT NOT NULL,
  price_inr         INTEGER,
  buy_url           TEXT NOT NULL,
  product_image_url TEXT NOT NULL,
  scraped_at        TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Generation tasks
CREATE TABLE IF NOT EXISTS generation_tasks (
  task_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id             UUID REFERENCES jobs(job_id),
  frame_id           UUID REFERENCES frames(frame_id),
  session_token      TEXT REFERENCES sessions(token),
  status             TEXT NOT NULL DEFAULT 'queued',
  image_r2_key       TEXT,
  fal_request_id     TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at       TIMESTAMPTZ,
  expires_at         TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Atomic increment function used by db/supabase.py
CREATE OR REPLACE FUNCTION increment_generations(session_token TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
  new_count INTEGER;
BEGIN
  UPDATE sessions
  SET generations_used = generations_used + 1
  WHERE token = session_token
  RETURNING generations_used INTO new_count;
  RETURN new_count;
END;
$$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_session ON jobs(session_token);
CREATE INDEX IF NOT EXISTS idx_jobs_expires ON jobs(expires_at);
CREATE INDEX IF NOT EXISTS idx_gen_tasks_session ON generation_tasks(session_token);
CREATE INDEX IF NOT EXISTS idx_frames_style ON frames(style);
CREATE INDEX IF NOT EXISTS idx_frames_colour ON frames(colour);
