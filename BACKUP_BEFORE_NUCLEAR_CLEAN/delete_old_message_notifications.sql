-- Delete all old message notifications
-- They will be recreated with correct URLs when new messages are sent

DELETE FROM notifications_notification 
WHERE category = 'message';

-- Verify they're deleted
SELECT COUNT(*) as remaining_message_notifications
FROM notifications_notification 
WHERE category = 'message';
