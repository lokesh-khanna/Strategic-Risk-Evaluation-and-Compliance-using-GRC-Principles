from flask import Flask
import os
from dotenv import load_dotenv

# Load environment variables before creating app
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Direct config from environment
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'grc_db')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30-min timeout (PCI-DSS Req 8.2.8)
    
    # Initialize session secret key
    app.secret_key = app.config['SECRET_KEY']
    
    # Register blueprints IN THIS EXACT ORDER
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    from app.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    from app.risk import risk_bp
    app.register_blueprint(risk_bp)
    
    from app.compliance import compliance_bp
    app.register_blueprint(compliance_bp)
    
    from app.audit import audit_bp
    app.register_blueprint(audit_bp)
    # Root route - redirects to login
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    return app