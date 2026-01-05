#!/usr/bin/env python3
"""
Database schema update script for multi-session attendance system
"""
from database.database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database_schema():
    """Update database schema for multi-session attendance"""
    try:
        db.connect()
        logger.info("Connected to database")
        
        # Read and execute SQL file
        with open('database/update_schema.sql', 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for stmt in statements:
            try:
                result = db.execute_query(stmt)
                logger.info(f"Executed: {stmt[:50]}... - Result: {result}")
            except Exception as e:
                logger.error(f"Error executing statement: {stmt[:50]}... - Error: {e}")
                
        logger.info("Database schema update completed")
        
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
    finally:
        db.disconnect()

if __name__ == "__main__":
    update_database_schema()