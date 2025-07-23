# Congo Connect - Marketplace Local Congolais

## Overview

Congo Connect is a local marketplace web application built with Flask, designed specifically for the Congolese market. It enables users to buy and sell products locally, with features like location-based search, premium memberships, real-time chat, and comprehensive admin management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite (can be upgraded to PostgreSQL)
- **Authentication**: Flask-Login for session management
- **File Handling**: Werkzeug for secure file uploads with PIL for image processing
- **Location Services**: Geolocation support with distance calculations

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **CSS Framework**: Bootstrap 5
- **Icons**: Font Awesome
- **JavaScript**: Vanilla JS with modular chat system
- **Responsive Design**: Mobile-first approach

### Database Schema
- **Users**: Authentication, profiles, premium status, geolocation
- **Listings**: Products/services with images, categories, pricing
- **Categories**: Product categorization system
- **Chat Messages**: Real-time messaging between users
- **Premium Requests**: Upgrade request management
- **Admin**: Administrative user management

## Key Components

### User Management
- Phone number-based authentication (Congolese format: 242XXXXXXXXX)
- Profile management with image uploads
- Premium membership system with enhanced visibility
- Location-based user profiles

### Marketplace Features
- Product listing creation with multiple images
- Category-based organization
- Price filtering and location-based search
- Premium listing prioritization
- Sold/active status management

### Communication System
- Real-time chat between buyers and sellers
- Conversation history management
- Unread message tracking
- User blocking and reporting features

### Admin Panel
- Comprehensive dashboard with statistics
- User management and moderation
- Listing oversight and approval
- Premium request processing
- Category management

### Premium Features
- Enhanced listing visibility
- Priority placement in search results
- Premium badges and branding
- Homepage feature placement

## Data Flow

1. **User Registration/Login**: Phone-based authentication with profile setup
2. **Listing Creation**: Multi-step form with image upload and categorization
3. **Search & Discovery**: Filter-based search with location proximity
4. **Communication**: Direct messaging between interested parties
5. **Premium Upgrade**: Request-based premium status activation
6. **Admin Oversight**: Moderation and management of all platform activities

## External Dependencies

### Frontend Libraries
- Bootstrap 5 (CDN)
- Font Awesome 6 (CDN)
- Vanilla JavaScript (no external JS frameworks)

### Python Packages
- Flask ecosystem (Flask, Flask-SQLAlchemy, Flask-Login)
- Werkzeug (security and file handling)
- PIL/Pillow (image processing)
- SQLAlchemy (database ORM)

### File Storage
- Local filesystem for image uploads
- Organized folder structure in `/static/uploads/`
- Image optimization and resizing

## Deployment Strategy

### Environment Configuration
- Environment variables for database URL and session secrets
- Debug mode configuration for development
- Production-ready WSGI configuration with ProxyFix

### Database Setup
- SQLite for development (easy setup)
- PostgreSQL support for production scaling
- Automatic table creation with SQLAlchemy

### File Management
- Upload folder creation and management
- Image processing pipeline for optimization
- Secure filename handling

### Session Management
- Flask session-based authentication
- Admin session security with active status checking
- Remember me functionality for user convenience

The application follows a traditional MVC pattern with Flask, uses session-based authentication, and implements a modular approach for different feature sets (user management, listings, chat, admin). The codebase is structured for easy maintenance and scalability, with clear separation between user-facing features and administrative functions.