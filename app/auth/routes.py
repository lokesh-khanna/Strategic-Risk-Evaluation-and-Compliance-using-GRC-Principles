"""
Authentication routes: login, logout, access control
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.utils import login_user, logout_user, get_user_roles, verify_password
from app.db import db

from . import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication handler"""
    # Redirect if already logged in
    if session.get('logged_in'):
        return redirect(url_for('dashboard.view'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('auth/login.html'), 400
        
        try:
            # Retrieve user with password hash
            users = db.execute_query(
                "SELECT user_id, username, password_hash, is_active FROM users WHERE username = %s",
                (username,),
                fetch=True
            )
            
            if not users:
                flash('Invalid username or password.', 'danger')
                return render_template('auth/login.html'), 401
            
            user = users[0]
            
            # Check if user is active
            if not user['is_active']:
                flash('Account is deactivated. Contact administrator.', 'danger')
                return render_template('auth/login.html'), 403
            
            # Verify password
            if not verify_password(password, user['password_hash']):
                flash('Invalid username or password.', 'danger')
                return render_template('auth/login.html'), 401
            
            # Get user roles
            user_roles = get_user_roles(user['user_id'])
            
            if not user_roles:
                flash('User has no assigned roles. Contact administrator.', 'danger')
                return render_template('auth/login.html'), 403
            
            # Create session
            login_user(user['user_id'], user['username'], user_roles)
            
            # Log audit event
            try:
                db.execute_query(
                    """INSERT INTO audit_logs (user_id, action, details, ip_address)
                       VALUES (%s, %s, %s, %s)""",
                    (
                        user['user_id'],
                        'USER_LOGIN',
                        '{"event": "successful_login"}',
                        request.remote_addr,
                    )
                )
            except Exception as e:
                print(f"Audit log failed: {e}")
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            
            # Redirect based on primary role
            if 'admin' in user_roles:
                return redirect(url_for('dashboard.view'))
            elif 'risk_manager' in user_roles:
                return redirect(url_for('risk.register'))
            elif 'compliance_officer' in user_roles:
                return redirect(url_for('compliance.controls'))
            elif 'auditor' in user_roles:
                return redirect(url_for('audit.trail'))
            else:
                return redirect(url_for('dashboard.view'))
                
        except Exception as e:
            flash('An error occurred during login. Please try again.', 'danger')
            print(f"Login error: {e}")
            return render_template('auth/login.html'), 500
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Logout handler"""
    user_id = session.get('user_id')
    
    # Log audit event before clearing session
    if user_id:
        try:
            db.execute_query(
                """INSERT INTO audit_logs (user_id, action, details, ip_address)
                   VALUES (%s, %s, %s, %s)""",
                (
                    user_id,
                    'USER_LOGOUT',
                    '{"event": "user_logout"}',
                    request.remote_addr,
                )
            )
        except Exception as e:
            print(f"Audit log failed: {e}")
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/unauthorized')
def unauthorized():
    """Access denied page"""
    return render_template('auth/unauthorized.html'), 403