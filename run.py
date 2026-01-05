from app import app
from database.database import db

if __name__ == '__main__':
    # Initialize database on startup
    with app.app_context():
        if db.connect():
            db.create_tables()
            db.insert_sample_data()
            print("Database initialized successfully")
        else:
            print("Failed to initialize database")
    
    app.run(debug=True, host='0.0.0.0', port=5000)