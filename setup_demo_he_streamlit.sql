-- ============================================================================
-- DEMO HIGHER EDUCATION STREAMLIT DATABASE SETUP
-- Database: demo_he_streamlit
-- Created for Streamlit in Snowflake data exploration application
-- ============================================================================
-- This script creates the database, schemas, tables, stage, file format,
-- and loads data from CSV files using COPY INTO commands.
-- ============================================================================

-- Use your warehouse (replace with your warehouse name)
 USE WAREHOUSE XS_WAREHOUSE;

-- ============================================================================
-- DATABASE AND SCHEMA CREATION
-- ============================================================================

CREATE OR REPLACE DATABASE demo_he_streamlit;
USE DATABASE demo_he_streamlit;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS student;
CREATE SCHEMA IF NOT EXISTS advising;
CREATE SCHEMA IF NOT EXISTS staging;  -- Schema for stage and file format

-- ============================================================================
-- FILE FORMAT CREATION
-- ============================================================================

CREATE OR REPLACE FILE FORMAT staging.csv_format
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    NULL_IF = ('', 'NULL', 'null');

-- ============================================================================
-- INTERNAL STAGE CREATION
-- ============================================================================

CREATE OR REPLACE STAGE staging.he_data_stage
    FILE_FORMAT = staging.csv_format
    COMMENT = 'Internal stage for loading higher education demo data';

-- ============================================================================
-- TABLE CREATION
-- ============================================================================

-- -----------------------------------------------------------------------------
-- FINANCE.FINANCIAL_AID
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE finance.financial_aid (
    financial_aid_id INTEGER,
    student_id VARCHAR(10) NOT NULL,
    major VARCHAR(50),
    department VARCHAR(50),
    award_type VARCHAR(30),
    award_name VARCHAR(100),
    amount DECIMAL(10,2),
    academic_year VARCHAR(9),
    semester VARCHAR(10),
    status VARCHAR(20),
    application_date DATE,
    disbursement_date DATE
);

-- -----------------------------------------------------------------------------
-- FINANCE.BILLING
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE finance.billing (
    billing_id INTEGER,
    student_id VARCHAR(10) NOT NULL,
    major VARCHAR(50),
    department VARCHAR(50),
    billing_period VARCHAR(20),
    tuition_amount DECIMAL(10,2),
    fees_amount DECIMAL(10,2),
    total_charges DECIMAL(10,2),
    payments_received DECIMAL(10,2),
    balance_due DECIMAL(10,2),
    due_date DATE,
    payment_status VARCHAR(20)
);

-- -----------------------------------------------------------------------------
-- STUDENT.ADDRESS
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE student.address (
    address_id INTEGER,
    student_id VARCHAR(10) NOT NULL,
    major VARCHAR(50),
    department VARCHAR(50),
    address_type VARCHAR(20),
    street_address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    country VARCHAR(50),
    is_primary BOOLEAN,
    effective_date DATE
);

-- -----------------------------------------------------------------------------
-- STUDENT.SIS (Student Information System)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE student.sis (
    sis_id INTEGER,
    student_id VARCHAR(10) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    major VARCHAR(50),
    department VARCHAR(50),
    enrollment_status VARCHAR(30),
    class_level VARCHAR(20),
    gpa DECIMAL(3,2),
    total_credits INTEGER,
    advisor_id VARCHAR(10),
    enrollment_date DATE,
    expected_graduation DATE
);

-- -----------------------------------------------------------------------------
-- ADVISING.ADVISING_INTERACTIONS
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TABLE advising.advising_interactions (
    interaction_id INTEGER,
    student_id VARCHAR(10) NOT NULL,
    major VARCHAR(50),
    department VARCHAR(50),
    advisor_id VARCHAR(10),
    advisor_name VARCHAR(100),
    interaction_date DATE,
    interaction_type VARCHAR(50),
    duration_minutes INTEGER,
    meeting_format VARCHAR(20),
    notes VARCHAR(500),
    follow_up_required BOOLEAN
);

-- ============================================================================
-- UPLOAD FILES TO STAGE
-- ============================================================================
-- 
-- Before running the COPY INTO commands, you must upload the CSV files to the stage.
-- 
-- OPTION 1: Using SnowSQL CLI
-- ---------------------------
-- Run these commands from your terminal where the CSV files are located:
--
--   snowsql -a <account> -u <username> -d demo_he_streamlit -s staging
--
-- Then in SnowSQL:
--   PUT file://./data/financial_aid.csv @he_data_stage AUTO_COMPRESS=FALSE;
--   PUT file://./data/billing.csv @he_data_stage AUTO_COMPRESS=FALSE;
--   PUT file://./data/address.csv @he_data_stage AUTO_COMPRESS=FALSE;
--   PUT file://./data/sis.csv @he_data_stage AUTO_COMPRESS=FALSE;
--   PUT file://./data/advising_interactions.csv @he_data_stage AUTO_COMPRESS=FALSE;
--
-- OPTION 2: Using Snowsight UI
-- ----------------------------
-- 1. Navigate to Data > Databases > DEMO_HE_STREAMLIT > STAGING > Stages > HE_DATA_STAGE
-- 2. Click the "+ Files" button
-- 3. Upload each CSV file from the data/ folder
--
-- OPTION 3: Using Python (snowflake-connector-python)
-- ---------------------------------------------------
-- from snowflake.connector import connect
-- conn = connect(...)
-- cursor = conn.cursor()
-- cursor.execute("PUT file://./data/financial_aid.csv @demo_he_streamlit.staging.he_data_stage AUTO_COMPRESS=FALSE")
-- # Repeat for each file
--
-- ============================================================================

