-- Migration: Add location ownership and privacy controls
-- Version: 003
-- Date: 2025-12-20
-- Description: Adds owner_id and is_public columns to locations table for ownership and privacy controls

-- ============================================================================
-- FORWARD MIGRATION
-- ============================================================================

BEGIN;

-- Add owner_id column to locations table (nullable for existing records)
ALTER TABLE locations
ADD COLUMN owner_id VARCHAR REFERENCES users(id) ON DELETE SET NULL;

-- Add is_public column to locations table (default TRUE for existing records)
ALTER TABLE locations
ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT TRUE;

-- Create index on locations.owner_id for efficient querying
CREATE INDEX idx_locations_owner_id ON locations(owner_id);

-- Create index on locations.is_public for privacy filtering
CREATE INDEX idx_locations_is_public ON locations(is_public);

COMMIT;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- To rollback this migration, run the following SQL in a separate transaction:
--
-- BEGIN;
-- DROP INDEX IF EXISTS idx_locations_is_public;
-- DROP INDEX IF EXISTS idx_locations_owner_id;
-- ALTER TABLE locations DROP COLUMN IF EXISTS is_public;
-- ALTER TABLE locations DROP COLUMN IF EXISTS owner_id;
-- COMMIT;
