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
      "ig_business_account_id" :"xyz",
      "access_token" : "pdq"
    }'::jsonb,
    true
)
ON CONFLICT (account_key) DO UPDATE SET
    platform = EXCLUDED.platform,
    display_name = EXCLUDED.display_name,
    credentials = EXCLUDED.credentials,
    is_active = EXCLUDED.is_active;

INSERT INTO social_accounts (
    account_key,
    platform,
    display_name,
    credentials,
    is_active
) VALUES (
    'EW-Fb',
    'facebook',
    'EW Facebook',
    '{
      "page_id" : "id",
      "page_access_token" : "pdq"
    }'::jsonb,
    true
)
ON CONFLICT (account_key) DO UPDATE SET
    platform = EXCLUDED.platform,
    display_name = EXCLUDED.display_name,
    credentials = EXCLUDED.credentials,
    is_active = EXCLUDED.is_active;


