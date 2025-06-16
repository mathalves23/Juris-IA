from datetime import datetime
from src.extensions import db
import hashlib
import bcrypt
import re
from typing import Optional


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100))  # Compatibilidade com sistema novo
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255))  # Compatibilidade com sistema novo
    papel = db.Column(db.String(50), default='user')
    foto_url = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    email_verificado = db.Column(db.Boolean, default=False)
    is_email_verified = db.Column(db.Boolean, default=False)  # Compatibilidade com sistema novo
    email_verified_at = db.Column(db.DateTime)  # Novo campo para segurança
    ultimo_login = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)  # Compatibilidade com sistema novo
    login_count = db.Column(db.Integer, default=0)  # Novo campo para estatísticas
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)  # Novo campo para segurança
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    documentos = db.relationship('Document', backref='usuario', lazy=True)
    templates = db.relationship('Template', backref='usuario', lazy=True)
    subscription = db.relationship('Subscription', backref='usuario', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @property
    def display_name(self):
        """Nome para exibição (compatibilidade)"""
        return self.name or self.nome
    
    @property
    def current_password_hash(self):
        """Hash da senha atual (compatibilidade)"""
        return self.password_hash or self.senha_hash
    
    @property
    def email_verification_status(self):
        """Status de verificação do email (compatibilidade)"""
        return self.is_email_verified or self.email_verificado
    
    @property
    def last_login_time(self):
        """Último login (compatibilidade)"""
        return self.last_login or self.ultimo_login
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash da senha usando bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def hash_password_legacy(password: str) -> str:
        """Hash legado para compatibilidade."""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000).hex()
    
    def verify_password(self, password: str) -> bool:
        """Verificar senha."""
        # Usar o hash atual (novo sistema tem prioridade)
        current_hash = self.current_password_hash
        
        # Verificar se é hash do werkzeug (pbkdf2)
        if current_hash.startswith('pbkdf2:'):
            from werkzeug.security import check_password_hash
            return check_password_hash(current_hash, password)
        
        try:
            # Tentar bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), current_hash.encode('utf-8'))
        except ValueError:
            # Fallback para hash legado
            return self.verify_password_legacy(password)
    
    def verify_password_legacy(self, password: str) -> bool:
        """Verificar senha com hash legado."""
        test_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000)
        return test_hash.hex() == self.current_password_hash
    
    def set_password(self, password: str) -> None:
        """Definir nova senha."""
        if not self.validate_password(password):
            raise ValueError("Senha não atende aos critérios de segurança")
        
        # Usar werkzeug para compatibilidade com sistema novo
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(password)
        
        # Atualizar ambos os campos para compatibilidade
        self.password_hash = hashed
        self.senha_hash = hashed
        self.password_changed_at = datetime.utcnow()
    
    def sync_fields(self):
        """Sincronizar campos para compatibilidade entre sistemas"""
        # Sincronizar nomes
        if self.name and not self.nome:
            self.nome = self.name
        elif self.nome and not self.name:
            self.name = self.nome
        
        # Sincronizar verificação de email
        if self.is_email_verified is not None and self.email_verificado != self.is_email_verified:
            self.email_verificado = self.is_email_verified
        elif self.email_verificado is not None and self.is_email_verified != self.email_verificado:
            self.is_email_verified = self.email_verificado
        
        # Sincronizar último login
        if self.last_login and (not self.ultimo_login or self.last_login > self.ultimo_login):
            self.ultimo_login = self.last_login
        elif self.ultimo_login and (not self.last_login or self.ultimo_login > self.last_login):
            self.last_login = self.ultimo_login
        
        # Sincronizar senhas
        if self.password_hash and self.password_hash != self.senha_hash:
            self.senha_hash = self.password_hash
        elif self.senha_hash and self.senha_hash != self.password_hash:
            self.password_hash = self.senha_hash
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """Validar força da senha."""
        if len(password) < 8:
            return False
        
        # Verificar se contém pelo menos:
        # - Uma letra minúscula
        # - Uma letra maiúscula
        # - Um número
        # - Um caractere especial
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
            
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato do email."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_account_locked(self) -> bool:
        """Verificar se a conta está bloqueada."""
        if self.bloqueado_ate:
            return datetime.utcnow() < self.bloqueado_ate
        return False
    
    def increment_login_attempts(self) -> None:
        """Incrementar tentativas de login."""
        self.tentativas_login += 1
        if self.tentativas_login >= 5:
            # Bloquear por 30 minutos
            from datetime import timedelta
            self.bloqueado_ate = datetime.utcnow() + timedelta(minutes=30)
        db.session.commit()
    
    def reset_login_attempts(self) -> None:
        """Resetar tentativas de login."""
        self.tentativas_login = 0
        self.bloqueado_ate = None
        self.ultimo_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Converter para dicionário."""
        data = {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'papel': self.papel,
            'foto_url': self.foto_url,
            'ativo': self.ativo,
            'email_verificado': self.email_verificado,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'tentativas_login': self.tentativas_login,
                'bloqueado_ate': self.bloqueado_ate.isoformat() if self.bloqueado_ate else None
            })
        
        return data
    
    @classmethod
    def create_user(cls, nome: str, email: str, senha: str, papel: str = 'user') -> 'User':
        """Criar novo usuário com validações."""
        # Validar email
        if not cls.validate_email(email):
            raise ValueError("Email inválido")
        
        # Verificar se email já existe
        if cls.query.filter_by(email=email).first():
            raise ValueError("Email já cadastrado")
        
        # Validar nome
        if not nome or len(nome.strip()) < 2:
            raise ValueError("Nome deve ter pelo menos 2 caracteres")
        
        # Validar senha
        if not cls.validate_password(senha):
            raise ValueError("Senha não atende aos critérios de segurança")
        
        # Criar usuário
        user = cls(
            nome=nome.strip(),
            email=email.lower().strip(),
            papel=papel
        )
        user.set_password(senha)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def update_profile(self, **kwargs) -> None:
        """Atualizar perfil do usuário."""
        allowed_fields = ['nome', 'foto_url']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'nome' and (not value or len(value.strip()) < 2):
                    raise ValueError("Nome deve ter pelo menos 2 caracteres")
                setattr(self, field, value)
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def can_access_document(self, document) -> bool:
        """Verificar se pode acessar documento."""
        return document.usuario_id == self.id or self.papel == 'admin'
    
    def can_access_template(self, template) -> bool:
        """Verificar se pode acessar template."""
        return (template.usuario_id == self.id or 
                template.publico or 
                self.papel == 'admin')
    
    @property
    def is_admin(self) -> bool:
        """Verificar se é administrador."""
        return self.papel == 'admin'
    
    @property
    def subscription_active(self) -> bool:
        """Verificar se tem assinatura ativa."""
        return (self.subscription and 
                self.subscription.status == 'ativo')
    
    def get_usage_stats(self) -> dict:
        """Obter estatísticas de uso."""
        return {
            'total_documents': len(self.documentos),
            'total_templates': len(self.templates),
            'documents_this_month': len([d for d in self.documentos 
                                       if d.created_at.month == datetime.utcnow().month]),
            'subscription_status': self.subscription.status if self.subscription else 'free'
        }
