-- Migration: Add image_pull_sources table for automated image polling
-- This table tracks external image sources that should be polled periodically

CREATE TABLE IF NOT EXISTS image_pull_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    base_url TEXT NOT NULL,
    auth_type TEXT NOT NULL DEFAULT 'basic',
    auth_username TEXT,
    auth_password TEXT,
    auth_header TEXT,
    last_pulled_filename TEXT,
    last_pull_timestamp TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);

-- Index for efficient querying of active sources
CREATE INDEX IF NOT EXISTS idx_image_pull_sources_active ON image_pull_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_image_pull_sources_user ON image_pull_sources(user_id);
CREATE INDEX IF NOT EXISTS idx_image_pull_sources_location ON image_pull_sources(location_id);
