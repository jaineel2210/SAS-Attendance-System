-- Add faculty_id column if it doesn't exist
ALTER TABLE users
ADD COLUMN IF NOT EXISTS faculty_id VARCHAR(20) UNIQUE,
ADD COLUMN IF NOT EXISTS department VARCHAR(100),
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- Update existing faculty records
UPDATE users 
SET faculty_id = enrollment_no,
    enrollment_no = NULL 
WHERE role = 'faculty' AND faculty_id IS NULL;
