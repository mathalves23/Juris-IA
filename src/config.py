import os
from dotenv import load_dotenv
from datetime import timedelta
import secrets

load_dotenv()

class Config:
    # Database Configuration  
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Database URL - Suporte para PostgreSQL e SQLite
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    DB_PATH = os.path.join(BASE_DIR, 'instance', 'jurisia.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 30,
        'max_overflow': 10
    }
    
    # PostgreSQL específico
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'jurisia')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'jurisia_prod')
    
    # Backup Configuration
    BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', 24))
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
    BACKUP_LOCAL_PATH = os.getenv('BACKUP_LOCAL_PATH', 'backups')
    
    # S3 Backup Configuration
    BACKUP_S3_ENABLED = os.getenv('BACKUP_S3_ENABLED', 'false').lower() == 'true'
    BACKUP_S3_BUCKET = os.getenv('BACKUP_S3_BUCKET', '')
    BACKUP_S3_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID', '')
    BACKUP_S3_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    BACKUP_S3_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Migration Configuration
    MIGRATION_DIR = os.path.join(BASE_DIR, 'migrations')
    AUTO_MIGRATE = os.getenv('AUTO_MIGRATE', 'false').lower() == 'true'
    
    # JWT - Security Enhanced
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 86400))
    JWT_IDENTITY_CLAIM = 'sub'
    JWT_ALGORITHM = 'HS256'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Security Keys
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(32))
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', secrets.token_urlsafe(16))
    
    # Password Reset & Email Verification
    PASSWORD_RESET_EXPIRY = int(os.getenv('PASSWORD_RESET_EXPIRY', 3600))  # 1 hour
    EMAIL_VERIFICATION_EXPIRY = int(os.getenv('EMAIL_VERIFICATION_EXPIRY', 86400))  # 24 hours
    
    # Account Security
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', 5))
    LOCKOUT_DURATION = int(os.getenv('LOCKOUT_DURATION', 900))  # 15 minutes
    
    # 2FA Configuration
    TOTP_ISSUER = os.getenv('TOTP_ISSUER', 'JurisIA')
    TOTP_ALGORITHM = os.getenv('TOTP_ALGORITHM', 'SHA1')
    TOTP_DIGITS = int(os.getenv('TOTP_DIGITS', 6))
    TOTP_PERIOD = int(os.getenv('TOTP_PERIOD', 30))
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 2000))
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.7))
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
    
    # App
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    TESTING = False
    
    # Cors
    CORS_ORIGINS = [
        'http://localhost:3000', 'http://localhost:3001', 'http://localhost:3006', 
        'http://127.0.0.1:3000', 'http://127.0.0.1:3001', 'http://127.0.0.1:3006',
        'https://jurisia.netlify.app'
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', 3600))  # 1 hour
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Email Configuration - Multiple Providers
    # Gmail/SMTP
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    
    # SendGrid
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@jurisia.com')
    
    # ==== CONFIGURAÇÕES DE CACHE REDIS ====
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    REDIS_SSL = os.getenv('REDIS_SSL', 'false').lower() == 'true'
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'redis')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # ==== CONFIGURAÇÕES DE CLOUD STORAGE ====
    CLOUD_STORAGE_PROVIDER = os.getenv('CLOUD_STORAGE_PROVIDER', 'local')  # aws, gcp, local
    
    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_CLOUDFRONT_DOMAIN = os.getenv('AWS_CLOUDFRONT_DOMAIN')
    
    # Google Cloud Storage
    GCP_STORAGE_BUCKET = os.getenv('GCP_STORAGE_BUCKET')
    GCP_CDN_DOMAIN = os.getenv('GCP_CDN_DOMAIN')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Local Storage
    LOCAL_STORAGE_PATH = os.getenv('LOCAL_STORAGE_PATH', 'uploads')
    LOCAL_STORAGE_URL = os.getenv('LOCAL_STORAGE_URL', 'http://localhost:5005/uploads')
    
    # ==== CONFIGURAÇÕES DE OTIMIZAÇÃO ====
    # Imagens
    IMAGE_OPTIMIZATION_ENABLED = os.getenv('IMAGE_OPTIMIZATION_ENABLED', 'true').lower() == 'true'
    IMAGE_MAX_WIDTH = int(os.getenv('IMAGE_MAX_WIDTH', '1920'))
    IMAGE_MAX_HEIGHT = int(os.getenv('IMAGE_MAX_HEIGHT', '1080'))
    IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '85'))
    CREATE_THUMBNAILS = os.getenv('CREATE_THUMBNAILS', 'true').lower() == 'true'
    
    # Compressão
    FILE_COMPRESSION_ENABLED = os.getenv('FILE_COMPRESSION_ENABLED', 'true').lower() == 'true'
    COMPRESSION_LEVEL = int(os.getenv('COMPRESSION_LEVEL', '6'))
    
    # ==== CONFIGURAÇÕES DE MONITORAMENTO ====
    MONITORING_ENABLED = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
    METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    SYSTEM_MONITORING_INTERVAL = int(os.getenv('SYSTEM_MONITORING_INTERVAL', '30'))
    
    # Prometheus
    PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'false').lower() == 'true'
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', '9090'))
    
    # Sentry
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'development')
    
    # ==== CONFIGURAÇÕES DE COLABORAÇÃO ====
    # WebSocket/SocketIO para colaboração
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    WEBSOCKET_ENABLED = os.getenv('WEBSOCKET_ENABLED', 'true').lower() == 'true'
    WEBSOCKET_PORT = int(os.getenv('WEBSOCKET_PORT', '5006'))
    COLLABORATION_ENABLED = os.getenv('COLLABORATION_ENABLED', 'true').lower() == 'true'
    
    # ==== CONFIGURAÇÕES DE PERFORMANCE ====
    # Paginação
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', '20'))
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', '100'))
    
    # ==== CONFIGURAÇÕES DE INDEXAÇÃO ====
    FULL_TEXT_SEARCH_ENABLED = os.getenv('FULL_TEXT_SEARCH_ENABLED', 'true').lower() == 'true'
    ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    SEARCH_INDEX_PREFIX = os.getenv('SEARCH_INDEX_PREFIX', 'jurisia')
    
    # ==== CONFIGURAÇÕES DE TASK QUEUE ====
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'America/Sao_Paulo'
    
    # ==== CONFIGURAÇÕES DE FEATURE FLAGS ====
    FEATURE_COLLABORATION = os.getenv('FEATURE_COLLABORATION', 'true').lower() == 'true'
    FEATURE_KANBAN = os.getenv('FEATURE_KANBAN', 'true').lower() == 'true'
    FEATURE_WIKI = os.getenv('FEATURE_WIKI', 'true').lower() == 'true'
    FEATURE_ANALYTICS = os.getenv('FEATURE_ANALYTICS', 'true').lower() == 'true'
    FEATURE_AI_ASSISTANT = os.getenv('FEATURE_AI_ASSISTANT', 'true').lower() == 'true'
    FEATURE_PUBLICATIONS = os.getenv('FEATURE_PUBLICATIONS', 'true').lower() == 'true'
    
    # App Info
    APP_NAME = os.getenv('APP_NAME', 'JurisIA')
    APP_VERSION = os.getenv('APP_VERSION', '2.0.0')
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'JurisIA Legal Tech')
    SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'suporte@jurisia.com')
    
    # URLs
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5005')
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    @staticmethod
    def is_openai_configured():
        """Verifica se a OpenAI está configurada corretamente"""
        api_key = Config.OPENAI_API_KEY
        return api_key and len(api_key) > 20 and api_key.startswith('sk-')
    
    @staticmethod
    def is_email_configured():
        """Verifica se email está configurado"""
        return bool(Config.SENDGRID_API_KEY) or (Config.MAIL_USERNAME and Config.MAIL_PASSWORD)
    
    @staticmethod
    def is_postgresql():
        """Verifica se está usando PostgreSQL"""
        return 'postgresql' in Config.SQLALCHEMY_DATABASE_URI
    
    @staticmethod
    def get_backup_path():
        """Retorna o caminho completo para backups"""
        backup_path = os.path.join(os.getcwd(), Config.BACKUP_LOCAL_PATH)
        os.makedirs(backup_path, exist_ok=True)
        return backup_path
    
    @staticmethod
    def get_upload_path():
        """Retorna o caminho completo para uploads"""
        upload_path = os.path.join(os.getcwd(), Config.UPLOAD_FOLDER)
        os.makedirs(upload_path, exist_ok=True)
        return upload_path
    
    @staticmethod
    def is_allowed_file(filename):
        """Verifica se o arquivo tem uma extensão permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS 
    
    @staticmethod
    def generate_secure_token():
        """Gera token seguro para reset de senha"""
        return secrets.token_urlsafe(32)

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    # Relaxed security for development
    PASSWORD_RESET_EXPIRY = 3600  # 1 hour
    MAX_LOGIN_ATTEMPTS = 10
    BACKUP_ENABLED = False  # Desabilitar backup em desenvolvimento

class ProductionConfig(Config):
    DEBUG = False
    
    # PostgreSQL obrigatório em produção
    if not Config.DATABASE_URL and not Config.POSTGRES_PASSWORD:
        print("⚠️  AVISO: PostgreSQL não configurado. Usando SQLite.")
    
    # Backup obrigatório em produção
    BACKUP_ENABLED = True
    
    # Strict security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    
    # Strict security settings
    MAX_LOGIN_ATTEMPTS = 3
    LOCKOUT_DURATION = 1800  # 30 minutes
    PASSWORD_RESET_EXPIRY = 1800  # 30 minutes
    
    # Ensure keys are set
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Ensure production secrets are set
        if not os.getenv('JWT_SECRET_KEY'):
            raise ValueError("JWT_SECRET_KEY must be set in production")
        if not os.getenv('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production")

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    WTF_CSRF_ENABLED = False
    BACKUP_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 