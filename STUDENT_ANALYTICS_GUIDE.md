# Student Analytics System - Setup & Usage Guide

## Overview

This document provides comprehensive instructions for setting up and using the advanced Student Analytics System integrated into SecureAttend Pro.

---

## Features Implemented ✓

### 1. Database Design
- ✓ **students** table with proper structure
  - Auto-increment ID
  - Unique enrollment numbers
  - Automatic name parsing (first, middle, last)
  - Year extraction from enrollment numbers
  - Institute and department tracking

- ✓ **attendance_records** table
  - Links to students via enrollment number
  - Subject and faculty tracking
  - Date and timestamp recording
  - Status tracking (Present/Absent)

### 2. CSV Import Functionality
- ✓ Flask route: `/import-students`
- ✓ File validation (.csv only)
- ✓ Duplicate detection and skipping
- ✓ Automatic data cleaning and formatting
- ✓ Name parsing and capitalization
- ✓ Year extraction from enrollment numbers
- ✓ Detailed import statistics

### 3. Admin Analytics Dashboard
- ✓ Route: `/admin/analytics`
- ✓ **Basic Stats Cards:**
  - Total Students
  - Total Attendance Records
  - Average Attendance %
  - Students Below 75%

- ✓ **Institute-Based Analytics:**
  - Students per institute
  - Attendance percentage by institute

- ✓ **Name Pattern Analytics:**
  - Top 5 most common surnames
  - Count by surname

- ✓ **Enrollment Year Analytics:**
  - Year-wise student distribution
  - Interactive bar chart

- ✓ **Risk Detection System:**
  - High Risk (<60%) - Red
  - Medium Risk (60-75%) - Orange
  - Safe (>75%) - Green
  - Detailed student lists

- ✓ **Monthly Trend Graph:**
  - 6-month attendance trend
  - Interactive line chart

### 4. Faculty Analytics Dashboard
- ✓ Route: `/faculty/analytics`
- ✓ **Students List:**
  - Paginated view (20 per page)
  - Attendance % per student
  
- ✓ **Top 5 Regular Students:**
  - Ranked by attendance
  - Trophy icons for top 3

- ✓ **Students Below 75%:**
  - Filterable list
  - Risk level indicators

- ✓ **Daily Attendance Summary:**
  - Date-wise statistics
  - Subject-wise breakdown

- ✓ **Filters:**
  - Subject filter
  - Date filter
  - Search by enrollment number
  - Search by surname

### 5. Professional Features
- ✓ Export attendance report to CSV
- ✓ Export students list to CSV
- ✓ Pagination for large datasets
- ✓ Search functionality
- ✓ Filter by multiple criteria
- ✓ AJAX-ready API endpoints
- ✓ Responsive design
- ✓ Color-coded risk indicators

---

## Installation & Setup

### Step 1: Install Dependencies

All required packages are already in `requirements.txt`. Ensure pandas is installed:

