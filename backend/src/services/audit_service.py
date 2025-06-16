import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
import hmac
import os
from flask import request, g
from collections import deque
import threading
import sqlite3
from contextlib import contextmanager

class AuditEventType(Enum):
    """Tipos de eventos de auditoria"""
    # Autenticação
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # Autorização
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGE = "permission_change"
    
    # Documentos
    DOCUMENT_CREATE = "document_create"
    DOCUMENT_READ = "document_read"
    DOCUMENT_UPDATE = "document_update"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_SHARE = "document_share"
    DOCUMENT_DOWNLOAD = "document_download"
    
    # Templates
    TEMPLATE_CREATE = "template_create"
    TEMPLATE_UPDATE = "template_update"
    TEMPLATE_DELETE = "template_delete"
    TEMPLATE_USE = "template_use"
    
    # IA
    AI_GENERATE = "ai_generate"
    AI_REVIEW = "ai_review"
    AI_SUMMARIZE = "ai_summarize"
    
    # Sistema
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    
    # Segurança
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"

class RiskLevel(Enum):
    """Níveis de risco"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Evento de auditoria"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[int]
    user_email: Optional[str]
    ip_address: str
    user_agent: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    risk_level: RiskLevel
    success: bool
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        data['risk_level'] = self.risk_level.value
        return data

class SecurityAnalyzer:
    """Analisador de segurança para detectar atividades suspeitas"""
    
    def __init__(self):
        self.failed_logins = deque(maxlen=10000)
        self.suspicious_ips = set()
        self.rate_limits = {}
        self.logger = structlog.get_logger("security")
    
    def analyze_login_attempt(self, user_email: str, ip_address: str, success: bool) -> RiskLevel:
        """Analisar tentativa de login"""
        now = datetime.now()
        
        if not success:
            # Registrar tentativa falhada
            self.failed_logins.append({
                'email': user_email,
                'ip': ip_address,
                'timestamp': now
            })
            
            # Verificar tentativas de força bruta
            recent_failures = [
                f for f in self.failed_logins 
                if f['email'] == user_email and 
                   now - f['timestamp'] < timedelta(minutes=15)
            ]
            
            if len(recent_failures) >= 5:
                self.suspicious_ips.add(ip_address)
                return RiskLevel.CRITICAL
            elif len(recent_failures) >= 3:
                return RiskLevel.HIGH
            else:
                return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def analyze_request_pattern(self, user_id: int, ip_address: str, endpoint: str) -> RiskLevel:
        """Analisar padrão de requests"""
        now = datetime.now()
        key = f"{user_id}:{ip_address}:{endpoint}"
        
        if key not in self.rate_limits:
            self.rate_limits[key] = deque(maxlen=100)
        
        # Limpar requests antigos (últimos 5 minutos)
        self.rate_limits[key] = deque([
            req_time for req_time in self.rate_limits[key]
            if now - req_time < timedelta(minutes=5)
        ], maxlen=100)
        
        self.rate_limits[key].append(now)
        
        # Verificar rate limiting
        requests_count = len(self.rate_limits[key])
        
        if requests_count > 100:  # Mais de 100 requests em 5 minutos
            return RiskLevel.CRITICAL
        elif requests_count > 50:
            return RiskLevel.HIGH
        elif requests_count > 20:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def is_suspicious_ip(self, ip_address: str) -> bool:
        """Verificar se IP é suspeito"""
        return ip_address in self.suspicious_ips

class AuditLogger:
    """Logger de auditoria com persistência"""
    
    def __init__(self, db_path: str = "audit.db"):
        self.db_path = db_path
        self.logger = structlog.get_logger("audit")
        self.security_analyzer = SecurityAnalyzer()
        self._init_database()
        
    def _init_database(self):
        """Inicializar banco de dados de auditoria"""
        with self._get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    user_email TEXT,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    resource_type TEXT,
                    resource_id TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    risk_level TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    session_id TEXT,
                    request_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Índices para performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_risk_level ON audit_events(risk_level)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ip_address ON audit_events(ip_address)")
    
    @contextmanager
    def _get_db_connection(self):
        """Obter conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _generate_event_id(self, event: AuditEvent) -> str:
        """Gerar ID único para o evento"""
        data = f"{event.timestamp.isoformat()}{event.user_id}{event.ip_address}{event.action}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Obter contexto da requisição atual"""
        context = {
            'ip_address': 'unknown',
            'user_agent': 'unknown',
            'session_id': None,
            'request_id': None
        }
        
        if request:
            context.update({
                'ip_address': request.remote_addr or 'unknown',
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'session_id': request.headers.get('X-Session-ID'),
                'request_id': request.headers.get('X-Request-ID')
            })
        
        return context
    
    def log_event(self, 
                  event_type: AuditEventType,
                  action: str,
                  success: bool = True,
                  user_id: Optional[int] = None,
                  user_email: Optional[str] = None,
                  resource_type: Optional[str] = None,
                  resource_id: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  error_message: Optional[str] = None,
                  risk_level: Optional[RiskLevel] = None) -> AuditEvent:
        """Registrar evento de auditoria"""
        
        context = self._get_request_context()
        
        # Obter usuário atual se não fornecido
        if not user_id and hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user.id
            user_email = g.current_user.email
        
        # Analisar risco se não fornecido
        if risk_level is None:
            if event_type in [AuditEventType.LOGIN_SUCCESS, AuditEventType.LOGIN_FAILED]:
                risk_level = self.security_analyzer.analyze_login_attempt(
                    user_email or 'unknown', 
                    context['ip_address'], 
                    success
                )
            elif user_id:
                risk_level = self.security_analyzer.analyze_request_pattern(
                    user_id, 
                    context['ip_address'], 
                    action
                )
            else:
                risk_level = RiskLevel.LOW
        
        # Criar evento
        event = AuditEvent(
            id=None,  # Será gerado
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=context['ip_address'],
            user_agent=context['user_agent'],
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            risk_level=risk_level,
            success=success,
            error_message=error_message,
            session_id=context['session_id'],
            request_id=context['request_id']
        )
        
        event.id = self._generate_event_id(event)
        
        # Persistir no banco
        self._save_to_database(event)
        
        # Log estruturado
        self.logger.info(
            "audit_event",
            **event.to_dict()
        )
        
        # Alertas de segurança
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._send_security_alert(event)
        
        return event
    
    def _save_to_database(self, event: AuditEvent):
        """Salvar evento no banco de dados"""
        try:
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_events (
                        id, timestamp, event_type, user_id, user_email,
                        ip_address, user_agent, resource_type, resource_id,
                        action, details, risk_level, success, error_message,
                        session_id, request_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.id,
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.user_id,
                    event.user_email,
                    event.ip_address,
                    event.user_agent,
                    event.resource_type,
                    event.resource_id,
                    event.action,
                    json.dumps(event.details),
                    event.risk_level.value,
                    event.success,
                    event.error_message,
                    event.session_id,
                    event.request_id
                ))
        except Exception as e:
            self.logger.error("failed_to_save_audit_event", error=str(e), event_id=event.id)
    
    def _send_security_alert(self, event: AuditEvent):
        """Enviar alerta de segurança"""
        alert_logger = structlog.get_logger("security_alert")
        alert_logger.warning(
            "security_alert",
            event_id=event.id,
            event_type=event.event_type.value,
            risk_level=event.risk_level.value,
            user_id=event.user_id,
            ip_address=event.ip_address,
            action=event.action,
            details=event.details
        )
    
    def get_events(self, 
                   user_id: Optional[int] = None,
                   event_type: Optional[AuditEventType] = None,
                   risk_level: Optional[RiskLevel] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Obter eventos de auditoria"""
        
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level.value)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(query, params)
                events = []
                for row in cursor.fetchall():
                    event_dict = dict(row)
                    event_dict['details'] = json.loads(event_dict['details'] or '{}')
                    events.append(event_dict)
                return events
        except Exception as e:
            self.logger.error("failed_to_get_audit_events", error=str(e))
            return []
    
    def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """Obter resumo de segurança"""
        start_date = datetime.now() - timedelta(days=days)
        
        try:
            with self._get_db_connection() as conn:
                # Total de eventos
                total_events = conn.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE timestamp >= ?",
                    (start_date.isoformat(),)
                ).fetchone()[0]
                
                # Eventos por nível de risco
                risk_summary = {}
                for risk in RiskLevel:
                    count = conn.execute(
                        "SELECT COUNT(*) FROM audit_events WHERE timestamp >= ? AND risk_level = ?",
                        (start_date.isoformat(), risk.value)
                    ).fetchone()[0]
                    risk_summary[risk.value] = count
                
                # Top IPs suspeitos
                suspicious_ips = conn.execute("""
                    SELECT ip_address, COUNT(*) as count 
                    FROM audit_events 
                    WHERE timestamp >= ? AND risk_level IN ('high', 'critical')
                    GROUP BY ip_address 
                    ORDER BY count DESC 
                    LIMIT 10
                """, (start_date.isoformat(),)).fetchall()
                
                # Tentativas de login falhadas
                failed_logins = conn.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE timestamp >= ? AND event_type = ? AND success = 0",
                    (start_date.isoformat(), AuditEventType.LOGIN_FAILED.value)
                ).fetchone()[0]
                
                return {
                    'period_days': days,
                    'total_events': total_events,
                    'risk_summary': risk_summary,
                    'suspicious_ips': [dict(row) for row in suspicious_ips],
                    'failed_logins': failed_logins,
                    'generated_at': datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error("failed_to_get_security_summary", error=str(e))
            return {}

# Singleton para o audit logger
audit_logger = AuditLogger()

def audit_event(event_type: AuditEventType, action: str, **kwargs):
    """Decorator para auditoria automática"""
    def decorator(f):
        def wrapper(*args, **func_kwargs):
            start_time = datetime.now()
            success = True
            error_message = None
            
            try:
                result = f(*args, **func_kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                details = kwargs.get('details', {})
                details['duration_ms'] = duration_ms
                
                audit_logger.log_event(
                    event_type=event_type,
                    action=action,
                    success=success,
                    error_message=error_message,
                    details=details,
                    **{k: v for k, v in kwargs.items() if k != 'details'}
                )
        
        return wrapper
    return decorator

def init_audit_system(app):
    """Inicializar sistema de auditoria"""
    
    @app.route('/api/audit/events')
    def get_audit_events():
        """Obter eventos de auditoria (apenas para admins)"""
        # Verificar se usuário é admin
        if not (hasattr(g, 'current_user') and g.current_user and g.current_user.is_admin):
            audit_logger.log_event(
                AuditEventType.ACCESS_DENIED,
                "get_audit_events",
                success=False,
                error_message="Access denied - admin required"
            )
            return {'error': 'Access denied'}, 403
        
        # Parâmetros de filtro
        user_id = request.args.get('user_id', type=int)
        event_type = request.args.get('event_type')
        risk_level = request.args.get('risk_level')
        limit = request.args.get('limit', 100, type=int)
        
        # Converter strings para enums
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                pass
        
        risk_level_enum = None
        if risk_level:
            try:
                risk_level_enum = RiskLevel(risk_level)
            except ValueError:
                pass
        
        events = audit_logger.get_events(
            user_id=user_id,
            event_type=event_type_enum,
            risk_level=risk_level_enum,
            limit=min(limit, 1000)  # Máximo 1000 eventos
        )
        
        audit_logger.log_event(
            AuditEventType.DATA_EXPORT,
            "get_audit_events",
            details={'events_count': len(events)}
        )
        
        return {'events': events, 'total': len(events)}
    
    @app.route('/api/audit/security-summary')
    def get_security_summary():
        """Obter resumo de segurança (apenas para admins)"""
        if not (hasattr(g, 'current_user') and g.current_user and g.current_user.is_admin):
            return {'error': 'Access denied'}, 403
        
        days = request.args.get('days', 7, type=int)
        summary = audit_logger.get_security_summary(days=days)
        
        audit_logger.log_event(
            AuditEventType.DATA_EXPORT,
            "get_security_summary",
            details={'days': days}
        )
        
        return summary
    
    return app 