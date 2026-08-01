import pandas as pd
import pymysql

# MySQL Connection
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="root",   # put your mysql password here if any
    database="attendance_system"
)

cursor = conn.cursor()

# Read CSV
df = pd.read_csv("student_data_sas.csv")

inserted = 0

for _, row in df.iterrows():

    sr_no = int(row["Srno"])
    institute = str(row["Institute"])
    enrollment_no = str(row["Enrollment No"])
    full_name = str(row["Student Full Name"])

    query = """
    INSERT IGNORE INTO students
    (sr_no, institute, enrollment_no, full_name, department, year)
    VALUES (%s,%s,%s,%s,%s,%s)
    """

    values = (
        sr_no,
        institute,
        enrollment_no,
        full_name,
        "Information Technology",
        4
    )

    cursor.execute(query, values)

    if cursor.rowcount > 0:
        inserted += 1

conn.commit()

print(f"\n✅ {inserted} students inserted successfully!")

cursor.close()
conn.close()