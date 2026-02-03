# Higher Education Data Explorer

A Streamlit in Snowflake application that enables business users to explore and visualize higher education data across Finance, Student Services, and Advising systems.

## Overview

This application provides a dynamic, no-code interface for exploring student data with:

- **Schema/Table Selection**: Dropdown navigation across multiple schemas and tables
- **Dynamic Filtering**: Automatically generates appropriate filters based on column data types
  - Multi-select dropdowns for categorical fields
  - Range sliders for numeric fields
  - Date range pickers for date fields
  - Radio buttons for boolean fields
- **Data Visualization**: Interactive charts showing distributions and aggregations
- **CSV Export**: One-click download of filtered data

## Project Structure

```
cursor_data_explorer/
├── README.md                       # This file
├── setup_demo_he_streamlit.sql     # SQL DDL script (tables, stage, file format)
├── streamlit_app.py                # Streamlit application code
└── data/                           # CSV data files
    ├── financial_aid.csv           # Financial aid awards data
    ├── billing.csv                 # Student billing records
    ├── address.csv                 # Student addresses
    ├── sis.csv                     # Student Information System data
    └── advising_interactions.csv   # Advising meeting records
```

## Database Structure

### Database: `DEMO_HE_STREAMLIT`

| Schema | Table | Description | Records |
|--------|-------|-------------|---------|
| `finance` | `financial_aid` | Student financial aid awards, scholarships, grants, and loans | 50 |
| `finance` | `billing` | Tuition and fee billing records, payments, and balances | 50 |
| `student` | `address` | Student address information (home, campus, mailing) | 50 |
| `student` | `sis` | Student Information System - enrollment, GPA, credits | 50 |
| `advising` | `advising_interactions` | Academic advising meeting records and notes | 50 |
| `staging` | — | Contains stage and file format for data loading | — |

### Common Fields

All tables share these common fields for cross-referencing:
- `student_id` - Alphanumeric student identifier (e.g., STU10001)
- `major` - Student's declared major
- `department` - Academic department (Engineering, Arts & Sciences, Business, Health Sciences)

### Data Coverage

- **Time Period**: Academic years 2023-2024 through 2025-2026
- **Records**: 50 records per table (250 total)
- **Students**: 50 unique students represented

---

## Setup Instructions

### Prerequisites

- Snowflake account with appropriate permissions
- Access to create databases, schemas, tables, and stages
- Ability to upload files to Snowflake stages
- Ability to create Streamlit apps in Snowflake

---

### Step 1: Create Database, Schemas, and Tables

1. Open a Snowflake worksheet in Snowsight
2. Copy the contents of `setup_demo_he_streamlit.sql`
3. **Replace placeholders** at the top:
   - `<YOUR_WAREHOUSE>` → Your warehouse name (e.g., `COMPUTE_WH`)
4. **Run only the first section** up to the UPLOAD FILES section:
   - Database creation
   - Schema creation
   - File format creation
   - Stage creation
   - Table creation

```sql
-- Run these sections first:
-- DATABASE AND SCHEMA CREATION
-- FILE FORMAT CREATION
-- INTERNAL STAGE CREATION
-- TABLE CREATION
```

---

### Step 2: Upload CSV Files to Stage

You have three options to upload the CSV files to the internal stage:

#### Option A: Using Snowsight UI (Easiest)

1. In Snowsight, navigate to: **Data** → **Databases** → **DEMO_HE_STREAMLIT** → **STAGING** → **Stages**
2. Click on **HE_DATA_STAGE**
3. Click the **"+ Files"** button in the top right
4. Upload all 5 CSV files from the `data/` folder:
   - `financial_aid.csv`
   - `billing.csv`
   - `address.csv`
   - `sis.csv`
   - `advising_interactions.csv`

#### Option B: Using SnowSQL CLI

```bash
# Connect to Snowflake
snowsql -a <your_account> -u <your_username>

# Use the correct database and schema
USE DATABASE demo_he_streamlit;
USE SCHEMA staging;

# Upload each file (run from the directory containing the data/ folder)
PUT file://./data/financial_aid.csv @he_data_stage AUTO_COMPRESS=FALSE;
PUT file://./data/billing.csv @he_data_stage AUTO_COMPRESS=FALSE;
PUT file://./data/address.csv @he_data_stage AUTO_COMPRESS=FALSE;
PUT file://./data/sis.csv @he_data_stage AUTO_COMPRESS=FALSE;
PUT file://./data/advising_interactions.csv @he_data_stage AUTO_COMPRESS=FALSE;
```

#### Option C: Using Python

