from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(allowed_roles):
    """
    Decorator to restrict access to specific roles
    Usage: @role_required(['superadmin', 'approver'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login to access this page', 'warning')
                return redirect(url_for('login'))
            
            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def superadmin_required(f):
    """Decorator for superadmin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        if current_user.role != 'superadmin':
            flash('Superadmin access required', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def approver_required(f):
    """Decorator for approver-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        if current_user.role not in ['approver', 'superadmin']:
            flash('Approver access required', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    """Decorator for user-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        if current_user.role not in ['user', 'approver', 'superadmin']:
            flash('User access required', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# Password validation functions
def validate_password_strength(password):
    """
    Validate password strength
    Returns: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isdigit() for char in password):
