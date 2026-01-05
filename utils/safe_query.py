from database.database import db
import logging

logger = logging.getLogger(__name__)

def safe_execute_query(query, default_value=None):
    """Safely execute a database query and return default value if query fails"""
    try:
        result = db.execute_query(query)
        if result and len(result) > 0:
            return result[0]
        return default_value
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        return default_value
