import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///congo_connect.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    # Import models and routes
    import models
    import routes
    import admin_routes
    import chat_routes
    
    # Create all database tables
    db.create_all()
    
    # Create default super admin if not exists
    from models import Admin, Category
    from werkzeug.security import generate_password_hash
    
    super_admin = Admin.query.filter_by(username='superadmin').first()
    if not super_admin:
        super_admin = Admin(
            username='superadmin',
            email='admin@congoconnect.com',
            phone_number='242000000000',
            first_name='Super',
            last_name='Admin',
            password_hash=generate_password_hash('admin123'),
            role='super_admin'
        )
        db.session.add(super_admin)
        db.session.commit()
        logging.info("Default super admin created: username=superadmin, password=admin123")
    
    # Create default categories
    if Category.query.count() == 0:
        categories = [
            {'name': 'Électronique', 'icon': 'fas fa-laptop'},
            {'name': 'Vêtements', 'icon': 'fas fa-tshirt'},
            {'name': 'Maison & Jardin', 'icon': 'fas fa-home'},
            {'name': 'Véhicules', 'icon': 'fas fa-car'},
            {'name': 'Services', 'icon': 'fas fa-handshake'},
            {'name': 'Emploi', 'icon': 'fas fa-briefcase'},
            {'name': 'Immobilier', 'icon': 'fas fa-building'},
            {'name': 'Loisirs', 'icon': 'fas fa-gamepad'},
        ]
        
        for cat_data in categories:
            category = Category(**cat_data)
            db.session.add(category)
        
        db.session.commit()
        logging.info("Default categories created")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