-- Verify files are staged (run after uploading)
-- LIST @staging.he_data_stage;

-- ============================================================================
-- LOAD DATA FROM STAGE USING COPY INTO
-- ============================================================================

-- Load financial_aid data
COPY INTO finance.financial_aid
FROM @staging.he_data_stage/financial_aid.csv
FILE_FORMAT = staging.csv_format
ON_ERROR = 'CONTINUE';

-- Load billing data
COPY INTO finance.billing
FROM @staging.he_data_stage/billing.csv
FILE_FORMAT = staging.csv_format
ON_ERROR = 'CONTINUE';

-- Load address data
COPY INTO student.address
FROM @staging.he_data_stage/address.csv
FILE_FORMAT = staging.csv_format
ON_ERROR = 'CONTINUE';

-- Load sis data
COPY INTO student.sis
FROM @staging.he_data_stage/sis.csv
FILE_FORMAT = staging.csv_format
ON_ERROR = 'CONTINUE';

-- Load advising_interactions data
COPY INTO advising.advising_interactions
FROM @staging.he_data_stage/advising_interactions.csv
FILE_FORMAT = staging.csv_format
ON_ERROR = 'CONTINUE';

-- ============================================================================
-- GRANT PERMISSIONS (Adjust role as needed)
-- ============================================================================

-- Grant usage on database and schemas
GRANT USAGE ON DATABASE demo_he_streamlit TO ROLE <YOUR_ROLE>;
GRANT USAGE ON SCHEMA demo_he_streamlit.finance TO ROLE <YOUR_ROLE>;
GRANT USAGE ON SCHEMA demo_he_streamlit.student TO ROLE <YOUR_ROLE>;
GRANT USAGE ON SCHEMA demo_he_streamlit.advising TO ROLE <YOUR_ROLE>;
GRANT USAGE ON SCHEMA demo_he_streamlit.staging TO ROLE <YOUR_ROLE>;

-- Grant SELECT on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA demo_he_streamlit.finance TO ROLE <YOUR_ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA demo_he_streamlit.student TO ROLE <YOUR_ROLE>;
GRANT SELECT ON ALL TABLES IN SCHEMA demo_he_streamlit.advising TO ROLE <YOUR_ROLE>;

-- Grant stage access (if needed for future loads)
GRANT READ ON STAGE demo_he_streamlit.staging.he_data_stage TO ROLE <YOUR_ROLE>;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify staged files
SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

-- List files in stage
LIST @staging.he_data_stage;

-- Verify record counts
SELECT 'finance.financial_aid' AS table_name, COUNT(*) AS record_count FROM finance.financial_aid
UNION ALL
SELECT 'finance.billing', COUNT(*) FROM finance.billing
UNION ALL
SELECT 'student.address', COUNT(*) FROM student.address
UNION ALL
SELECT 'student.sis', COUNT(*) FROM student.sis
UNION ALL
SELECT 'advising.advising_interactions', COUNT(*) FROM advising.advising_interactions;

-- Sample data verification
SELECT * FROM finance.financial_aid LIMIT 5;
SELECT * FROM finance.billing LIMIT 5;
SELECT * FROM student.address LIMIT 5;
SELECT * FROM student.sis LIMIT 5;
SELECT * FROM advising.advising_interactions LIMIT 5;

-- ============================================================================
-- CLEANUP STAGE (Optional - run after successful load)
-- ============================================================================
-- Uncomment to remove files from stage after loading:
-- REMOVE @staging.he_data_stage;


-- add a table on the fly and see it show up i the app
/*
drop table student.intramurals;

CREATE OR REPLACE TABLE student.intramurals (
    student_id VARCHAR(10) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    sport VARCHAR(100),
    semester VARCHAR(50),
    signup_date DATE,
    expected_graduation DATE
);

INSERT INTO student.intramurals VALUES 
('STU001', 'Sarah', 'Johnson', 'Basketball', 'Fall 2025', '2025-08-15', '2027-05-15');

INSERT INTO student.intramurals VALUES 
('STU002', 'Michael', 'Chen', 'Soccer', 'Fall 2025', '2025-08-20', '2026-12-15');

INSERT INTO student.intramurals VALUES 
('STU003', 'Emily', 'Rodriguez', 'Volleyball', 'Spring 2026', '2026-01-10', '2028-05-15');

INSERT INTO student.intramurals VALUES 
('STU004', 'James', 'Williams', 'Flag Football', 'Fall 2025', '2025-09-05', '2027-12-15');

INSERT INTO student.intramurals VALUES 
('STU005', 'Ashley', 'Brown', 'Tennis', 'Spring 2026', '2026-01-15', '2026-05-15');

INSERT INTO student.intramurals VALUES 
('STU006', 'David', 'Martinez', 'Softball', 'Fall 2025', '2025-08-25', '2028-12-15');

INSERT INTO student.intramurals VALUES 
('STU007', 'Jessica', 'Davis', 'Swimming', 'Spring 2026', '2026-01-20', '2027-05-15');

INSERT INTO student.intramurals VALUES 
('STU008', 'Ryan', 'Miller', 'Ultimate Frisbee', 'Fall 2025', '2025-09-10', '2026-12-15');

INSERT INTO student.intramurals VALUES 
('STU009', 'Amanda', 'Wilson', 'Badminton', 'Spring 2026', '2026-01-12', '2027-12-15');

INSERT INTO student.intramurals VALUES 
('STU010', 'Christopher', 'Garcia', 'Table Tennis', 'Fall 2025', '2025-08-30', '2028-05-15');


*/
