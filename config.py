import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Supabase Configuration
    SUPABASE_URL = "https://ppmhmbcmbqhgqelfdnvk.supabase.co"
    SUPABASE_KEY = "sb_publishable_5ComPSfppVJ6lWwpYbwA8A_n7HJn6dG"
    SUPABASE_PUBLIC_KEY = "sb_publishable_5ComPSfppVJ6lWwpYbwA8A_n7HJn6dG"
    
    # Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2026'
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Upload Settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
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
    
    # File Settings
    TEMPLATE_FILE = 'templates/raawa_template.xlsx'
    
    # Deployment Settings
    DEBUG = False
    TESTING = False
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Production-specific configurations

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
