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

-- Social media integration tables
-- Stores configured social media accounts (e.g., Instagram)
CREATE TABLE IF NOT EXISTS social_accounts (
    id BIGSERIAL PRIMARY KEY,
    account_key TEXT UNIQUE NOT NULL,          -- e.g., 'EW-Insta'
    platform TEXT NOT NULL,                    -- e.g., 'instagram'
    display_name TEXT,
    credentials JSONB,                         -- API credentials/config (secure role should access)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stores social posts (drafts, scheduled, published)
CREATE TABLE IF NOT EXISTS social_posts (
    id BIGSERIAL PRIMARY KEY,
    account_key TEXT NOT NULL REFERENCES social_accounts(account_key) ON UPDATE CASCADE,
    platform TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',      -- 'draft' | 'scheduled' | 'published' | 'cancelled'
    prompt TEXT,                               -- original prompt provided by user
    caption TEXT,                              -- generated or provided caption/text
    image_mode TEXT DEFAULT 'none',            -- 'none' | 'generate' | 'url'
    image_url TEXT,                            -- when image_mode = 'url'
    employee_name TEXT,                        -- AI employee assigned
    requested_by_user_id BIGINT,               -- Discord user id
    scheduled_for TIMESTAMP WITH TIME ZONE,    -- optional schedule time
    meta JSONB,                                -- additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for social tables
CREATE INDEX IF NOT EXISTS idx_social_accounts_platform ON social_accounts(platform);
CREATE INDEX IF NOT EXISTS idx_social_accounts_active ON social_accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_social_posts_account_key ON social_posts(account_key);
CREATE INDEX IF NOT EXISTS idx_social_posts_status ON social_posts(status);
CREATE INDEX IF NOT EXISTS idx_social_posts_created_at ON social_posts(created_at);

-- Enable RLS
ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_posts ENABLE ROW LEVEL SECURITY;

-- Read policies (adjust as needed)
CREATE POLICY "Allow public read access to social_accounts" ON social_accounts
    FOR SELECT USING (true);

CREATE POLICY "Allow public read access to social_posts" ON social_posts
    FOR SELECT USING (true);

-- Authenticated manage policies
CREATE POLICY "Allow authenticated users to manage social_accounts" ON social_accounts
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to manage social_posts" ON social_posts
    FOR ALL USING (auth.role() = 'authenticated');