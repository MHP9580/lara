import os
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_, func
from app import app, db
from models import User, Category, Listing, ListingImage, PremiumRequest, ChatMessage
from utils import validate_congolese_phone, save_image, calculate_distance, format_price, time_ago

# Template filters
app.jinja_env.filters['format_price'] = format_price
app.jinja_env.filters['time_ago'] = time_ago

@app.route('/')
def index():
    # Get search parameters
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    location = request.args.get('location', '')
    user_lat = request.args.get('lat', type=float)
    user_lon = request.args.get('lon', type=float)
    
    # Base query for active listings
    query = Listing.query.filter_by(is_active=True, is_sold=False)
    
    # Apply filters
    if search:
        query = query.filter(or_(
            Listing.title.contains(search),
            Listing.description.contains(search)
        ))
    
    if category_id:
        query = query.filter(Listing.category_id == category_id)
    
    if location:
        query = query.filter(Listing.location.contains(location))
    
    # Get all listings
    listings = query.all()
    
    # Sort by premium status and proximity
    def sort_key(listing):
        premium_score = 1000 if listing.is_premium_listing else 0
        distance_score = 0
        
        if user_lat and user_lon and listing.latitude and listing.longitude:
            distance = calculate_distance(user_lat, user_lon, listing.latitude, listing.longitude)
            distance_score = max(0, 100 - distance)  # Closer = higher score
        
        return -(premium_score + distance_score)  # Negative for descending order
    
    listings.sort(key=sort_key)
    
    # Get featured premium listings for homepage
    premium_listings = [l for l in listings if l.is_premium_listing][:6]
    recent_listings = sorted(listings, key=lambda x: x.created_at, reverse=True)[:8]
    
    # Get categories
    categories = Category.query.all()
    
    return render_template('index.html', 
                         listings=listings, 
                         premium_listings=premium_listings,
                         recent_listings=recent_listings,
                         categories=categories,
                         search=search,
                         selected_category=category_id,
                         location=location)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        location = request.form.get('location')
        
        # Validation
        if not validate_congolese_phone(phone_number):
            flash('Numéro de téléphone invalide. Format requis: 242XXXXXXXXX', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Ce numéro de téléphone est déjà utilisé.', 'error')
            return render_template('auth/register.html')
        
        # Handle profile picture upload
        profile_picture = 'default-avatar.svg'
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                saved_path = save_image(file, 'profiles')
                if saved_path:
                    profile_picture = saved_path
        
        # Create new user
        user = User(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            profile_picture=profile_picture,
            password_hash=generate_password_hash(password),
            location=location
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        
        user = User.query.filter_by(phone_number=phone_number, is_active=True).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Numéro de téléphone ou mot de passe incorrect.', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_listings = Listing.query.filter_by(user_id=current_user.id).order_by(Listing.created_at.desc()).all()
    pending_premium_request = PremiumRequest.query.filter_by(user_id=current_user.id, status='pending').first()
    
    # Get chat statistics
    unread_messages = ChatMessage.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    
    return render_template('profile/dashboard.html', 
                         user_listings=user_listings,
                         pending_premium_request=pending_premium_request,
                         unread_messages=unread_messages)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.location = request.form.get('location')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                saved_path = save_image(file, 'profiles')
                if saved_path:
                    current_user.profile_picture = saved_path
        
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if current_password and new_password:
            if check_password_hash(current_user.password_hash, current_password):
                current_user.password_hash = generate_password_hash(new_password)
            else:
                flash('Mot de passe actuel incorrect.', 'error')
                return render_template('profile/edit_profile.html')
        
        db.session.commit()
        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('profile/edit_profile.html')

@app.route('/listings/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        price = request.form.get('price', type=float)
        location = request.form.get('location')
        category_id = request.form.get('category_id', type=int)
        
        # Create listing
        listing = Listing(
            title=title,
            description=description,
            price=price,
            location=location,
            category_id=category_id,
            user_id=current_user.id
        )
        
        db.session.add(listing)
        db.session.flush()  # Get the listing ID
        
        # Handle image uploads
        uploaded_files = request.files.getlist('images')
        for i, file in enumerate(uploaded_files):
            if file and file.filename:
                saved_path = save_image(file, 'listings')
                if saved_path:
                    image = ListingImage(
                        listing_id=listing.id,
                        image_path=saved_path,
                        is_primary=(i == 0)
                    )
                    db.session.add(image)
        
        db.session.commit()
        flash('Annonce créée avec succès!', 'success')
        return redirect(url_for('listing_detail', id=listing.id))
    
    categories = Category.query.all()
    return render_template('listings/create.html', categories=categories)

@app.route('/listings/<int:id>')
def listing_detail(id):
    listing = Listing.query.get_or_404(id)
    
    # Increment view count
    listing.view_count += 1
    db.session.commit()
    
    # Get related listings from same category
    related_listings = Listing.query.filter(
        and_(
            Listing.category_id == listing.category_id,
            Listing.id != listing.id,
            Listing.is_active == True,
            Listing.is_sold == False
        )
    ).limit(4).all()
    
    return render_template('listings/detail.html', listing=listing, related_listings=related_listings)

@app.route('/listings/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_listing(id):
    listing = Listing.query.get_or_404(id)
    
    if listing.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à modifier cette annonce.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        listing.title = request.form.get('title')
        listing.description = request.form.get('description')
        listing.price = request.form.get('price', type=float)
        listing.location = request.form.get('location')
        listing.category_id = request.form.get('category_id', type=int)
        
        # Handle new image uploads
        uploaded_files = request.files.getlist('images')
        for file in uploaded_files:
            if file and file.filename:
                saved_path = save_image(file, 'listings')
                if saved_path:
                    image = ListingImage(
                        listing_id=listing.id,
                        image_path=saved_path
                    )
                    db.session.add(image)
        
        db.session.commit()
        flash('Annonce mise à jour avec succès!', 'success')
        return redirect(url_for('listing_detail', id=listing.id))
    
    categories = Category.query.all()
    return render_template('listings/edit.html', listing=listing, categories=categories)

@app.route('/listings/<int:id>/toggle_sold', methods=['POST'])
@login_required
def toggle_sold(id):
    listing = Listing.query.get_or_404(id)
    
    if listing.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    
    listing.is_sold = not listing.is_sold
    db.session.commit()
    
    status = 'vendu' if listing.is_sold else 'disponible'
    return jsonify({'status': status, 'is_sold': listing.is_sold})

@app.route('/listings/<int:id>/delete', methods=['POST'])
@login_required
def delete_listing(id):
    listing = Listing.query.get_or_404(id)
    
    if listing.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à supprimer cette annonce.', 'error')
        return redirect(url_for('dashboard'))
    
    db.session.delete(listing)
    db.session.commit()
    
    flash('Annonce supprimée avec succès.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/search')
def search():
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    user_lat = request.args.get('lat', type=float)
    user_lon = request.args.get('lon', type=float)
    sort_by = request.args.get('sort', 'relevance')
    
    # Base query
    query = Listing.query.filter_by(is_active=True, is_sold=False)
    
    # Apply filters
    if search:
        query = query.filter(or_(
            Listing.title.contains(search),
            Listing.description.contains(search)
        ))
    
    if category_id:
        query = query.filter(Listing.category_id == category_id)
    
    if location:
        query = query.filter(Listing.location.contains(location))
    
    if min_price:
        query = query.filter(Listing.price >= min_price)
    
    if max_price:
        query = query.filter(Listing.price <= max_price)
    
    listings = query.all()
    
    # Sort listings
    if sort_by == 'price_low':
        listings.sort(key=lambda x: x.price)
    elif sort_by == 'price_high':
        listings.sort(key=lambda x: x.price, reverse=True)
    elif sort_by == 'newest':
        listings.sort(key=lambda x: x.created_at, reverse=True)
    elif sort_by == 'oldest':
        listings.sort(key=lambda x: x.created_at)
    else:  # relevance - premium and proximity
        def sort_key(listing):
            premium_score = 1000 if listing.is_premium_listing else 0
            distance_score = 0
            
            if user_lat and user_lon and listing.latitude and listing.longitude:
                distance = calculate_distance(user_lat, user_lon, listing.latitude, listing.longitude)
                distance_score = max(0, 100 - distance)
            
            return -(premium_score + distance_score)
        
        listings.sort(key=sort_key)
    
    categories = Category.query.all()
    
    return render_template('search.html', 
                         listings=listings,
                         categories=categories,
                         search=search,
                         selected_category=category_id,
                         location=location,
                         min_price=min_price,
                         max_price=max_price,
                         sort_by=sort_by)

@app.route('/premium/upgrade', methods=['GET', 'POST'])
@login_required
def upgrade_premium():
    if request.method == 'POST':
        payment_phone = request.form.get('payment_phone')
        amount = request.form.get('amount', type=float)
        payment_date = request.form.get('payment_date')
        
        # Create premium request
        premium_request = PremiumRequest(
            user_id=current_user.id,
            payment_phone=payment_phone,
            amount=amount,
            payment_date=payment_date
        )
        
        db.session.add(premium_request)
        db.session.commit()
        
        flash('Votre demande d\'activation Premium a été soumise. Elle sera traitée dans les plus brefs délais.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('premium/upgrade.html')

# Initialize default categories (moved to app.py)
def create_default_categories():
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
