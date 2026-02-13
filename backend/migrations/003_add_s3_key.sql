-- Migration: Add s3_key column to images table
-- Note: base64_data will be made nullable (SQLAlchemy handles this in models, but raw SQL here helps DB consistency)

-- SQLite does not support ALTER COLUMN well, so we add s3_key first.
ALTER TABLE images ADD COLUMN s3_key VARCHAR;
CREATE INDEX ix_images_s3_key ON images (s3_key);

-- Note: We are not removing the NOT NULL constraint from base64_data in pure SQLite without a complex table rebuild.
-- The application code will treat it as nullable.
