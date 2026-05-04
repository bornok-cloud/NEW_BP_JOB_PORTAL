-- ============================================================
-- Job Portal Database Schema
-- Run this in phpMyAdmin or MySQL CLI
-- ============================================================

CREATE DATABASE IF NOT EXISTS job_portal_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE job_portal_db;

-- Users (all roles)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','employer','jobseeker') NOT NULL DEFAULT 'jobseeker',
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Jobseeker Profiles
CREATE TABLE IF NOT EXISTS jobseeker_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    full_name VARCHAR(150),
    phone VARCHAR(30),
    location VARCHAR(150),
    preferred_location VARCHAR(150),
    skills TEXT,
    experience_years INT DEFAULT 0,
    education TEXT,
    bio TEXT,
    linkedin_url VARCHAR(255),
    github_url VARCHAR(255),
    resume_path VARCHAR(255),
    resume_text LONGTEXT,
    resume_builder_data LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Employer Profiles
CREATE TABLE IF NOT EXISTS employer_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    company_name VARCHAR(200) NOT NULL,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    website VARCHAR(255),
    location VARCHAR(150),
    phone VARCHAR(30),
    company_description TEXT,
    logo_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employer_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    job_type ENUM('full-time','part-time','contract','internship','remote') DEFAULT 'full-time',
    experience_level ENUM('entry','mid','senior','executive') DEFAULT 'entry',
    location VARCHAR(150),
    salary_min DECIMAL(12,2),
    salary_max DECIMAL(12,2),
    required_skills TEXT,
    description LONGTEXT,
    requirements TEXT,
    benefits TEXT,
    deadline DATE,
    slots INT DEFAULT 1,
    status ENUM('active','inactive','closed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (employer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Applications
CREATE TABLE IF NOT EXISTS applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    applicant_id INT NOT NULL,
    cover_letter TEXT,
    match_score INT DEFAULT 0,
    status ENUM('pending','reviewed','interview','hired','rejected') DEFAULT 'pending',
    interview_date DATETIME,
    interview_notes TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_application (job_id, applicant_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (applicant_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Saved Jobs
CREATE TABLE IF NOT EXISTS saved_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    job_id INT NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_save (user_id, job_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content TEXT NOT NULL,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Default Admin Account (password: admin123)
INSERT IGNORE INTO users (name, email, password, role)
VALUES ('Administrator', 'admin@jobportal.com',
        '$2b$12$7WCkXCIrioXNKsQ4Ae5j9.o6HglFlPQS7GNQ/vDs6D3RJAmHJoQq.', 'admin');
