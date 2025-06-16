from src.extensions import db
from datetime import datetime
from enum import Enum

class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning" 
    ERROR = "error"
    SYSTEM = "system"
    LEGAL = "legal"
    TASK = "task"
    DOCUMENT = "document"
    AI = "ai"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum(NotificationType), default=NotificationType.INFO)
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Status e timing
    is_read = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    # Metadata
    category = db.Column(db.String(50))
    tags = db.Column(db.JSON)
    meta_data = db.Column(db.JSON)  # Dados adicionais específicos por tipo
    
    # Ações
    action_url = db.Column(db.String(500))
    action_text = db.Column(db.String(100))
    dismiss_url = db.Column(db.String(500))
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type.value if self.type else 'info',
            'priority': self.priority.value if self.priority else 'medium',
            'is_read': self.is_read,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'category': self.category,
            'tags': self.tags,
            'metadata': self.meta_data,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'dismiss_url': self.dismiss_url
        }
    
    def mark_as_read(self):
        """Marca a notificação como lida"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def archive(self):
        """Arquiva a notificação"""
        self.is_archived = True
        db.session.commit()
    
    @classmethod
    def create_notification(cls, user_id, title, message, type=NotificationType.INFO, 
                          priority=NotificationPriority.MEDIUM, **kwargs):
        """Cria uma nova notificação"""
        notification = cls(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            priority=priority,
            **kwargs
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    @classmethod
    def get_user_notifications(cls, user_id, unread_only=False, limit=None):
        """Busca notificações do usuário"""
        query = cls.query.filter_by(user_id=user_id, is_archived=False)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_unread_count(cls, user_id):
        """Conta notificações não lidas"""
        return cls.query.filter_by(
            user_id=user_id, 
            is_read=False, 
            is_archived=False
        ).count()
    
    @classmethod
    def mark_all_as_read(cls, user_id):
        """Marca todas as notificações como lidas"""
        cls.query.filter_by(user_id=user_id, is_read=False).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        db.session.commit()


class NotificationTemplate(db.Model):
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    title_template = db.Column(db.String(200), nullable=False)
    message_template = db.Column(db.Text, nullable=False)
    type = db.Column(db.Enum(NotificationType), default=NotificationType.INFO)
    priority = db.Column(db.Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def create_notification(self, user_id, **template_vars):
        """Cria notificação usando este template"""
        title = self.title_template.format(**template_vars)
        message = self.message_template.format(**template_vars)
        
        return Notification.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            type=self.type,
            priority=self.priority,
            category=self.category
        )


class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Configurações por tipo
    email_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=True)
    browser_enabled = db.Column(db.Boolean, default=True)
    
    # Configurações por categoria
    legal_notifications = db.Column(db.Boolean, default=True)
    task_notifications = db.Column(db.Boolean, default=True)
    document_notifications = db.Column(db.Boolean, default=True)
    ai_notifications = db.Column(db.Boolean, default=True)
    system_notifications = db.Column(db.Boolean, default=True)
    
    # Configurações de timing
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)
    weekend_notifications = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('notification_settings', uselist=False))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'push_enabled': self.push_enabled,
            'browser_enabled': self.browser_enabled,
            'legal_notifications': self.legal_notifications,
            'task_notifications': self.task_notifications,
            'document_notifications': self.document_notifications,
            'ai_notifications': self.ai_notifications,
            'system_notifications': self.system_notifications,
            'quiet_hours_start': self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            'quiet_hours_end': self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            'weekend_notifications': self.weekend_notifications
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_entidade = db.Column(db.Enum('Cartão', 'Wiki', 'Processo', name='comment_entity'), nullable=False)
    entidade_id = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_entidade': self.tipo_entidade,
            'entidade_id': self.entidade_id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else None,
            'texto': self.texto,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }

class Attachment(db.Model):
    __tablename__ = 'attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_entidade = db.Column(db.Enum('Cartão', 'Processo', 'Wiki', name='attachment_entity'), nullable=False)
    entidade_id = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)  # MIME type
    url = db.Column(db.String(255), nullable=False)
    tamanho = db.Column(db.Integer, nullable=False)  # em bytes
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_entidade': self.tipo_entidade,
            'entidade_id': self.entidade_id,
            'nome': self.nome,
            'tipo_arquivo': self.tipo_arquivo,
            'url': self.url,
            'tamanho': self.tamanho,
            'tamanho_mb': round(self.tamanho / (1024 * 1024), 2),
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else None,
            'data_upload': self.data_upload.isoformat() if self.data_upload else None
        } 