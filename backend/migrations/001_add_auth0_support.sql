-- Migration: Add Auth0 authentication support
-- Version: 001
-- Date: 2025-11-23
-- Description: Adds users table and user_id column to images table for Auth0 integration

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

BEGIN;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR,
    name VARCHAR,
    privacy_public BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_privacy ON users(privacy_public);

-- Add user_id column to images table (nullable for existing records)
ALTER TABLE images
ADD COLUMN IF NOT EXISTS user_id VARCHAR REFERENCES users(id);

-- Create index on images.user_id for efficient querying
CREATE INDEX IF NOT EXISTS idx_images_user_id ON images(user_id);

COMMIT;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- To rollback this migration, run the following SQL in a separate transaction:
--
-- BEGIN;
-- DROP INDEX IF EXISTS idx_images_user_id;
-- ALTER TABLE images DROP COLUMN IF EXISTS user_id;
-- DROP INDEX IF EXISTS idx_users_privacy;
-- DROP INDEX IF EXISTS idx_users_email;
-- DROP TABLE IF EXISTS users;
-- COMMIT;
