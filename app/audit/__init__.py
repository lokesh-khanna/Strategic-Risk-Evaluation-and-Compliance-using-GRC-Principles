"""
Audit Trail module blueprint
"""
from flask import Blueprint

# Create blueprint instance
audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

from . import routes