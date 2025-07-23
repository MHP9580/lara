from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func
from app import app, db
from models import Admin, User, Listing, Category, PremiumRequest, ChatMessage
from utils import save_image

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username, is_active=True).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            admin.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Vous avez été déconnecté de l\'administration.', 'info')
    return redirect(url_for('admin_login'))

def admin_required(f):
    """Decorator to require admin authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin or not admin.is_active:
            session.pop('admin_id', None)
            return redirect(url_for('admin_login'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def super_admin_required(f):
    """Decorator to require super admin authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin = Admin.query.get(session['admin_id'])
        if not admin or not admin.is_active or not admin.is_super_admin:
            flash('Accès refusé. Privilèges de super administrateur requis.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    admin = Admin.query.get(session['admin_id'])
    
    # Get statistics
    stats = {
        'total_users': User.query.filter_by(is_active=True).count(),
        'premium_users': User.query.filter_by(is_premium=True, is_active=True).count(),
        'total_listings': Listing.query.filter_by(is_active=True).count(),
        'sold_listings': Listing.query.filter_by(is_sold=True, is_active=True).count(),
        'pending_premium_requests': PremiumRequest.query.filter_by(status='pending').count(),
        'total_messages': ChatMessage.query.count(),
        'unread_messages': ChatMessage.query.filter_by(is_read=False).count(),
    }
    
    # Recent activities
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_listings = Listing.query.order_by(Listing.created_at.desc()).limit(5).all()
    pending_requests = PremiumRequest.query.filter_by(status='pending').order_by(PremiumRequest.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         admin=admin, 
                         stats=stats,
                         recent_users=recent_users,
                         recent_listings=recent_listings,
                         pending_requests=pending_requests)

@app.route('/admin/users')
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.phone_number.contains(search)
            )
        )
    
    if filter_type == 'premium':
        query = query.filter_by(is_premium=True)
    elif filter_type == 'regular':
        query = query.filter_by(is_premium=False)
    elif filter_type == 'inactive':
        query = query.filter_by(is_active=False)
    else:
        query = query.filter_by(is_active=True)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search, filter_type=filter_type)

