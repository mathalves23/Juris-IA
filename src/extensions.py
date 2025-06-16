from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt

# Inicializar extensões
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()
bcrypt = Bcrypt()

def init_extensions(app):
    """Inicializa todas as extensões Flask com a aplicação"""
    # Verificar se o SQLAlchemy já foi inicializado
    if not hasattr(app, 'extensions') or 'sqlalchemy' not in app.extensions:
        db.init_app(app)
    
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # Configurar CORS com as origens permitidas
    cors.init_app(app, 
                  origins=app.config.get('CORS_ORIGINS', ['http://localhost:3007']),
                  supports_credentials=True,
                  allow_headers=['Content-Type', 'Authorization', 'Accept'],
                  methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                  max_age=86400)
    
    migrate.init_app(app, db)
    
    # Configurar callbacks do JWT para blacklist
    setup_jwt_callbacks(app)
    
    return app

def setup_jwt_callbacks(app):
    """Configura callbacks do JWT para segurança avançada"""
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Verifica se o token está na blacklist"""
        try:
            from src.models.user_security import TokenBlacklist
            jti = jwt_payload['jti']
            return TokenBlacklist.query.filter_by(jti=jti).first() is not None
        except Exception:
            # Em caso de erro, considerar token válido para não quebrar a aplicação
            return False
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Callback para token expirado"""
        return {
            'success': False,
            'error': 'TOKEN_EXPIRED',
            'message': 'Token expirado. Faça login novamente.'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Callback para token inválido"""
        return {
            'success': False,
            'error': 'INVALID_TOKEN',
            'message': 'Token inválido. Faça login novamente.'
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Callback para token ausente"""
        return {
            'success': False,
            'error': 'MISSING_TOKEN',
            'message': 'Token de acesso requerido.'
        }, 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        """Callback para token não-fresh"""
        return {
            'success': False,
            'error': 'FRESH_TOKEN_REQUIRED',
            'message': 'Token fresh requerido. Faça login novamente.'
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Callback para token revogado"""
        return {
            'success': False,
            'error': 'TOKEN_REVOKED',
            'message': 'Token foi revogado. Faça login novamente.'
        }, 401
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Define como extrair identidade do usuário"""
        return str(user.id) if hasattr(user, 'id') else str(user)
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Carrega usuário a partir do token JWT"""
        try:
            from src.models.user import User
            identity = jwt_data["sub"]
            return User.query.get(int(identity))
        except Exception:
            return None
