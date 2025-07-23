import os
import re
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
import math

def validate_congolese_phone(phone_number):
    """Validate Congolese phone number format (242XXXXXXXXX)"""
    pattern = r'^242\d{9}$'
    return bool(re.match(pattern, phone_number))

def allowed_file(filename):
    """Check if file extension is allowed for image uploads"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image_file, folder='uploads'):
    """Save uploaded image with unique filename and resize if needed"""
    if not image_file or not allowed_file(image_file.filename):
        return None
    
    # Generate unique filename
    filename = secure_filename(image_file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    # Create full path
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, unique_filename)
    
    try:
        # Save and resize image
        image = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize image (max 800x600 for listings, 400x400 for profiles)
        if folder == 'profiles':
            max_size = (400, 400)
        else:
            max_size = (800, 600)
        
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        image.save(file_path, 'JPEG', quality=85, optimize=True)
        
        return f"{folder}/{unique_filename}"
    except Exception as e:
        current_app.logger.error(f"Error saving image: {e}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r

def format_price(price):
    """Format price with FCFA currency"""
    return f"{price:,.0f} FCFA"

def time_ago(date):
    """Return human-readable time difference"""
    from datetime import datetime
    
    now = datetime.utcnow()
    diff = now - date
    
    if diff.days > 0:
        return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "à l'instant"
