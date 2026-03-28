"""
Authentication utilities: password hashing, session management, RBAC checks
"""
from flask import session, redirect, url_for, flash
from functools import wraps
from app.db import db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def hash_password(password):
    """Hash password using bcrypt (cost factor 12)"""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.check_password_hash(password_hash, password)

def login_user(user_id, username, roles):
    """Create authenticated session"""
    session.clear()  # Clear any existing session data
    session['user_id'] = user_id
    session['username'] = username
    session['roles'] = roles  # List of role names
    session['logged_in'] = True
    session.permanent = True  # Use app.config['PERMANENT_SESSION_LIFETIME']
    
    # Update last_login timestamp
    try:
        db.execute_query(
            "UPDATE users SET last_login = NOW() WHERE user_id = %s",
            (user_id,)
        )
    except Exception as e:
        print(f"Warning: Failed to update last_login: {e}")

def logout_user():
    """Destroy session"""
    session.clear()

def get_current_user():
    """Get current authenticated user data"""
    if not session.get('logged_in'):
        return None
    
    try:
        user = db.execute_query(
            "SELECT user_id, username, full_name, email FROM users WHERE user_id = %s AND is_active = TRUE",
            (session['user_id'],),
            fetch=True
        )
        if user:
            return user[0]
        else:
            logout_user()  # User not found or inactive
            return None
    except Exception as e:
        print(f"Error retrieving current user: {e}")
        return None

def get_user_roles(user_id):
    """Get all role names for a user"""
    roles = db.execute_query("""
        SELECT r.role_name
        FROM user_roles ur
        INNER JOIN roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = %s
    """, (user_id,), fetch=True)
    return [role['role_name'] for role in roles]

def has_role(required_role):
    """Check if current user has required role"""
    if not session.get('logged_in'):
        return False
    
    user_roles = session.get('roles', [])
    return required_role in user_roles

def has_any_role(*required_roles):
    """Check if current user has any of the required roles"""
    if not session.get('logged_in'):
        return False
    
    user_roles = session.get('roles', [])
    return any(role in user_roles for role in required_roles)

# ========== RBAC DECORATORS FOR ROUTE PROTECTION ==========

def login_required(f):
    """Decorator: Require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Decorator factory: Require specific role
    Usage: @role_required('admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not has_role(role_name):
                flash(f'Access denied. Requires {role_name} role.', 'danger')
                # Redirect based on user's role
                if has_role('auditor'):
                    return redirect(url_for('dashboard.view'))
                elif has_role('risk_manager'):
                    return redirect(url_for('risk.register'))
                elif has_role('compliance_officer'):
                    return redirect(url_for('compliance.controls'))
                else:
                    return redirect(url_for('dashboard.view'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def any_role_required(*role_names):
    """
    Decorator factory: Require any of the specified roles
    Usage: @any_role_required('risk_manager', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not has_any_role(*role_names):
                flash(f'Access denied. Requires one of: {", ".join(role_names)}', 'danger')
                return redirect(url_for('dashboard.view'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator