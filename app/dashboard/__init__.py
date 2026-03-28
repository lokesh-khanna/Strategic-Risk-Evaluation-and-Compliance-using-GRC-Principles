"""
Dashboard module blueprint
"""
from flask import Blueprint

# Create blueprint instance
dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

# Import routes to register them with blueprint
from . import routes