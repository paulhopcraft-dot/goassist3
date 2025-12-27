-- GoAssist v3.0 Database Initialization
-- Creates tables for session persistence and analytics

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    state VARCHAR(20) NOT NULL DEFAULT 'idle',
    config JSONB NOT NULL DEFAULT '{}',

    -- Metrics
    turns_completed INTEGER DEFAULT 0,
    total_audio_ms INTEGER DEFAULT 0,
    avg_ttfa_ms REAL DEFAULT 0.0,
    barge_in_count INTEGER DEFAULT 0,
    context_rollover_count INTEGER DEFAULT 0,

    -- Indexes for common queries
    CONSTRAINT valid_state CHECK (state IN ('idle', 'listening', 'thinking', 'speaking', 'interrupted'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);

-- Session events for debugging and analytics
CREATE TABLE IF NOT EXISTS session_events (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}',
    t_audio_ms INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_events_session_id ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_session_events_type ON session_events(event_type);

-- Turn history for conversation analytics
CREATE TABLE IF NOT EXISTS turns (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    user_text TEXT,
    assistant_text TEXT,
    ttfa_ms INTEGER,
    total_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_turns_session_id ON turns(session_id);

-- Materialized view for daily metrics (refresh periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_metrics AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_sessions,
    AVG(turns_completed) as avg_turns,
    AVG(avg_ttfa_ms) as avg_ttfa_ms,
    SUM(barge_in_count) as total_barge_ins,
    COUNT(*) FILTER (WHERE ended_at IS NOT NULL) as completed_sessions
FROM sessions
GROUP BY DATE(created_at);

-- Create refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_daily_metrics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_metrics;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your security model)
GRANT SELECT, INSERT, UPDATE ON sessions TO postgres;
GRANT SELECT, INSERT ON session_events TO postgres;
GRANT SELECT, INSERT ON turns TO postgres;
GRANT SELECT ON daily_metrics TO postgres;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Add comment for documentation
COMMENT ON TABLE sessions IS 'Active and historical voice sessions';
COMMENT ON TABLE session_events IS 'Timestamped events within sessions for debugging';
COMMENT ON TABLE turns IS 'Individual conversation turns with metrics';
