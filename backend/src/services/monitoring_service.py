import structlog
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import os
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
from flask import request, g
import functools

# Configurar Sentry para monitoramento de erros
def configure_sentry(app):
    """Configurar Sentry para monitoramento de erros em produção"""
    sentry_dsn = os.getenv('SENTRY_DSN')
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FlaskIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            environment=os.getenv('ENVIRONMENT', 'development'),
            release=os.getenv('APP_VERSION', '1.0.0')
        )

# Configurar logging estruturado
def configure_structured_logging():
    """Configurar logging estruturado com structlog"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

@dataclass
class SystemMetrics:
    """Métricas do sistema"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    response_time_avg: float
    error_rate: float
    requests_per_minute: int

@dataclass
class UserActivity:
    """Atividade do usuário"""
    user_id: int
    action: str
    resource: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None

class MetricsCollector:
    """Coletor de métricas da aplicação"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)
        self.error_count = defaultdict(int)
        self.request_count = defaultdict(int)
        self.user_activities = deque(maxlen=10000)
        self.redis_client = None
        
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
        except:
            pass
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Registrar métricas de request"""
        self.request_times.append(duration_ms)
        
        key = f"{method}:{endpoint}"
        self.request_count[key] += 1
        
        if status_code >= 400:
            self.error_count[key] += 1
        
        # Armazenar no Redis se disponível
        if self.redis_client:
            try:
                minute_key = f"requests:{datetime.now().strftime('%Y-%m-%d:%H:%M')}"
                self.redis_client.incr(minute_key)
                self.redis_client.expire(minute_key, 3600)  # Expira em 1 hora
                
                if status_code >= 400:
                    error_key = f"errors:{datetime.now().strftime('%Y-%m-%d:%H:%M')}"
                    self.redis_client.incr(error_key)
                    self.redis_client.expire(error_key, 3600)
            except:
                pass
    
    def record_user_activity(self, user_id: int, action: str, resource: str, 
                           success: bool = True, error_message: str = None, 
                           duration_ms: int = None):
        """Registrar atividade do usuário"""
        activity = UserActivity(
            user_id=user_id,
            action=action,
            resource=resource,
            timestamp=datetime.now(),
            ip_address=getattr(request, 'remote_addr', 'unknown'),
            user_agent=getattr(request, 'user_agent', {}).get('string', 'unknown'),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        
        self.user_activities.append(activity)
        
        # Log estruturado
        logger = structlog.get_logger("user_activity")
        logger.info(
            "user_activity",
            user_id=user_id,
            action=action,
            resource=resource,
            success=success,
            duration_ms=duration_ms,
            ip_address=activity.ip_address
        )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Obter métricas do sistema"""
        # Métricas de sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Métricas da aplicação
        avg_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
        total_requests = sum(self.request_count.values())
        total_errors = sum(self.error_count.values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Requests por minuto (últimos dados)
        current_minute = datetime.now().strftime('%Y-%m-%d:%H:%M')
        requests_per_minute = 0
        if self.redis_client:
            try:
                requests_per_minute = int(self.redis_client.get(f"requests:{current_minute}") or 0)
            except:
                pass
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            active_connections=len(psutil.net_connections()),
            response_time_avg=avg_response_time,
            error_rate=error_rate,
            requests_per_minute=requests_per_minute
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Verificar status de saúde da aplicação"""
        metrics = self.get_system_metrics()
        
        # Definir thresholds
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'cpu': {
                    'status': 'healthy' if metrics.cpu_percent < 80 else 'warning' if metrics.cpu_percent < 95 else 'critical',
                    'value': metrics.cpu_percent,
                    'threshold': 80
                },
                'memory': {
                    'status': 'healthy' if metrics.memory_percent < 80 else 'warning' if metrics.memory_percent < 95 else 'critical',
                    'value': metrics.memory_percent,
                    'threshold': 80
                },
                'disk': {
                    'status': 'healthy' if metrics.disk_percent < 80 else 'warning' if metrics.disk_percent < 95 else 'critical',
                    'value': metrics.disk_percent,
                    'threshold': 80
                },
                'response_time': {
                    'status': 'healthy' if metrics.response_time_avg < 1000 else 'warning' if metrics.response_time_avg < 3000 else 'critical',
                    'value': metrics.response_time_avg,
                    'threshold': 1000
                },
                'error_rate': {
                    'status': 'healthy' if metrics.error_rate < 5 else 'warning' if metrics.error_rate < 10 else 'critical',
                    'value': metrics.error_rate,
                    'threshold': 5
                }
            }
        }
        
        # Determinar status geral
        critical_checks = [check for check in health_status['checks'].values() if check['status'] == 'critical']
        warning_checks = [check for check in health_status['checks'].values() if check['status'] == 'warning']
        
        if critical_checks:
            health_status['status'] = 'critical'
        elif warning_checks:
            health_status['status'] = 'warning'
        
        return health_status

