"""
Configuration management for the web application
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    
    # File upload configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB default
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER') or 'temp'
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER') or 'outputs'
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'docx'}
    
    # CORS configuration
    CORS_ORIGINS = [origin.strip() for origin in os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')]
    
    # Processing configuration
    MAX_PROCESSING_TIME = int(os.environ.get('MAX_PROCESSING_TIME', 300))  # 5 minutes
    JOB_TIMEOUT = int(os.environ.get('JOB_TIMEOUT', 600))  # 10 minutes
    
    # AI API configuration (inherited from existing .env)
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    # Database configuration (for job management)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///jobs.db'
    
    # WebSocket configuration
    WEBSOCKET_PING_TIMEOUT = int(os.environ.get('WEBSOCKET_PING_TIMEOUT', 60))
    WEBSOCKET_PING_INTERVAL = int(os.environ.get('WEBSOCKET_PING_INTERVAL', 25))
    WEBSOCKET_MAX_CONNECTIONS = int(os.environ.get('WEBSOCKET_MAX_CONNECTIONS', 100))
    
    # Progress tracking configuration
    PROGRESS_UPDATE_INTERVAL = float(os.environ.get('PROGRESS_UPDATE_INTERVAL', 1.0))
    JOB_CLEANUP_TIMEOUT = int(os.environ.get('JOB_CLEANUP_TIMEOUT', 3600))  # 1 hour
    
    @classmethod
    def get_required_directories(cls):
        """Return list of directories that need to exist"""
        return [cls.UPLOAD_FOLDER, cls.TEMP_FOLDER, cls.OUTPUT_FOLDER]
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Configuration initialization - directories are now handled in app factory
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Use secure secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    def __init__(self):
        if not self.SECRET_KEY:
            raise RuntimeError('SECRET_KEY environment variable must be set in production')

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB for testing

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Export the default configuration
WebConfig = config[os.environ.get('FLASK_ENV', 'default')]