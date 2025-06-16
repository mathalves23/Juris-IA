from datetime import datetime, timedelta
from src.extensions import db
from src.config import Config

class TokenBlacklist(db.Model):
    """Tokens JWT invalidados"""
    __tablename__ = 'token_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)  # JWT ID
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh' 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    revoked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<TokenBlacklist {self.jti}>'

class LoginAttempt(db.Model):
    """Controle de tentativas de login"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 support
    user_agent = db.Column(db.String(500))
    success = db.Column(db.Boolean, nullable=False, default=False)
    attempted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    failure_reason = db.Column(db.String(100))  # 'invalid_password', 'account_locked', etc.
    
    @staticmethod
    def is_account_locked(email):
        """Verifica se a conta está bloqueada por muitas tentativas"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=Config.LOCKOUT_DURATION)
        
        recent_failures = LoginAttempt.query.filter(
            LoginAttempt.email == email,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at > cutoff_time
        ).count()
        
        return recent_failures >= Config.MAX_LOGIN_ATTEMPTS
    
    @staticmethod
    def record_attempt(email, ip_address, user_agent, success, failure_reason=None):
        """Registra uma tentativa de login"""
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} - {"Success" if self.success else "Failed"}>'

class PasswordResetToken(db.Model):
    """Tokens para reset de senha"""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Relationship
    user = db.relationship('User', backref='password_reset_tokens')
    
    def __init__(self, user_id, token, ip_address=None, user_agent=None):
        self.user_id = user_id
        self.token = token
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.expires_at = datetime.utcnow() + timedelta(seconds=Config.PASSWORD_RESET_EXPIRY)
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_used(self):
        return self.used_at is not None
    
    @property
    def is_valid(self):
        return not self.is_expired and not self.is_used
    
    def mark_as_used(self):
        """Marca o token como usado"""
        self.used_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def create_for_user(user_id, ip_address=None, user_agent=None):
        """Cria um novo token de reset para o usuário"""
        # Invalidar tokens existentes
        existing_tokens = PasswordResetToken.query.filter_by(
            user_id=user_id, 
            used_at=None
        ).all()
        
        for token in existing_tokens:
            token.mark_as_used()
        
        # Criar novo token
        token_value = Config.generate_secure_token()
        new_token = PasswordResetToken(
            user_id=user_id,
            token=token_value,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(new_token)
        db.session.commit()
        return new_token
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}... for User {self.user_id}>'

class EmailVerificationToken(db.Model):
    """Tokens para verificação de email"""
    __tablename__ = 'email_verification_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=False)  # Email a ser verificado
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref='email_verification_tokens')
    
    def __init__(self, user_id, email, token):
        self.user_id = user_id
        self.email = email
        self.token = token
        self.expires_at = datetime.utcnow() + timedelta(seconds=Config.EMAIL_VERIFICATION_EXPIRY)
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_verified(self):
        return self.verified_at is not None
    
    @property
    def is_valid(self):
        return not self.is_expired and not self.is_verified
    
    def mark_as_verified(self):
        """Marca o token como verificado"""
        self.verified_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def create_for_user(user_id, email):
        """Cria um novo token de verificação para o usuário"""
        # Invalidar tokens existentes para o mesmo email
        existing_tokens = EmailVerificationToken.query.filter_by(
            user_id=user_id,
            email=email,
            verified_at=None
        ).all()
        
        for token in existing_tokens:
            token.mark_as_verified()  # Marca como verificado para invalidar
        
        # Criar novo token
        token_value = Config.generate_secure_token()
        new_token = EmailVerificationToken(
            user_id=user_id,
            email=email,
            token=token_value
        )
        
        db.session.add(new_token)
        db.session.commit()
        return new_token
    
    def __repr__(self):
        return f'<EmailVerificationToken {self.token[:8]}... for {self.email}>'

class UserSession(db.Model):
    """Controle avançado de sessões de usuário"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(100), nullable=False, unique=True, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    location = db.Column(db.String(100))  # Geolocalização baseada no IP
    device_info = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    logout_at = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref='sessions')
    
    @property
    def is_expired(self):
        """Verifica se a sessão expirou por inatividade"""
        if not self.is_active:
            return True
        
        inactive_time = datetime.utcnow() - self.last_activity
        return inactive_time > timedelta(hours=24)  # 24 horas de inatividade
    
    def update_activity(self):
        """Atualiza o timestamp da última atividade"""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def terminate(self):
        """Termina a sessão"""
        self.is_active = False
        self.logout_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<UserSession {self.session_token[:8]}... for User {self.user_id}>' 