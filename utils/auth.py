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
        return False, "Password must contain at least one number"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for char in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def validate_username(username):
    """
    Validate username
    Returns: (is_valid, message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 30:
        return False, "Username must be at most 30 characters long"
    
    if not username.isalnum() and '_' not in username:
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, "Username is valid"

def validate_email(email):
    """
    Validate email
    Returns: (is_valid, message)
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, "Email is valid"

# Permission check functions
def can_approve_raawa(user, raawa):
    """
    Check if user can approve a specific RAAWA
    """
    if user.role == 'superadmin':
        return True
    
    if user.role != 'approver':
        return False
    
    # Check if user is the assigned FM or Security
    from utils.db_utils import SupabaseDB
    db = SupabaseDB()
    approver = db.get_approver_by_user_id(user.id)
    if not approver:
        return False
    
    if raawa.get('facility_manager_id') == approver['id']:
        return True
    
    if raawa.get('security_id') == approver['id']:
        return True
    
    return False

def can_view_raawa(user, raawa):
    """
    Check if user can view a specific RAAWA
    """
    if user.role == 'superadmin':
        return True
    
    if user.role == 'user' and raawa.get('created_by') == user.id:
        return True
    
    if user.role == 'approver':
        from utils.db_utils import SupabaseDB
        db = SupabaseDB()
        approver = db.get_approver_by_user_id(user.id)
        if approver:
            if raawa.get('facility_manager_id') == approver['id']:
                return True
            if raawa.get('security_id') == approver['id']:
                return True
    
    return False
