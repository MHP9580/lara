from app import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from sqlalchemy import func, Numeric

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    profile_picture = db.Column(db.String(200), default='default-avatar.svg')
    password_hash = db.Column(db.String(256), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    premium_end_date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    listings = db.relationship('Listing', backref='user', lazy=True, cascade='all, delete-orphan')
    premium_requests = db.relationship('PremiumRequest', backref='user', lazy=True, cascade='all, delete-orphan')
    sent_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.receiver_id', backref='receiver', lazy=True)

    def __repr__(self):
        return f'<User {self.phone_number}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_premium_active(self):
        if not self.is_premium:
            return False
        if self.premium_end_date and self.premium_end_date < datetime.utcnow():
            return False
        return True

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-tag')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    listings = db.relationship('Listing', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Listing(db.Model):
    __tablename__ = 'listings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(Numeric(12, 2), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_sold = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Relationships
    images = db.relationship('ListingImage', backref='listing', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Listing {self.title}>'
    
    @property
    def main_image(self):
        if self.images:
            return self.images[0].image_path
        return 'default-product.svg'
    
    @property
    def is_premium_listing(self):
        return self.user.is_premium_active

class ListingImage(db.Model):
    __tablename__ = 'listing_images'
    
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    
    # Foreign Keys
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)

class PremiumRequest(db.Model):
    __tablename__ = 'premium_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_phone = db.Column(db.String(15), nullable=False)
    amount = db.Column(Numeric(10, 2))
    payment_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    processed_by = db.Column(db.Integer, db.ForeignKey('admins.id'))

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'))

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    profile_picture = db.Column(db.String(200), default='default-admin.svg')
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='moderator')  # moderator, super_admin
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    processed_requests = db.relationship('PremiumRequest', backref='admin_processor', lazy=True)

    def __repr__(self):
        return f'<Admin {self.username}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'