```python
from snowflake.connector import connect
import os

# Connect to Snowflake
conn = connect(
    account='<your_account>',
    user='<your_username>',
    password='<your_password>',
    warehouse='<your_warehouse>',
    database='demo_he_streamlit',
    schema='staging'
)

cursor = conn.cursor()

# Upload each CSV file
data_files = [
    'financial_aid.csv',
    'billing.csv', 
    'address.csv',
    'sis.csv',
    'advising_interactions.csv'
]

for file in data_files:
    file_path = f'./data/{file}'
    cursor.execute(f"PUT file://{file_path} @he_data_stage AUTO_COMPRESS=FALSE")
    print(f"Uploaded {file}")

cursor.close()
conn.close()
```

#### Verify Upload

After uploading, verify files are in the stage:

```sql
LIST @staging.he_data_stage;
```

You should see all 5 CSV files listed.

---

### Step 3: Load Data from Stage

Run the COPY INTO commands from the SQL script:

```sql
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
```

---

### Step 4: Verify Data Load

Run the verification query:

```sql
SELECT 'finance.financial_aid' AS table_name, COUNT(*) AS record_count FROM finance.financial_aid
UNION ALL
SELECT 'finance.billing', COUNT(*) FROM finance.billing
UNION ALL
SELECT 'student.address', COUNT(*) FROM student.address
UNION ALL
SELECT 'student.sis', COUNT(*) FROM student.sis
UNION ALL
SELECT 'advising.advising_interactions', COUNT(*) FROM advising.advising_interactions;
```

**Expected output:** 50 records per table.

---

### Step 5: Grant Permissions

Update `<YOUR_ROLE>` and run the GRANT statements:

```sql
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
```

---

### Step 6: Create the Streamlit App

1. Navigate to **Snowsight** → **Streamlit**
2. Click **+ Streamlit App**
3. Configure the app:
   - **App name**: `Higher_Education_Data_Explorer`
   - **Warehouse**: Select your warehouse
   - **Database**: `DEMO_HE_STREAMLIT`
   - **Schema**: `STUDENT` (or any schema)
4. Delete the default code in the editor
5. Copy and paste the entire contents of `streamlit_app.py`
6. Click **Run** to launch the application

---

### Step 7: Verify Application

Once running, you should see:
- Header with application title
- Sidebar with schema and table dropdowns
- Dynamic filters based on selected table
- Data grid showing table records
- Visualization charts
- Export button

---

## Usage Guide

### Selecting Data

1. Use the **Schema** dropdown in the sidebar to select a data domain:
   - `FINANCE` - Financial aid and billing data
   - `STUDENT` - Address and enrollment data
   - `ADVISING` - Advising interaction records

2. Use the **Table** dropdown to select a specific table

### Filtering Data

Filters are automatically generated based on column types:

| Column Type | Filter Widget | Example |
|-------------|---------------|---------|
| Text/VARCHAR | Multi-select dropdown | Major, Status, Department |
| Numeric | Range slider | Amount, GPA, Credits |
| Date | Date range picker | Application Date, Due Date |
| Boolean | Radio buttons | Is Primary, Follow Up Required |

**Tips:**
- Leave filters empty to show all records
- Active filters display a count badge
- Filters are combined with AND logic

### Exporting Data

1. Apply desired filters
2. Click the **📥 Export to CSV** button
3. File downloads with format: `{schema}_{table}_export.csv`

### Visualizations

Two chart areas are provided:
- **Left chart**: Categorical distribution (count by category)
- **Right chart**: Numeric aggregation by category

Use the dropdowns above each chart to customize the visualization.

---

## Table Schemas

### finance.financial_aid

| Column | Type | Description |
|--------|------|-------------|
| financial_aid_id | INTEGER | Primary key |
| student_id | VARCHAR(10) | Student identifier |
| major | VARCHAR(50) | Student's major |
| department | VARCHAR(50) | Academic department |
| award_type | VARCHAR(30) | Grant, Scholarship, Loan, Work-Study |
| award_name | VARCHAR(100) | Specific award name |
| amount | DECIMAL(10,2) | Award amount in dollars |
| academic_year | VARCHAR(9) | e.g., "2024-2025" |
| semester | VARCHAR(10) | Fall, Spring, Summer |
| status | VARCHAR(20) | Pending, Approved, Disbursed, Cancelled |
| application_date | DATE | Date application submitted |
| disbursement_date | DATE | Date funds disbursed |

### finance.billing

| Column | Type | Description |
|--------|------|-------------|
| billing_id | INTEGER | Primary key |
| student_id | VARCHAR(10) | Student identifier |
| major | VARCHAR(50) | Student's major |
| department | VARCHAR(50) | Academic department |
| billing_period | VARCHAR(20) | e.g., "Fall 2024" |
| tuition_amount | DECIMAL(10,2) | Tuition charges |
| fees_amount | DECIMAL(10,2) | Fee charges |
| total_charges | DECIMAL(10,2) | Sum of tuition and fees |
| payments_received | DECIMAL(10,2) | Payments made |
| balance_due | DECIMAL(10,2) | Outstanding balance |
| due_date | DATE | Payment due date |
| payment_status | VARCHAR(20) | Paid, Partial, Outstanding, Overdue |

