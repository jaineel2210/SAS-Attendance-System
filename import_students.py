import csv
import pymysql

# CHANGE THESE IF NEEDED
HOST = "localhost"
USER = "root"
PASSWORD = "root"
DATABASE = "attendance_system"
CSV_FILE = "student_data_sas.csv"

conn = pymysql.connect(
    host=HOST,
    user=USER,
    password=PASSWORD,
    database=DATABASE,
    charset="utf8mb4",
    autocommit=True
)

cursor = conn.cursor()

count = 0

with open(CSV_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        cursor.execute("""
        INSERT IGNORE INTO students
        (sr_no, institute, enrollment_no, full_name, department, year)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            row["Srno"],
            row["Institute"],
            row["Enrollment No"],
            row["Student Full Name"],
            "Information Technology",
            4
        ))
        count += 1

print(f"Successfully imported {count} students")

cursor.close()
conn.close()
