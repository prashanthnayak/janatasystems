-- Database migration script to add client phone and email fields
-- Run this on your EC2 instance to update the existing database

-- Add the new columns to the cases table
ALTER TABLE cases ADD COLUMN IF NOT EXISTS client_phone VARCHAR(10);
ALTER TABLE cases ADD COLUMN IF NOT EXISTS client_email VARCHAR(255);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cases_client_phone ON cases(client_phone);
CREATE INDEX IF NOT EXISTS idx_cases_client_email ON cases(client_email);

-- Verify the changes
\d cases;

-- Show sample data
SELECT cnr_number, client_name, client_phone, client_email FROM cases LIMIT 5;