@app.route('/admin/users/<int:id>/toggle_premium', methods=['POST'])
@admin_required
def toggle_user_premium(id):
    user = User.query.get_or_404(id)
    duration = request.form.get('duration', type=int, default=30)
    
    admin = Admin.query.get(session['admin_id'])
    
    if user.is_premium:
        user.is_premium = False
        user.premium_end_date = None
        message = f'Statut Premium retiré de {user.full_name}'
    else:
        user.is_premium = True
        user.premium_end_date = datetime.utcnow() + timedelta(days=duration)
        message = f'Statut Premium activé pour {user.full_name} ({duration} jours)'
    
    db.session.commit()
    flash(message, 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:id>/toggle_active', methods=['POST'])
@admin_required
def toggle_user_active(id):
    user = User.query.get_or_404(id)
    
    user.is_active = not user.is_active
    status = 'activé' if user.is_active else 'désactivé'
    
    db.session.commit()
    flash(f'Utilisateur {user.full_name} {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/listings')
@admin_required
def admin_listings():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    category_id = request.args.get('category', type=int)
    
    query = Listing.query
    
    if search:
        query = query.filter(
            db.or_(
                Listing.title.contains(search),
                Listing.description.contains(search)
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if filter_type == 'sold':
        query = query.filter_by(is_sold=True)
    elif filter_type == 'inactive':
        query = query.filter_by(is_active=False)
    else:
        query = query.filter_by(is_active=True, is_sold=False)
    
    listings = query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = Category.query.all()
    
    return render_template('admin/listings.html', 
                         listings=listings, 
                         categories=categories,
                         search=search, 
                         filter_type=filter_type,
                         selected_category=category_id)

@app.route('/admin/listings/<int:id>/toggle_active', methods=['POST'])
@admin_required
def toggle_listing_active(id):
    listing = Listing.query.get_or_404(id)
    
    listing.is_active = not listing.is_active
    status = 'activée' if listing.is_active else 'désactivée'
    
    db.session.commit()
    flash(f'Annonce "{listing.title}" {status}.', 'success')
    return redirect(url_for('admin_listings'))

@app.route('/admin/listings/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_listing(id):
    listing = Listing.query.get_or_404(id)
    title = listing.title
    
    db.session.delete(listing)
    db.session.commit()
    
    flash(f'Annonce "{title}" supprimée définitivement.', 'success')
    return redirect(url_for('admin_listings'))

@app.route('/admin/premium-requests')
@admin_required
def admin_premium_requests():
    status_filter = request.args.get('status', 'pending')
    
    query = PremiumRequest.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    requests = query.order_by(PremiumRequest.created_at.desc()).all()
    
    return render_template('admin/premium_requests.html', requests=requests, status_filter=status_filter)

@app.route('/admin/premium-requests/<int:id>/approve', methods=['POST'])
@admin_required
def approve_premium_request(id):
    request_obj = PremiumRequest.query.get_or_404(id)
    duration = request.form.get('duration', type=int, default=30)
    admin_notes = request.form.get('admin_notes', '')
    
    admin = Admin.query.get(session['admin_id'])
    
    # Activate premium for user
    user = request_obj.user
    user.is_premium = True
    user.premium_end_date = datetime.utcnow() + timedelta(days=duration)
    
    # Update request status
    request_obj.status = 'approved'
    request_obj.processed_at = datetime.utcnow()
    request_obj.processed_by = admin.id
    request_obj.admin_notes = admin_notes
    
    db.session.commit()
    
    flash(f'Demande Premium approuvée pour {user.full_name} ({duration} jours).', 'success')
    return redirect(url_for('admin_premium_requests'))

@app.route('/admin/premium-requests/<int:id>/reject', methods=['POST'])
@admin_required
def reject_premium_request(id):
    request_obj = PremiumRequest.query.get_or_404(id)
    admin_notes = request.form.get('admin_notes', '')
    
    admin = Admin.query.get(session['admin_id'])
    
    # Update request status
    request_obj.status = 'rejected'
    request_obj.processed_at = datetime.utcnow()
    request_obj.processed_by = admin.id
    request_obj.admin_notes = admin_notes
    
    db.session.commit()
    
    flash(f'Demande Premium rejetée pour {request_obj.user.full_name}.', 'warning')
    return redirect(url_for('admin_premium_requests'))

@app.route('/admin/moderators')
@super_admin_required
def admin_moderators():
    moderators = Admin.query.filter_by(role='moderator').order_by(Admin.created_at.desc()).all()
    return render_template('admin/moderators.html', moderators=moderators)

@app.route('/admin/moderators/add', methods=['POST'])
@super_admin_required
def add_moderator():
    username = request.form.get('username')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    password = request.form.get('password')
    
    # Check if username or email already exists
    if Admin.query.filter_by(username=username).first():
        flash('Ce nom d\'utilisateur existe déjà.', 'error')
        return redirect(url_for('admin_moderators'))
    
    if Admin.query.filter_by(email=email).first():
        flash('Cette adresse email existe déjà.', 'error')
        return redirect(url_for('admin_moderators'))
    
    # Create new moderator
    moderator = Admin(
        username=username,
        email=email,
        phone_number=phone_number,
        first_name=first_name,
        last_name=last_name,
        password_hash=generate_password_hash(password),
        role='moderator'
    )
    
    db.session.add(moderator)
    db.session.commit()
    
    flash(f'Modérateur {moderator.full_name} créé avec succès.', 'success')
    return redirect(url_for('admin_moderators'))

@app.route('/admin/moderators/<int:id>/toggle_active', methods=['POST'])
@super_admin_required
def toggle_moderator_active(id):
    moderator = Admin.query.get_or_404(id)
    
    if moderator.is_super_admin:
        flash('Impossible de désactiver un super administrateur.', 'error')
        return redirect(url_for('admin_moderators'))
    
    moderator.is_active = not moderator.is_active
    status = 'activé' if moderator.is_active else 'désactivé'
    
    db.session.commit()
    flash(f'Modérateur {moderator.full_name} {status}.', 'success')
    return redirect(url_for('admin_moderators'))

@app.route('/admin/profile', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    admin = Admin.query.get(session['admin_id'])
    
    if request.method == 'POST':
        admin.first_name = request.form.get('first_name')
        admin.last_name = request.form.get('last_name')
        admin.email = request.form.get('email')
        admin.phone_number = request.form.get('phone_number')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                saved_path = save_image(file, 'profiles')
                if saved_path:
                    admin.profile_picture = saved_path
        
        # Handle password change
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if current_password and new_password:
            if check_password_hash(admin.password_hash, current_password):
                admin.password_hash = generate_password_hash(new_password)
            else:
                flash('Mot de passe actuel incorrect.', 'error')
                return render_template('admin/profile.html', admin=admin)
        
        db.session.commit()
        flash('Profil administrateur mis à jour avec succès.', 'success')
        return redirect(url_for('admin_profile'))
    
    return render_template('admin/profile.html', admin=admin)

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon', 'fas fa-tag')
        
        category = Category(name=name, description=description, icon=icon)
        db.session.add(category)
        db.session.commit()
        
        flash(f'Catégorie "{name}" créée avec succès.', 'success')
        return redirect(url_for('admin_categories'))
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/<int:id>/delete', methods=['POST'])
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    
    # Check if category has listings
    if category.listings:
        flash(f'Impossible de supprimer la catégorie "{category.name}" car elle contient des annonces.', 'error')
    else:
        name = category.name
        db.session.delete(category)
        db.session.commit()
        flash(f'Catégorie "{name}" supprimée avec succès.', 'success')
    
    return redirect(url_for('admin_categories'))
