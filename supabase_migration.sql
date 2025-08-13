-- Supabase Migration Script
-- Run this in your Supabase SQL Editor to create the required tables

-- Create AI employees table
CREATE TABLE IF NOT EXISTS ai_employees (
    id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    employee_type TEXT NOT NULL,
    parameters JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user permissions table
CREATE TABLE IF NOT EXISTS user_permissions (
    user_id BIGINT PRIMARY KEY,
    permission_level INTEGER DEFAULT 1,
    granted_by BIGINT,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create conversation history table
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT,
    user_id BIGINT,
    channel_id BIGINT,
    message TEXT,
    response TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ai_employees_name ON ai_employees(name);
CREATE INDEX IF NOT EXISTS idx_ai_employees_active ON ai_employees(is_active);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_employee_id ON conversations(employee_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);

-- Enable Row Level Security (RLS) - optional but recommended for production
ALTER TABLE ai_employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (adjust based on your security needs)
CREATE POLICY "Allow public read access to ai_employees" ON ai_employees
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to user_permissions" ON user_permissions
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to conversations" ON conversations
    FOR SELECT USING (true);

-- Create policies for authenticated users to insert/update
CREATE POLICY "Allow authenticated users to manage ai_employees" ON ai_employees
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to manage user_permissions" ON user_permissions
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to manage conversations" ON conversations
    FOR ALL USING (auth.role() = 'authenticated');
