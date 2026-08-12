import os
import sys

# Only load .env if NOT on Render
if not os.environ.get('RENDER'):
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv()
        print("Loaded .env file (development mode)")
else:
    print("Running on Render - using environment variables")

class Config:
    # Supabase Configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Debug output
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"SUPABASE_KEY: {SUPABASE_KEY[:30] if SUPABASE_KEY else 'None'}...")
    
    # Validate credentials
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is not set")
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_KEY environment variable is not set")
    
    # Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600
    
    # Upload Settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'pdf', 'png', 'jpg', 'jpeg'}
    
    # RAAWA Settings
    MAX_PERSONNEL = 20
    REGIONS = ['MIN', 'LUZ', 'VIS']
    ROLES = ['superadmin', 'user', 'approver']
    RAAWA_EXPIRY_DAYS = 30
    
    # Notification Settings
    NOTIFICATION_TYPES = ['approval', 'rejection', 'expiry', 'system', 'info', 'warning']
    
    # Messaging Settings
    MESSAGE_TYPES = ['global', 'regional', 'dm']
    
    # Superadmin default account
    SUPERADMIN_USERNAME = 'admin'
    SUPERADMIN_PASSWORD = 'Admin@2026'
    SUPERADMIN_EMAIL = 'admin@raawa.com'
    SUPERADMIN_FULLNAME = 'System Administrator'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
