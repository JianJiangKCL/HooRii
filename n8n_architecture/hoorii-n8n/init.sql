-- Hoorii n8n Database Schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(100) NOT NULL,
    familiarity_score INTEGER DEFAULT 0 CHECK (familiarity_score >= 0 AND familiarity_score <= 100),
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(50) PRIMARY KEY,
    device_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    current_state JSONB DEFAULT '{}',
    required_familiarity INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
    session_id VARCHAR(50) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    context_data JSONB DEFAULT '{}',
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS device_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    device_id VARCHAR(50) REFERENCES devices(device_id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    parameters JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT true,
    response_time INTEGER,
    session_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_memories (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    importance INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_users_familiarity ON users(familiarity_score);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_user_device ON device_interactions(user_id, device_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_type ON user_memories(user_id, memory_type, created_at DESC);

-- 默认数据
INSERT INTO devices (device_id, device_type, name, required_familiarity, current_state) VALUES
('light_living_room', 'light', '客厅灯', 10, '{"state": "off", "brightness": 100}'),
('light_bedroom', 'light', '卧室灯', 10, '{"state": "off", "brightness": 50}'),
('speaker_living_room', 'speaker', '客厅音箱', 20, '{"state": "off", "volume": 50}'),
('tv_living_room', 'tv', '客厅电视', 30, '{"state": "off", "channel": 1}'),
('air_conditioner_living_room', 'air_conditioner', '客厅空调', 40, '{"state": "off", "temperature": 25}'),
('curtain_bedroom', 'curtain', '卧室窗帘', 50, '{"state": "open", "position": 100}')
ON CONFLICT (device_id) DO NOTHING;

INSERT INTO users (user_id, name, familiarity_score, interaction_count) VALUES
('test_user', 'Test User', 30, 10)
ON CONFLICT (user_id) DO NOTHING;
