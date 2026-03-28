"""
Authentication module blueprint
"""
from flask import Blueprint

# Create blueprint instance FIRST
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Import routes AFTER blueprint creation
from . import routes