### student.address

| Column | Type | Description |
|--------|------|-------------|
| address_id | INTEGER | Primary key |
| student_id | VARCHAR(10) | Student identifier |
| major | VARCHAR(50) | Student's major |
| department | VARCHAR(50) | Academic department |
| address_type | VARCHAR(20) | Home, Campus, Mailing |
| street_address | VARCHAR(200) | Street address |
| city | VARCHAR(100) | City |
| state | VARCHAR(2) | State abbreviation |
| zip_code | VARCHAR(10) | ZIP code |
| country | VARCHAR(50) | Country |
| is_primary | BOOLEAN | Primary address flag |
| effective_date | DATE | Date address became effective |

### student.sis

| Column | Type | Description |
|--------|------|-------------|
| sis_id | INTEGER | Primary key |
| student_id | VARCHAR(10) | Student identifier |
| first_name | VARCHAR(50) | First name |
| last_name | VARCHAR(50) | Last name |
| email | VARCHAR(100) | University email |
| major | VARCHAR(50) | Declared major |
| department | VARCHAR(50) | Academic department |
| enrollment_status | VARCHAR(30) | Full-time, Part-time, Leave of Absence, Graduated, Withdrawn |
| class_level | VARCHAR(20) | Freshman, Sophomore, Junior, Senior, Graduate |
| gpa | DECIMAL(3,2) | Cumulative GPA |
| total_credits | INTEGER | Earned credits |
| advisor_id | VARCHAR(10) | Assigned advisor ID |
| enrollment_date | DATE | Initial enrollment date |
| expected_graduation | DATE | Expected graduation date |

### advising.advising_interactions

| Column | Type | Description |
|--------|------|-------------|
| interaction_id | INTEGER | Primary key |
| student_id | VARCHAR(10) | Student identifier |
| major | VARCHAR(50) | Student's major |
| department | VARCHAR(50) | Academic department |
| advisor_id | VARCHAR(10) | Advisor identifier |
| advisor_name | VARCHAR(100) | Advisor full name |
| interaction_date | DATE | Meeting date |
| interaction_type | VARCHAR(50) | Academic Advising, Career Counseling, Personal Support, Registration Help, Graduation Planning |
| duration_minutes | INTEGER | Meeting duration |
| meeting_format | VARCHAR(20) | In-Person, Virtual, Phone, Email |
| notes | VARCHAR(500) | Meeting notes |
| follow_up_required | BOOLEAN | Follow-up flag |

---

## Troubleshooting

### "Error connecting to database"
- Verify the database `DEMO_HE_STREAMLIT` exists
- Check that your role has USAGE grants on the database and schemas
- Ensure SELECT grants are in place for all tables

### Files not showing in stage
- Verify you uploaded to the correct stage: `@staging.he_data_stage`
- Check file names match exactly (case-sensitive)
- Run `LIST @staging.he_data_stage;` to see staged files

### COPY INTO shows 0 rows loaded
- Verify files are in the stage with `LIST @staging.he_data_stage;`
- Check file format matches CSV structure
- Look for errors: `SELECT * FROM TABLE(VALIDATE(finance.financial_aid, JOB_ID => '_last'));`

### No schemas/tables appear in app
- Run the SQL setup script completely
- Verify no errors occurred during table creation
- Check information_schema access permissions

### Filters not working
- Refresh the page to clear cached data
- Verify the column contains non-null values
- Check for data type mismatches

### Charts not displaying
- Ensure at least 2 unique values exist in categorical columns
- Verify numeric columns contain valid numbers
- Apply fewer filters to increase data volume

---

## Cleanup (Optional)

To remove staged files after successful load:

```sql
REMOVE @staging.he_data_stage;
```

To completely remove the demo:

```sql
DROP DATABASE demo_he_streamlit;
```

---

## Customization

### Adding New Tables
1. Create CSV file with data
2. Upload to stage: `PUT file://new_table.csv @staging.he_data_stage`
3. Create table DDL
4. Run COPY INTO command
5. Refresh Streamlit app - new tables appear automatically

### Modifying Filters
Edit `streamlit_app.py` to customize:
- `filter_columns.head(12)` - Change number of filterable columns
- `categorical_cols[:6]` - Limit categorical filters displayed
- `unique_values <= 50` - Threshold for dropdown vs. text input

### Styling
Modify the CSS in the `<style>` block to match your organization's branding.

---

## Support

For issues or feature requests, please contact your Snowflake administrator or data team.
