# SecureAttend Pro - Biometric & RFID Attendance Management System

A comprehensive attendance management system combining face recognition, RFID technology, and OTP-based authentication for educational institutions.

## 🎯 Project Overview

**Problem Statement**: Educational institutions need secure, accurate, and efficient attendance tracking systems that prevent proxy attendance and provide real-time analytics.

**Solution**: SecureAttend Pro uses dual authentication (face recognition + RFID) with OTP verification for enhanced security and accuracy.

## ✅ **LATEST UPDATE - FACE REGISTRATION FIXED**

**Issue Resolved**: "Face capture failed: No stored face encoding found" during student registration

**Fix Applied**:
- Created `store_face_encoding()` method for new user registration
- Updated `/capture_face` route to properly handle first-time face capture
- Now correctly stores face encodings during registration instead of trying to verify against non-existent encodings
- Application is **FULLY FUNCTIONAL** and ready for use

## 🚀 **Current Status: READY TO USE** ✅

- ✅ Database setup working
- ✅ Flask app running on http://127.0.0.1:5000
- ✅ Face registration completely fixed
- ✅ All templates and routes functional
- ✅ Authentication system working
- ✅ OTP system configured (with simulation for testing)
- ✅ Analytics dashboard operational

## 🚀 Key Features

### Core Functionality
- **Face Recognition Attendance**: Advanced facial recognition using OpenCV and face_recognition
- **RFID Integration**: Quick card-based verification
- **OTP Authentication**: SMS-based verification for registration and admin access
- **Real-time Analytics**: Comprehensive attendance tracking and reporting
- **Role-based Access Control**: Separate interfaces for Admin, Faculty, and Students

### Security Features
- **Anti-Proxy Technology**: Dual authentication prevents fake attendance
- **Data Encryption**: Face encodings and sensitive data encrypted
- **Session Management**: Secure user sessions with timeout
- **Activity Logging**: Complete audit trail of system activities
- **Input Validation**: Comprehensive data validation and sanitization

### Analytics & Reporting
- **Date-wise Attendance**: Daily, weekly, monthly reports
- **Subject-wise Analysis**: Separate tracking for lectures and labs
- **Percentage Calculations**: Automatic attendance percentage computation
- **Visual Charts**: Interactive graphs using Chart.js and Plotly
- **Real-time Dashboard**: Live attendance monitoring

## 📋 Technology Stack

### Backend
- **Python 3.8+**: Core programming language
- **Flask**: Web framework for UI/UX
- **MySQL**: Primary database for data storage
- **OpenCV**: Computer vision for face recognition
- **face_recognition**: Advanced facial recognition library

### Frontend
- **HTML5/CSS3**: Modern web standards
- **Bootstrap 5**: Responsive UI framework
- **JavaScript**: Interactive functionality
- **Chart.js**: Data visualization
- **Font Awesome**: Icon library

### Security & Communication
- **bcrypt**: Password hashing
- **Twilio**: SMS/OTP service
- **PySerial**: RFID reader communication
- **cryptography**: Data encryption

## 🏗 Project Structure

```
SecureAttend_Pro/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── run.py                          # Application entry point
├── .env                           # Environment variables
├── database/
│   └── database.py                # Database management
├── auth/
│   └── authentication.py         # User authentication
├── face_recognition/
│   └── face_processor.py         # Face recognition logic
├── rfid/
│   └── rfid_reader.py            # RFID integration
├── utils/
│   ├── otp_service.py            # SMS/OTP services
│   └── analytics.py              # Attendance analytics
├── templates/
│   ├── base.html                 # Base template
│   ├── index.html                # Home page
│   ├── login.html                # Login interface
│   ├── register.html             # Registration flow
│   └── dashboard/                # Role-specific dashboards
└── static/
    ├── uploads/                  # File uploads
    └── face_images/             # Face recognition images
```

## 👥 Team Division (3 Members)

### Member 1: Backend & Database Developer
**Responsibilities:**
- Database design and MySQL integration (`database/database.py`)
- User authentication system (`auth/authentication.py`)
- RFID sensor integration (`rfid/rfid_reader.py`)
- Security implementation and OTP services (`utils/otp_service.py`)
- System configuration (`config.py`, `.env`)

**Files to Work On:**
- `database/database.py`
- `auth/authentication.py` 
- `rfid/rfid_reader.py`
- `utils/otp_service.py`
- `config.py`

### Member 2: Face Recognition & Computer Vision
**Responsibilities:**
- OpenCV face recognition implementation (`face_recognition/face_processor.py`)
- Camera integration and image processing
- Face encoding and matching algorithms
- Real-time video processing
- Face capture during registration

**Files to Work On:**
- `face_recognition/face_processor.py`
- Face capture components in templates
- Camera integration scripts
- Image processing utilities

### Member 3: Frontend & Analytics Developer
**Responsibilities:**
- Flask dashboard development (`app.py`, templates)
- UI/UX design and responsiveness
- Charts and analytics implementation (`utils/analytics.py`)
- Student management interface
- Frontend JavaScript functionality

**Files to Work On:**
- `app.py` (Flask routes and views)
- All template files (`templates/*.html`)
- `utils/analytics.py`
- CSS styling and JavaScript
- Dashboard interfaces

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MySQL Server 8.0+
- Camera/Webcam for face recognition
- RFID reader hardware (optional for testing)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd SecureAttend_Pro
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Database Setup
1. Create MySQL database:
```sql
CREATE DATABASE attendance_system;
```

