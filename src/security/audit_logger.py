import logging
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from flask import request, g
from flask_jwt_extended import get_jwt_identity
import os

class AuditEventType(Enum):
    """Tipos de eventos de auditoria"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    DOCUMENT_CREATE = "document_create"
    DOCUMENT_UPDATE = "document_update"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_VIEW = "document_view"
    TEMPLATE_CREATE = "template_create"
    TEMPLATE_UPDATE = "template_update"
    TEMPLATE_DELETE = "template_delete"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    AI_REQUEST = "ai_request"
    ADMIN_ACTION = "admin_action"
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT_EXCEED = "rate_limit_exceed"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

class AuditLogger:
    """Sistema de auditoria avançado"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar sistema de auditoria"""
        self.app = app
        
        # Configurar logger de auditoria
        self.setup_audit_logger()
        
        # Registrar middleware
        self.register_middleware()
    
    def setup_audit_logger(self):
        """Configurar logger específico para auditoria"""
        # Criar diretório de logs se não existir
        log_dir = self.app.config.get('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar logger de auditoria
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Handler para arquivo de auditoria
        audit_handler = logging.FileHandler(
            os.path.join(log_dir, 'audit.log'),
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        
        # Formatter estruturado
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(formatter)
        
        self.logger.addHandler(audit_handler)
        
        # Handler para console em desenvolvimento
        if self.app.config.get('FLASK_ENV') == 'development':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def register_middleware(self):
        """Registrar middleware para capturar eventos automáticos"""
        
        @self.app.before_request
        def before_request():
            g.start_time = datetime.utcnow()
            g.request_id = self.generate_request_id()
        
        @self.app.after_request
        def after_request(response):
            # Log de request HTTP
            self.log_http_request(response)
            return response
    
    def generate_request_id(self) -> str:
        """Gerar ID único para request"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_client_info(self) -> Dict[str, Any]:
        """Obter informações do cliente"""
        return {
            'ip_address': request.headers.get('X-Forwarded-For', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', ''),
            'method': request.method,
            'endpoint': request.endpoint,
            'url': request.url,
            'request_id': getattr(g, 'request_id', 'unknown')
        }
    
    def get_user_info(self) -> Dict[str, Any]:
        """Obter informações do usuário autenticado"""
        try:
            user_id = get_jwt_identity()
            if user_id:
                return {
                    'user_id': user_id,
                    'authenticated': True
                }
        except:
            pass
        
        return {
            'user_id': None,
            'authenticated': False
        }
    
    def log_event(self, 
                  event_type: AuditEventType, 
                  message: str,
                  details: Optional[Dict[str, Any]] = None,
                  user_id: Optional[int] = None,
                  severity: str = "INFO"):
        """Log de evento de auditoria"""
        
        if not self.logger:
            return
        
        # Construir evento de auditoria
        audit_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type.value,
            'message': message,
            'severity': severity,
            'client_info': self.get_client_info(),
            'user_info': self.get_user_info() if not user_id else {'user_id': user_id, 'authenticated': True},
            'details': details or {}
        }
        
        # Log estruturado em JSON
        self.logger.info(json.dumps(audit_event, ensure_ascii=False, indent=None))
    
    def log_http_request(self, response):
        """Log de request HTTP"""
        if not self.logger:
            return
        
        # Não logar requests de health check e assets
        if request.endpoint in ['health_check', 'static']:
            return
        
        duration = None
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
        
        http_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'http_request',
            'method': request.method,
            'endpoint': request.endpoint,
            'status_code': response.status_code,
            'duration_seconds': duration,
            'client_info': self.get_client_info(),
            'user_info': self.get_user_info(),
            'response_size': response.content_length
        }
        
        # Log apenas requests importantes ou com erro
        if response.status_code >= 400 or request.method in ['POST', 'PUT', 'DELETE']:
            self.logger.info(json.dumps(http_event, ensure_ascii=False, indent=None))
    
    def log_security_event(self, 
                          event_type: AuditEventType,
                          message: str,
                          details: Optional[Dict[str, Any]] = None,
                          severity: str = "WARNING"):
        """Log de evento de segurança"""
        self.log_event(event_type, message, details, severity=severity)
    
    def log_data_access(self, 
                       resource_type: str,
                       resource_id: int,
                       action: str,
                       success: bool = True):
        """Log de acesso a dados"""
        event_type = AuditEventType.DOCUMENT_VIEW if resource_type == 'document' else AuditEventType.ADMIN_ACTION
        
        self.log_event(
            event_type,
            f"{action} {resource_type} {resource_id}",
            {
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                'success': success
            }
        )

# Instância global
audit_logger = AuditLogger()

# Decorators para facilitar uso
def audit_action(event_type: AuditEventType, message: str = None):
    """Decorator para automatizar audit de ações"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Log de sucesso
                audit_logger.log_event(
                    event_type,
                    message or f"{func.__name__} executado com sucesso",
                    {'function': func.__name__, 'args_count': len(args)}
                )
                
                return result
                
            except Exception as e:
                # Log de erro
                audit_logger.log_event(
                    AuditEventType.SECURITY_VIOLATION,
                    f"Erro em {func.__name__}: {str(e)}",
                    {'function': func.__name__, 'error': str(e)},
                    severity="ERROR"
                )
                raise
        
        return wrapper
    return decorator

def log_login_attempt(success: bool, email: str, reason: str = None):
    """Log de tentativa de login"""
    event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED
    message = f"Login {'bem-sucedido' if success else 'falhou'} para {email}"
    
    details = {'email': email}
    if reason:
        details['reason'] = reason
    
    audit_logger.log_event(event_type, message, details)

def log_document_action(action: str, document_id: int, document_title: str = None):
    """Log de ação em documento"""
    event_type_map = {
        'create': AuditEventType.DOCUMENT_CREATE,
        'update': AuditEventType.DOCUMENT_UPDATE,
        'delete': AuditEventType.DOCUMENT_DELETE,
        'view': AuditEventType.DOCUMENT_VIEW
    }
    
    event_type = event_type_map.get(action, AuditEventType.DOCUMENT_VIEW)
    message = f"Documento {action}: {document_title or document_id}"
    
    audit_logger.log_event(event_type, message, {
        'document_id': document_id,
        'document_title': document_title,
        'action': action
    })

def log_template_action(action: str, template_id: int, template_title: str = None):
    """Log de ação em template"""
    event_type_map = {
        'create': AuditEventType.TEMPLATE_CREATE,
        'update': AuditEventType.TEMPLATE_UPDATE,
        'delete': AuditEventType.TEMPLATE_DELETE
    }
    
    event_type = event_type_map.get(action, AuditEventType.TEMPLATE_CREATE)
    message = f"Template {action}: {template_title or template_id}"
    
    audit_logger.log_event(event_type, message, {
        'template_id': template_id,
        'template_title': template_title,
        'action': action
    }) 