-- Fix all old message notifications for admin users
-- Run this SQL directly on your PostgreSQL database

-- Update admin message notifications
UPDATE notifications_notification 
SET action_url = '/admin/discussions/'
WHERE category = 'message' 
AND recipient_id IN (
    SELECT id FROM accounts_user WHERE login_role = 'admin'
)
AND action_url != '/admin/discussions/';

-- Update user message notifications
UPDATE notifications_notification 
SET action_url = '/user/discussions/'
WHERE category = 'message' 
AND recipient_id IN (
    SELECT id FROM accounts_user WHERE login_role = 'user'
)
AND action_url != '/user/discussions/';

-- Check the results
SELECT 
    id,
    category,
    action_url,
    recipient_id
FROM notifications_notification 
WHERE category = 'message'
ORDER BY created_at DESC
LIMIT 10;