2. Update database credentials in `.env`:
```env
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=attendance_system
```

### Step 4: Configure Services
1. **Twilio Setup** (for SMS/OTP):
   - Sign up at [Twilio](https://www.twilio.com)
   - Get Account SID, Auth Token, and Phone Number
   - Update `.env` file with credentials

2. **RFID Reader Setup**:
   - Connect RFID reader to USB port
   - Update `RFID_PORT` in `.env` (e.g., COM3 for Windows, /dev/ttyUSB0 for Linux)

### Step 5: Run Application
```bash
python run.py
```

Access the application at `http://localhost:5000`

## 🔧 VS Code Extensions Required

1. **Python** - Python language support
2. **MySQL** - Database management
3. **Flask Snippets** - Flask development shortcuts
4. **HTML CSS Support** - Web development
5. **JavaScript (ES6) code snippets** - JS development
6. **Bootstrap 4, Font awesome snippets** - UI components
7. **Live Server** - Local development server
8. **Python Docstring Generator** - Documentation
9. **Auto Rename Tag** - HTML tag management
10. **Bracket Pair Colorizer** - Code readability

## 📱 RFID Hardware Setup

### Required Components
- RC522 RFID Reader Module
- RFID Cards/Tags (125kHz or 13.56MHz)
- Arduino Uno/Nano (for USB interface)
- USB to Serial Converter
- Jumper wires

### Connections (Arduino-based)
```
RC522 Module → Arduino Pins
VCC → 3.3V
RST → Pin 9
GND → GND
MISO → Pin 12
MOSI → Pin 11
SCK → Pin 13
SDA → Pin 10
```

### Arduino Code
```cpp
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN 9
#define SS_PIN 10

MFRC522 mfrc522(SS_PIN, RST_PIN);

void setup() {
    Serial.begin(9600);
    SPI.begin();
    mfrc522.PCD_Init();
}

void loop() {
    if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
        return;
    }
    
    String uid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
        uid += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
        uid += String(mfrc522.uid.uidByte[i], HEX);
    }
    
    Serial.println(uid.toUpperCase());
    mfrc522.PICC_HaltA();
}
```

## 🔐 Security Implementation

### Data Protection
- **Face Encodings**: Encrypted using base64 + pickle
- **Passwords**: Hashed using bcrypt with salt
- **Sessions**: Secure session management with timeouts
- **Input Validation**: SQL injection and XSS prevention

### Access Control
- **Role-based Permissions**: Admin, Faculty, Student roles
- **OTP Verification**: 30-second expiry for enhanced security
- **Anti-tampering**: Dual authentication prevents proxy attendance
- **Activity Logging**: Complete audit trail

### Network Security
- **HTTPS Ready**: SSL/TLS configuration support
- **CSRF Protection**: Cross-site request forgery prevention
- **Rate Limiting**: Brute force attack prevention

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    enrollment_no VARCHAR(20) UNIQUE NOT NULL,
    mobile_number VARCHAR(15) NOT NULL,
    role ENUM('admin', 'faculty', 'student') DEFAULT 'student',
    password_hash VARCHAR(255),
    face_encoding TEXT,
    rfid_uid VARCHAR(50),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Attendance Table
```sql
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    faculty_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL,
    session_type ENUM('lecture', 'lab') DEFAULT 'lecture',
    attendance_date DATE NOT NULL,
    attendance_time TIME NOT NULL,
    status ENUM('P', 'A') DEFAULT 'P',
    marked_by_face BOOLEAN DEFAULT FALSE,
    marked_by_rfid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 Usage Instructions

### For Students
1. **Registration**: Provide name, enrollment number, mobile
2. **OTP Verification**: Enter 6-digit code (30-second validity)
3. **Face Capture**: Position face clearly for encoding
4. **RFID Registration**: Tap ID card on reader
5. **Attendance Marking**: Use face + RFID for daily attendance

### For Faculty
1. **Login**: Use credentials (no OTP required)
2. **Start Session**: Select subject and session type
3. **Monitor Attendance**: Real-time student count display
4. **View Analytics**: Access attendance reports and charts

### For Administrators
1. **Login**: Credentials + OTP verification required
2. **Manage Users**: Add/remove students and faculty
3. **System Monitoring**: View security logs and statistics
4. **Analytics**: Access comprehensive reports

## 🔍 Troubleshooting

### Common Issues
1. **Camera Not Working**: Check permissions and driver installation
2. **RFID Not Detected**: Verify COM port and hardware connections
3. **OTP Not Received**: Check Twilio credentials and mobile number format
4. **Database Connection**: Verify MySQL service and credentials

### Debug Mode
Enable debug logging in `config.py`:
```python
DEBUG = True
```

## 🚀 Future Enhancements

1. **Mobile App**: Android/iOS companion app
2. **Cloud Integration**: AWS/Azure deployment support
3. **AI Analytics**: Predictive attendance patterns
4. **Blockchain**: Immutable attendance records
5. **IoT Integration**: Smart classroom devices
6. **Multi-language**: Support for regional languages

## 📞 Support & Contact

For technical support and queries:
- **Documentation**: Check README and code comments
- **Issues**: Create GitHub issues for bugs
- **Enhancements**: Submit feature requests

## 📄 License

This project is developed for educational purposes. All rights reserved.

---

**SecureAttend Pro** - *Revolutionizing Attendance Management with Advanced Security*