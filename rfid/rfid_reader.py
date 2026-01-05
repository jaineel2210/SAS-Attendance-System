import serial
import time
import threading
import queue
import logging
from config import Config

logger = logging.getLogger(__name__)

class RFIDReader:
    def __init__(self):
        self.port = Config.RFID_PORT
        self.baudrate = Config.RFID_BAUDRATE
        self.connection = None
        self.is_reading = False
        self.card_queue = queue.Queue()
        self.read_thread = None

    def connect(self):
        """Connect to RFID reader"""
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            logger.info(f"Connected to RFID reader on {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to RFID reader: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to RFID reader: {e}")
            return False

    def disconnect(self):
        """Disconnect from RFID reader"""
        self.stop_reading()
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("RFID reader disconnected")

    def start_reading(self):
        """Start reading RFID cards in a separate thread"""
        if not self.connection or not self.connection.is_open:
            if not self.connect():
                return False
        
        self.is_reading = True
        self.read_thread = threading.Thread(target=self._read_cards, daemon=True)
        self.read_thread.start()
        logger.info("Started RFID reading thread")
        return True

    def stop_reading(self):
        """Stop reading RFID cards"""
        self.is_reading = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        logger.info("Stopped RFID reading")

    def _read_cards(self):
        """Internal method to continuously read RFID cards"""
        while self.is_reading:
            try:
                if self.connection.in_waiting > 0:
                    # Read data from RFID reader
                    data = self.connection.readline().decode('utf-8').strip()
                    if data and len(data) >= 8:  # Valid RFID data
                        self.card_queue.put(data)
                        logger.info(f"RFID card detected: {data}")
                
                time.sleep(0.1)  # Small delay to prevent CPU overload
                
            except serial.SerialException as e:
                logger.error(f"Serial communication error: {e}")
                break
            except Exception as e:
                logger.error(f"Error reading RFID: {e}")
                break

    def get_card(self, timeout=5):
        """Get the next RFID card (blocking with timeout)"""
        try:
            return self.card_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def simulate_card_read(self, rfid_uid):
        """Simulate RFID card reading (for testing without hardware)"""
        if self.is_reading:
            self.card_queue.put(rfid_uid)
            logger.info(f"Simulated RFID card: {rfid_uid}")
            return True
        return False

    def register_card(self, enrollment_no):
        """Register RFID card for a user"""
        from database.database import db
        
        try:
            print(f"Please tap the RFID card for {enrollment_no}")
            print("Waiting for RFID card... (timeout: 10 seconds)")
            
            # For demonstration, we'll simulate card reading
            # In real implementation, this would read from actual RFID reader
            import random
            import string
            
            # Generate a random RFID UID for simulation
            rfid_uid = ''.join(random.choices(string.hexdigits.upper(), k=8))
            
            # In real implementation, use:
            # rfid_uid = self.get_card(timeout=10)
            
            if rfid_uid:
                # Update user with RFID UID
                query = "UPDATE users SET rfid_uid = %s WHERE enrollment_no = %s"
                result = db.execute_query(query, (rfid_uid, enrollment_no))
                
                if result:
                    logger.info(f"RFID card {rfid_uid} registered for {enrollment_no}")
                    return True, rfid_uid
                else:
                    return False, "Failed to register RFID card"
            else:
                return False, "No RFID card detected"
                
        except Exception as e:
            logger.error(f"Error registering RFID card: {e}")
            return False, f"Error: {e}"

    def verify_card(self, rfid_uid):
        """Verify RFID card and return user information"""
        from database.database import db
        
        try:
            query = "SELECT * FROM users WHERE rfid_uid = %s"
            result = db.execute_query(query, (rfid_uid,))
            
            if result:
                return True, result[0]
            else:
                return False, None
                
        except Exception as e:
            logger.error(f"Error verifying RFID card: {e}")
            return False, None

# Initialize RFID reader
rfid_reader = RFIDReader()

# RFID Hardware Setup Instructions (for README)
RFID_SETUP_INSTRUCTIONS = """
RFID Hardware Setup Instructions:

1. Required Components:
   - RC522 RFID Reader Module
   - RFID Cards/Tags
   - Arduino Uno/Nano (optional, for USB interface)
   - USB to Serial Converter (if not using Arduino)
   - Jumper wires

2. Connections (if using Arduino):
   RC522 -> Arduino
   VCC -> 3.3V
   RST -> Pin 9
   GND -> GND
   MISO -> Pin 12
   MOSI -> Pin 11
   SCK -> Pin 13
   SDA -> Pin 10

3. Arduino Code:
   Upload the provided RFID reader sketch to Arduino
   Configure serial communication at 9600 baud

4. Software Configuration:
   - Update RFID_PORT in .env file
   - Install PySerial: pip install pyserial
   - Test connection with provided test script

5. Alternative Setup (Direct USB):
   - Use USB RFID reader modules
   - Configure appropriate COM port
   - Install device drivers if required

For detailed setup instructions, refer to the hardware documentation.
"""