```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database Tables

Run the initialization script:

```bash
python init_student_system.py
```

This will:
1. Create the `students` table
2. Create the `attendance_records` table
3. Optionally import data from your CSV file

### Step 3: Configure Database

Ensure your `config.py` has correct MySQL settings:

```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DATABASE = 'attendance_system'
```

### Step 4: Start the Application

```bash
python app.py
```

Or using the provided batch file:

```bash
start_server.bat
```

---

## Usage Guide

### For Admins

#### 1. Import Student Data from CSV

1. Login as admin
2. Navigate to `/import-students` or use the button in analytics dashboard
3. Upload your CSV file
4. View import statistics
5. Check for any errors or duplicates

**CSV Format:**
```csv
Srno,Institute,Enrollment No,Student Full Name
1,SOCET,2201031000001,AMIT KUMAR MAURYA
2,SOCET,2201031000002,PATEL DHWANIL JAYESHBHAI
```

#### 2. View Analytics Dashboard

1. Navigate to `/admin/analytics`
2. View comprehensive statistics:
   - Basic stats cards
   - Institute analytics
   - Surname analytics
   - Year distribution chart
   - Risk detection system
   - Monthly trend graph

#### 3. Export Data

- **Export Students List:** Click "Export Students" button
- **Export Attendance Report:** Use the export feature in faculty analytics

### For Faculty

#### 1. View Faculty Analytics

1. Login as faculty
2. Navigate to `/faculty/analytics`
3. View your subject-specific analytics

#### 2. Use Filters

- **Subject Filter:** Select specific subject
- **Date Filter:** View attendance for specific date
- **Search by Enrollment:** Find specific student
- **Search by Surname:** Filter by last name

#### 3. Identify At-Risk Students

- View "Students Below 75%" section
- Check risk levels (High/Medium)
- Take necessary action

#### 4. Export Reports

Click "Export Report" button to download CSV with:
- Student enrollment numbers
- Names
- Subject
- Faculty
- Dates
- Status
- Timestamps

---

## API Endpoints

### CSV Upload
```
POST /upload-csv
Content-Type: multipart/form-data
Body: csv_file (file)
```

### Admin Analytics Stats (AJAX)
```
GET /api/admin/analytics/stats
Returns: JSON with basic statistics
```

### Monthly Trend Data (AJAX)
```
GET /api/admin/analytics/monthly-trend?months=6
Returns: JSON with trend data
```

### Faculty Students List (AJAX)
```
GET /api/faculty/students?page=1&subject=Math&search_enrollment=2201
Returns: JSON with paginated student list
```

### Export Attendance Report
```
GET /export/attendance-report?subject=Math&from_date=2024-01-01&to_date=2024-12-31
Returns: CSV file
```

### Export Students List
```
GET /export/students-list
Returns: CSV file
```

---

## Database Schema

### students Table

```sql
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sr_no INT,
    institute VARCHAR(100) DEFAULT 'SOCET',
    enrollment_no VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    last_name VARCHAR(100),
    department VARCHAR(100) DEFAULT 'SOCET',
    year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_enrollment (enrollment_no),
    INDEX idx_last_name (last_name),
    INDEX idx_year (year)
);
```

### attendance_records Table

```sql
CREATE TABLE attendance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_no VARCHAR(20) NOT NULL,
    subject_name VARCHAR(100),
    faculty_name VARCHAR(100),
    date DATE NOT NULL,
    status ENUM('Present', 'Absent') DEFAULT 'Present',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_no) REFERENCES students(enrollment_no) ON DELETE CASCADE,
    INDEX idx_enrollment (enrollment_no),
    INDEX idx_date (date),
    INDEX idx_subject (subject_name)
);
```

---

## Color Theme

The system uses a **Deep Blue + Teal** color scheme throughout:

- **Primary Blue:** `#0d6efd`
- **Teal Accent:** `#17a2b8`, `#20c997`
- **Gradients:** Various blue-purple-teal gradients
- **Risk Colors:**
  - High Risk: Red (`#dc3545`)
  - Medium Risk: Orange/Yellow (`#ffc107`)
  - Safe: Green (`#20c997`)

---

## File Structure

```
SAS_project/
├── database/
│   └── database.py (updated with new tables)
├── utils/
│   └── student_analytics.py (NEW - analytics service)
├── routes/
│   └── student_management.py (NEW - routes for CSV import & analytics)
├── templates/
│   ├── admin/
│   │   ├── import_students.html (NEW)
│   │   └── admin_analytics_dashboard.html (NEW)
│   └── faculty/
│       └── faculty_analytics_dashboard.html (NEW)
├── student_data_sas.csv (your data file)
├── init_student_system.py (NEW - initialization script)
└── STUDENT_ANALYTICS_GUIDE.md (this file)
```

---

## Troubleshooting

### Issue: Tables not created
**Solution:** Run `python init_student_system.py` to create tables

### Issue: CSV import fails
**Solution:** 
- Check CSV format matches requirements
- Ensure column names are: Srno, Institute, Enrollment No, Student Full Name
- Verify file encoding is UTF-8

### Issue: Duplicate enrollment numbers
**Solution:** System automatically skips duplicates. Check import statistics.

### Issue: Analytics showing no data
**Solution:** 
- Ensure students are imported
- Add attendance records to attendance_records table
- Check database connection

### Issue: Charts not displaying
**Solution:** 
- Ensure Chart.js is loaded (CDN)
- Check browser console for errors
- Verify data is present in database

---

## Best Practices

1. **Import Students First:** Always import student master data before adding attendance records

2. **Regular Backups:** Export students list and attendance reports regularly

3. **Monitor At-Risk Students:** Check risk detection daily/weekly

4. **Use Filters:** Utilize subject and date filters for focused analysis

5. **Data Validation:** Review import statistics after CSV upload

6. **Performance:** For large datasets (1000+ students), use pagination and filters

---

## Support & Maintenance

### Maintenance Tasks

1. **Weekly:** Export backup of students and attendance data
2. **Monthly:** Review attendance trends and risk levels
3. **Semester:** Clean up old attendance records if needed

### Database Optimization

The system includes indexes on:
- enrollment_no (for fast lookups)
- last_name (for surname searches)
- year (for year-wise queries)
- date (for date-range queries)
- subject_name (for subject filters)

---

## Future Enhancements

Potential features for future versions:

- [ ] Bulk attendance marking from CSV
- [ ] Email notifications for at-risk students
- [ ] Mobile app integration
- [ ] Real-time analytics updates via WebSocket
- [ ] Machine learning predictions
- [ ] Custom report builder
- [ ] Student performance correlation
- [ ] Automated reminder system

---

## Credits

**SecureAttend Pro - Student Analytics System**

Developed by: SecureAttend Pro Team
Version: 1.0
Date: February 2026

For support, contact your system administrator.

---

## License

Copyright © 2025 Jaineel Pandya, Dhwanil Patel. All rights reserved.

---

**END OF GUIDE**
