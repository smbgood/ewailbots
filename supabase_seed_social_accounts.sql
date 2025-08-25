-- Supabase Seed Script: Insert default Instagram social account
-- Safe to run multiple times; uses upsert on unique account_key

INSERT INTO social_accounts (
    account_key,
    platform,
    display_name,
    credentials,
    is_active
) VALUES (
    'EW-Insta',
    'instagram',
    'EW Instagram',
    '{
      "description": "Dummy credentials for development only",
      "app_id": "placeholder",
      "app_secret": "placeholder",
      "access_token": "placeholder"
    }'::jsonb,
    true
)
ON CONFLICT (account_key) DO UPDATE SET
    platform = EXCLUDED.platform,
    display_name = EXCLUDED.display_name,
    credentials = EXCLUDED.credentials,
    is_active = EXCLUDED.is_active;