class AlertManager:
    """Gerenciador de alertas"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alert_history = deque(maxlen=1000)
        self.alert_cooldown = {}  # Para evitar spam de alertas
        self.logger = structlog.get_logger("alerts")
    
    def check_alerts(self):
        """Verificar e disparar alertas se necessário"""
        health_status = self.metrics_collector.get_health_status()
        
        for check_name, check_data in health_status['checks'].items():
            if check_data['status'] in ['warning', 'critical']:
                self._send_alert(check_name, check_data)
    
    def _send_alert(self, check_name: str, check_data: Dict[str, Any]):
        """Enviar alerta"""
        alert_key = f"{check_name}_{check_data['status']}"
        now = datetime.now()
        
        # Verificar cooldown (evitar spam)
        if alert_key in self.alert_cooldown:
            if now - self.alert_cooldown[alert_key] < timedelta(minutes=15):
                return
        
        self.alert_cooldown[alert_key] = now
        
        alert_data = {
            'timestamp': now.isoformat(),
            'type': check_name,
            'status': check_data['status'],
            'value': check_data['value'],
            'threshold': check_data['threshold'],
            'message': f"{check_name.upper()} {check_data['status']}: {check_data['value']}% (threshold: {check_data['threshold']}%)"
        }
        
        self.alert_history.append(alert_data)
        
        # Log do alerta
        self.logger.warning(
            "system_alert",
            **alert_data
        )
        
        # Aqui você pode integrar com sistemas de notificação
        # como Slack, Discord, email, SMS, etc.
        self._notify_external_systems(alert_data)
    
    def _notify_external_systems(self, alert_data: Dict[str, Any]):
        """Notificar sistemas externos (Slack, email, etc.)"""
        # Implementar integrações com sistemas de notificação
        pass

# Singleton para o coletor de métricas
metrics_collector = MetricsCollector()
alert_manager = AlertManager(metrics_collector)

def monitor_request(f):
    """Decorator para monitorar requests"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
            success = status_code < 400
        except Exception as e:
            status_code = 500
            success = False
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Registrar métricas
            endpoint = request.endpoint or 'unknown'
            method = request.method
            metrics_collector.record_request(endpoint, method, status_code, duration_ms)
            
            # Registrar atividade do usuário se autenticado
            if hasattr(g, 'current_user') and g.current_user:
                metrics_collector.record_user_activity(
                    user_id=g.current_user.id,
                    action=method,
                    resource=endpoint,
                    success=success,
                    duration_ms=int(duration_ms)
                )
        
        return result
    return decorated_function

def setup_monitoring_background_tasks():
    """Configurar tarefas de background para monitoramento"""
    def monitoring_loop():
        while True:
            try:
                # Verificar alertas a cada 5 minutos
                alert_manager.check_alerts()
                
                # Log de métricas a cada 10 minutos
                metrics = metrics_collector.get_system_metrics()
                logger = structlog.get_logger("system_metrics")
                logger.info("system_metrics", **asdict(metrics))
                
                time.sleep(300)  # 5 minutos
            except Exception as e:
                structlog.get_logger("monitoring").error("monitoring_error", error=str(e))
                time.sleep(60)  # Retry em 1 minuto se houver erro
    
    # Iniciar thread de monitoramento
    monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitoring_thread.start()

def init_monitoring(app):
    """Inicializar sistema de monitoramento"""
    configure_sentry(app)
    configure_structured_logging()
    setup_monitoring_background_tasks()
    
    # Adicionar rotas de monitoramento
    @app.route('/api/health')
    def health_check():
        return metrics_collector.get_health_status()
    
    @app.route('/api/metrics')
    def get_metrics():
        metrics = metrics_collector.get_system_metrics()
        return asdict(metrics)
    
    @app.route('/api/alerts')
    def get_alerts():
        return {
            'alerts': list(alert_manager.alert_history),
            'total': len(alert_manager.alert_history)
        }
    
    return app 