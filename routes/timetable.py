"""
DEPRECATED: This module requires SQLAlchemy ORM which is not configured.

The timetable functionality is currently handled through:
- Direct SQL queries in app.py 
- Student/Faculty dashboards with inline timetable queries

TODO: Rewrite this module to use raw SQL queries compatible with DatabaseManager
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
from database.database import db
import logging

logger = logging.getLogger(__name__)

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/timetable', methods=['GET'])
def view_timetable():
    """View timetable - currently disabled, use dashboard instead"""
    flash('Timetable view is currently under maintenance. Please check your dashboard.', 'info')
    return redirect(url_for('dashboard'))

# All legacy SQLAlchemy-based code has been removed
# Timetable queries are now handled through raw SQL in the main app and dashboard routes
