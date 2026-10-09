"""
LoginTabSystem Configuration
Cybersecurity Modal 0 Edition
"""

import os
from pathlib import Path

# Direktori Dasar
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
LOG_DIR = BASE_DIR / "logs"

# Buat direktori jika belum ada
DB_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_CONFIG = {
    'type': 'sqlite',
    'path': DB_DIR / 'users.db',
    'timeout': 5.0,
    'check_same_thread': False,
}

# ============================================
# SECURITY CONFIGURATION
# ============================================
SECURITY_CONFIG = {
    # Password Hashing
    'password_hash_algorithm': 'pbkdf2_sha256',
    'password_iterations': 100000,
    'password_salt_length': 32,
    
    # Session Management
    'session_timeout_minutes': 30,
    'remember_me_days': 7,
    
    # Rate Limiting
    'max_login_attempts': 5,
    'lockout_duration_minutes': 15,
    'password_reset_attempts': 3,
    'password_reset_timeout_minutes': 30,
    
    # Token Configuration
    'jwt_secret_key': os.getenv('JWT_SECRET_KEY', 'cybersecurity-modal-0-dev-key-change-in-production'),
    'jwt_algorithm': 'HS256',
    'jwt_expiry_hours': 24,
    
    # 2FA Settings
    'enable_2fa': True,
    '2fa_timeout_seconds': 300,
    '2fa_code_length': 6,
    
    # Password Policy
    'password_min_length': 8,
    'password_require_uppercase': True,
    'password_require_lowercase': True,
    'password_require_numbers': True,
    'password_require_special': True,
    'special_characters': '!@#$%^&*()_+-=[]{}|;:,.<>?',
}

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOGGING_CONFIG = {
    'log_dir': LOG_DIR,
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'max_log_size_mb': 10,
    'backup_count': 5,
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'audit_log': True,
    'audit_log_file': LOG_DIR / 'audit.log',
}

# ============================================
# APPLICATION CONFIGURATION
# ============================================
APP_CONFIG = {
    'app_name': 'LoginTabSystem',
    'app_version': '1.0.0',
    'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
    'testing_mode': False,
    
    # Server Settings
    'host': '0.0.0.0',
    'port': int(os.getenv('PORT', 8000)),
    'workers': 4,
    
    # UI Settings
    'enable_cli': True,
    'enable_web': True,
    'enable_api': True,
}

# ============================================
# EMAIL CONFIGURATION (Optional)
# ============================================
EMAIL_CONFIG = {
    'enabled': False,
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'sender_email': os.getenv('SENDER_EMAIL', ''),
    'sender_password': os.getenv('SENDER_PASSWORD', ''),
    'use_tls': True,
}

# ============================================
# DEFAULT USERS (Hanya untuk development)
# ============================================
DEFAULT_USERS = [
    {
        'username': 'admin',
        'email': 'admin@localhost',
        'password': 'admin123',  # Harus diubah!
        'role': 'admin',
    },
    {
        'username': 'demo',
        'email': 'demo@localhost',
        'password': 'demo123',
        'role': 'user',
    },
]

# ============================================
# FEATURE FLAGS
# ============================================
FEATURES = {
    'enable_registration': True,
    'enable_password_reset': True,
    'enable_2fa': True,
    'enable_social_login': False,
    'enable_api_access': True,
    'enable_audit_logging': True,
    'maintenance_mode': False,
}

# ============================================
# ENVIRONMENT SPECIFIC
# ============================================
ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'production':
    SECURITY_CONFIG['jwt_secret_key'] = os.getenv('JWT_SECRET_KEY')
    APP_CONFIG['debug_mode'] = False
    LOGGING_CONFIG['log_level'] = 'WARNING'
    
elif ENV == 'testing':
    DATABASE_CONFIG['path'] = ':memory:'
    APP_CONFIG['testing_mode'] = True
    LOGGING_CONFIG['log_level'] = 'DEBUG'
