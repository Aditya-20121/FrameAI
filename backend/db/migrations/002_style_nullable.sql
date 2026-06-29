-- FrameAI Migration 002
-- Make style nullable so frames without auto-detected style can be loaded
-- and annotated later via the annotation CLI.
-- Run this in the Supabase SQL editor before running: python run.py load

ALTER TABLE frames ALTER COLUMN style DROP NOT NULL;
ALTER TABLE frames ALTER COLUMN colour DROP NOT NULL;
