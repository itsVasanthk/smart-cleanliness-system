-- Schema Update for Smart Cleanliness System Overhaul

USE smart_cleanliness_db;

-- Update complaints table with new fields
ALTER TABLE complaints
ADD COLUMN authority_decision ENUM('pending', 'agreed', 'disagreed') DEFAULT 'pending',
ADD COLUMN authority_reason TEXT,
ADD COLUMN escalated_to_admin BOOLEAN DEFAULT FALSE,
ADD COLUMN escalated_at TIMESTAMP NULL,
ADD COLUMN citizen_feedback TEXT,
ADD COLUMN citizen_rating INT;

-- Ensure admin role is available in users table (already exists based on DESCRIBE)
-- ALTER TABLE users MODIFY COLUMN role ENUM('citizen', 'authority', 'admin') DEFAULT 'citizen';
