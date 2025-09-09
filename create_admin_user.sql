-- Create admin user directly in Supabase
-- Password: admin123 (hashed with bcrypt)

INSERT INTO users (
    username, 
    email, 
    password_hash, 
    role, 
    is_active, 
    is_approved, 
    email_verified
) VALUES (
    'admin',
    'admin@bfisignals.com',
    '$2b$12$LQv3c1yX8LjAavnbLOTTNOHtychtHq0sb5csvda7TQC4xURag8.Gq',
    'admin',
    true,
    true,
    true
) ON CONFLICT (username) DO NOTHING;