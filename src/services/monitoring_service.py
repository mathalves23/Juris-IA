"""
Serviço de Monitoramento Avançado para JurisIA
Métricas, Logs Estruturados e Alertas
"""
import os
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
import psutil
from functools import wraps

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import structlog

from src.config import Config

# Configuração de logging estruturado
class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricEvent:
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Dict[str, Any]

@dataclass
class LogEvent:
    level: LogLevel
    message: str
    timestamp: datetime
    module: str
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Registra log estruturado"""
        log_event = LogEvent(
            level=level,
            message=message,
            timestamp=datetime.now(),
            module=self.name,
            metadata=kwargs
        )
        
        # Log estruturado em JSON
        log_data = asdict(log_event)
        log_data['timestamp'] = log_data['timestamp'].isoformat()
        
        # Envia para o logger apropriado
        if level == LogLevel.DEBUG:
            self.logger.debug(json.dumps(log_data))
        elif level == LogLevel.INFO:
            self.logger.info(json.dumps(log_data))
        elif level == LogLevel.WARNING:
            self.logger.warning(json.dumps(log_data))
        elif level == LogLevel.ERROR:
            self.logger.error(json.dumps(log_data))
        elif level == LogLevel.CRITICAL:
            self.logger.critical(json.dumps(log_data))
    
    def debug(self, message: str, **kwargs):
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(LogLevel.CRITICAL, message, **kwargs)

class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Incrementa contador"""
        with self.lock:
            full_name = self._make_metric_name(name, tags)
            self.counters[full_name] += value
            
            self._record_metric(MetricEvent(
                name=name,
                value=value,
                unit="count",
                timestamp=datetime.now(),
                tags=tags or {},
                metadata={"type": "counter"}
            ))
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Define valor de gauge"""
        with self.lock:
            full_name = self._make_metric_name(name, tags)
            self.gauges[full_name] = value
            
            self._record_metric(MetricEvent(
                name=name,
                value=value,
                unit="gauge",
                timestamp=datetime.now(),
                tags=tags or {},
                metadata={"type": "gauge"}
            ))
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Adiciona valor ao histograma"""
        with self.lock:
            full_name = self._make_metric_name(name, tags)
            self.histograms[full_name].append(value)
            
            # Mantém apenas os últimos 1000 valores
            if len(self.histograms[full_name]) > 1000:
                self.histograms[full_name] = self.histograms[full_name][-1000:]
            
            self._record_metric(MetricEvent(
                name=name,
                value=value,
                unit="histogram",
                timestamp=datetime.now(),
                tags=tags or {},
                metadata={"type": "histogram"}
            ))
    
    def timer(self, name: str, tags: Dict[str, str] = None):
        """Context manager para medir tempo"""
        return TimerContext(self, name, tags)
    
    def _make_metric_name(self, name: str, tags: Dict[str, str] = None) -> str:
        """Gera nome completo da métrica com tags"""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}#{tag_str}"
    
    def _record_metric(self, metric: MetricEvent):
        """Registra métrica no histórico"""
        self.metrics[metric.name].append(metric)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém todas as métricas"""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    name: {
                        "count": len(values),
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                        "avg": sum(values) / len(values) if values else 0
                    }
                    for name, values in self.histograms.items()
                }
            }
    
    def reset_metrics(self):
        """Reset todas as métricas"""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.metrics.clear()

class TimerContext:
    def __init__(self, collector: MetricsCollector, name: str, tags: Dict[str, str] = None):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.histogram(f"{self.name}_duration", duration * 1000, self.tags)

class SystemMonitor:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: int = 30):
        """Inicia monitoramento de sistema"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento de sistema"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, interval: int):
        """Loop de monitoramento"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error("Erro no monitoramento de sistema", error=str(e))
    
    def _collect_system_metrics(self):
        """Coleta métricas do sistema"""
        # CPU
        cpu_percent = psutil.cpu_percent()
        self.metrics.gauge("system.cpu.usage", cpu_percent, {"unit": "percent"})
        
        # Memória
        memory = psutil.virtual_memory()
        self.metrics.gauge("system.memory.usage", memory.percent, {"unit": "percent"})
        self.metrics.gauge("system.memory.available", memory.available / 1024 / 1024, {"unit": "MB"})
        
        # Disco
        disk = psutil.disk_usage('/')
        self.metrics.gauge("system.disk.usage", disk.percent, {"unit": "percent"})
        self.metrics.gauge("system.disk.free", disk.free / 1024 / 1024 / 1024, {"unit": "GB"})
        
        # Processo atual
        process = psutil.Process()
        self.metrics.gauge("process.memory.rss", process.memory_info().rss / 1024 / 1024, {"unit": "MB"})
        self.metrics.gauge("process.cpu.percent", process.cpu_percent(), {"unit": "percent"})

class AlertManager:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts: List[Dict[str, Any]] = []
        self.thresholds = {
            "system.cpu.usage": {"critical": 90, "warning": 75},
            "system.memory.usage": {"critical": 90, "warning": 80},
            "system.disk.usage": {"critical": 95, "warning": 85},
            "response_time": {"critical": 5000, "warning": 2000}  # ms
        }
    
    def check_alerts(self):
        """Verifica condições de alerta"""
        current_metrics = self.metrics.get_metrics()
        
        for metric_name, thresholds in self.thresholds.items():
            if metric_name in current_metrics.get("gauges", {}):
                value = current_metrics["gauges"][metric_name]
                
                if value >= thresholds["critical"]:
                    self._trigger_alert("critical", metric_name, value, thresholds["critical"])
                elif value >= thresholds["warning"]:
                    self._trigger_alert("warning", metric_name, value, thresholds["warning"])
    
    def _trigger_alert(self, level: str, metric: str, value: float, threshold: float):
        """Dispara alerta"""
        alert = {
            "level": level,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "timestamp": datetime.now(),
            "message": f"{metric} ({value}) ultrapassou o limite {level} ({threshold})"
        }
        
        self.alerts.append(alert)
        
        # Log do alerta
        logger.warning("Alerta disparado", **alert)
        
        # Mantém apenas os últimos 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Obtém alertas ativos das últimas 24h"""
        cutoff = datetime.now() - timedelta(hours=24)
        return [
            alert for alert in self.alerts 
            if alert["timestamp"] > cutoff
        ]

class MonitoringService:
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.metrics = MetricsCollector()
        self.system_monitor = SystemMonitor(self.metrics)
        self.alert_manager = AlertManager(self.metrics)
        self.is_initialized = False
        
        # Configurações
        self.sentry_dsn = getattr(Config, 'SENTRY_DSN', None)
        self.enable_analytics = getattr(Config, 'ENABLE_ANALYTICS', True)
        self.enable_metrics = getattr(Config, 'ENABLE_METRICS', True)
        
        # Storage de eventos
        self.metric_events = deque(maxlen=50000)
        self.analytics_events = deque(maxlen=50000)
        
        # Configurar Sentry se DSN disponível
        if self.sentry_dsn:
            self.setup_sentry()
        
        # Configurar logging estruturado
        self.setup_structured_logging()
        
    def setup_sentry(self):
        """Configura Sentry para error tracking"""
        try:
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                integrations=[
                    FlaskIntegration(auto_enabling_integrations=False),
                    SqlalchemyIntegration()
                ],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment=getattr(Config, 'FLASK_ENV', 'development'),
                release=getattr(Config, 'APP_VERSION', '1.0.0'),
                attach_stacktrace=True,
                send_default_pii=False  # Não enviar PII por segurança
            )
            
            self.logger.info("Sentry configurado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar Sentry: {str(e)}")
    
    def setup_structured_logging(self):
        """Configura logging estruturado com structlog"""
        try:
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
            
            self.logger.info("Logging estruturado configurado")
            
        except Exception as e:
            print(f"Erro ao configurar logging estruturado: {str(e)}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, 
                      duration: float, user_id: Optional[str] = None):
        """Registra métricas de requisição"""
        if not self.enable_metrics:
            return
        
        try:
            # Prometheus metrics
            self.metrics.counter(f"http_requests_total", 1, {
                "method": method,
                "endpoint": endpoint,
                "status": str(status_code)
            })
            
            self.metrics.gauge(f"http_request_duration_seconds", duration, {
                "method": method,
                "endpoint": endpoint
            })
            
            # Real-time stats
            current_minute = int(time.time() // 60)
            self.metrics.gauge(f"active_users_total", 1, {"user_id": user_id})
            
            # Log estruturado
            self.logger.info(
                "HTTP request processed",
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
                user_id=user_id
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar métricas de requisição: {str(e)}")
    
    def record_ai_request(self, model: str, status: str, tokens_used: int = 0,
                         cost: float = 0.0, duration: float = 0.0):
        """Registra métricas de requisições de IA"""
        try:
            self.metrics.counter(f"ai_requests_total", 1, {
                "model": model,
                "status": status
            })
            
            # Métrica personalizada para AI
            metric_event = MetricEvent(
                name="ai_usage",
                value=tokens_used,
                unit="tokens",
                timestamp=datetime.now(),
                tags={
                    "model": model,
                    "status": status,
                    "cost": str(cost),
                    "duration": str(duration)
                },
                metadata={"type": "ai_request"}
            )
            
            self.metric_events.append(metric_event)
            
            self.logger.info(
                "AI request processed",
                model=model,
                status=status,
                tokens_used=tokens_used,
                cost=cost,
                duration=duration
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar métricas de IA: {str(e)}")
    
    def record_contract_analysis(self, status: str, file_type: str, 
                               file_size: int, processing_time: float):
        """Registra métricas de análise de contratos"""
        try:
            self.metrics.counter(f"contract_analyses_total", 1, {
                "status": status
            })
            
            analytics_event = MetricEvent(
                name="contract_analysis",
                value=1,
                unit="analysis",
                timestamp=datetime.now(),
                tags={
                    "status": status,
                    "file_type": file_type,
                    "file_size": file_size,
                    "processing_time": str(processing_time)
                },
                metadata={"type": "analytics"}
            )
            
            self.analytics_events.append(analytics_event)
            
            self.logger.info(
                "Contract analysis completed",
                status=status,
                file_type=file_type,
                file_size=file_size,
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar análise de contrato: {str(e)}")
    
    def record_user_activity(self, user_id: str, activity_type: str, 
                           data: Dict[str, Any] = None):
        """Registra atividade do usuário para analytics"""
        if not self.enable_analytics:
            return
        
        try:
            analytics_event = MetricEvent(
                name="user_activity",
                value=1,
                unit="activity",
                timestamp=datetime.now(),
                tags={
                    "user_id": user_id,
                    "activity_type": activity_type
                },
                metadata={"type": "analytics"}
            )
            
            self.analytics_events.append(analytics_event)
            
            # Atualizar sessão do usuário
            self.update_user_session(user_id, activity_type)
            
            self.logger.info(
                "User activity recorded",
                user_id=user_id,
                activity_type=activity_type,
                data=data
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar atividade do usuário: {str(e)}")
    
    def get_session_id(self, user_id: str) -> str:
        """Obtém ou cria session ID para usuário"""
        if user_id not in self.metrics.gauges:
            self.metrics.gauge(f"active_users_total", 1, {"user_id": user_id})
        
        return f"session_{user_id}_{int(time.time())}"
    
    def update_user_session(self, user_id: str, activity_type: str):
        """Atualiza informações da sessão do usuário"""
        if user_id in self.metrics.gauges:
            self.metrics.gauge(f"active_users_total", 1, {"user_id": user_id})
        
        # Atualizar contagem de usuários ativos
        self.update_active_users_count()
    
    def update_active_users_count(self):
        """Atualiza contagem de usuários ativos"""
        try:
            current_time = time.time()
            active_threshold = current_time - 300  # 5 minutos
            
            active_users = sum(
                1 for user_id, _ in self.metrics.gauges.items()
                if user_id.startswith("active_users_total") and current_time > active_threshold
            )
            
            self.metrics.gauge(f"active_users_total", active_users)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar usuários ativos: {str(e)}")
    
    def record_database_query(self, operation: str):
        """Registra query do banco de dados"""
        try:
            self.metrics.counter(f"database_queries_total", 1, {
                "operation": operation
            })
        except Exception as e:
            self.logger.error(f"Erro ao registrar query de banco: {str(e)}")
    
    def get_prometheus_metrics(self) -> str:
        """Retorna métricas no formato Prometheus"""
        try:
            return generate_latest()
        except Exception as e:
            self.logger.error(f"Erro ao gerar métricas Prometheus: {str(e)}")
            return ""
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas em tempo real"""
        try:
            current_time = time.time()
            
            # Calcular RPM (requests per minute)
            current_minute = int(current_time // 60)
            recent_requests = [
                req for req in self.metrics.histograms.get(f"http_request_duration_seconds", [])
                if req >= current_minute - 5
            ]
            rpm = sum(recent_requests) / 5
            
            # Calcular média de tempo de resposta
            response_times = list(self.metrics.histograms.get(f"http_request_duration_seconds", []))
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calcular taxa de erro
            recent_errors = [
                err for err in self.metrics.histograms.get(f"http_request_duration_seconds", [])
                if err >= current_minute - 5
            ]
            error_rate = sum(recent_errors) / len(recent_requests) if recent_requests else 0
            
            return {
                'requests_per_minute': rpm,
                'average_response_time': avg_response_time,
                'error_rate': error_rate,
                'active_users': len(self.metrics.gauges),
                'timestamp': current_time
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas: {str(e)}")
            return {}
    
    def get_analytics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Retorna resumo de analytics das últimas horas"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            recent_events = [
                event for event in self.analytics_events
                if event.timestamp.timestamp() > cutoff_time
            ]
            
            # Agrupar por tipo de evento
            events_by_type = defaultdict(int)
            users_active = set()
            
            for event in recent_events:
                events_by_type[event.name] += 1
                if event.name.startswith("active_users_total"):
                    users_active.add(event.name.split("_")[1])
            
            return {
                'total_events': len(recent_events),
                'unique_users': len(users_active),
                'events_by_type': dict(events_by_type),
                'time_period_hours': hours,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo de analytics: {str(e)}")
            return {}
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """Registra erro com contexto adicional"""
        try:
            # Enviar para Sentry se configurado
            if self.sentry_dsn:
                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_tag(key, value)
                    
                    sentry_sdk.capture_exception(error)
            
            # Log estruturado
            self.logger.error(
                "Error occurred",
                error_type=type(error).__name__,
                error_message=str(error),
                context=context
            )
            
        except Exception as e:
            print(f"Erro ao registrar erro: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde dos sistemas de monitoramento"""
        health = {
            'monitoring_service': 'healthy',
            'sentry_configured': bool(self.sentry_dsn),
            'metrics_enabled': self.enable_metrics,
            'analytics_enabled': self.enable_analytics,
            'events_in_buffer': len(self.analytics_events),
            'metrics_in_buffer': len(self.metric_events),
            'active_user_sessions': len(self.metrics.gauges)
        }
        
        return health

    def start(self):
        """Inicia serviço de monitoramento"""
        self.system_monitor.start_monitoring()
        self.logger.info("Serviço de monitoramento iniciado")
    
    def stop(self):
        """Para serviço de monitoramento"""
        self.system_monitor.stop_monitoring()
        self.logger.info("Serviço de monitoramento parado")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtém dados para dashboard de monitoramento"""
        return {
            "metrics": self.metrics.get_metrics(),
            "alerts": self.alert_manager.get_active_alerts(),
            "system_status": self._get_system_status(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_system_status(self) -> Dict[str, str]:
        """Obtém status geral do sistema"""
        metrics = self.metrics.get_metrics()
        status = {"overall": "healthy"}
        
        # Verifica CPU
        cpu_usage = metrics.get("gauges", {}).get("system.cpu.usage", 0)
        if cpu_usage > 90:
            status["cpu"] = "critical"
        elif cpu_usage > 75:
            status["cpu"] = "warning"
        else:
            status["cpu"] = "healthy"
        
        # Verifica memória
        memory_usage = metrics.get("gauges", {}).get("system.memory.usage", 0)
        if memory_usage > 90:
            status["memory"] = "critical"
        elif memory_usage > 80:
            status["memory"] = "warning"
        else:
            status["memory"] = "healthy"
        
        # Status geral baseado no pior componente
        if any(s == "critical" for s in status.values()):
            status["overall"] = "critical"
        elif any(s == "warning" for s in status.values()):
            status["overall"] = "warning"
        
        return status

# Decoradores para monitoramento automático
def monitor_performance(name: str = None, tags: Dict[str, str] = None):
    """Decorador para monitorar performance de funções"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metric_name = name or f"{func.__module__}.{func.__name__}"
            
            with monitoring_service.metrics.timer(metric_name, tags):
                try:
                    result = func(*args, **kwargs)
                    monitoring_service.metrics.counter(f"{metric_name}.success", tags=tags)
                    return result
                except Exception as e:
                    monitoring_service.metrics.counter(f"{metric_name}.error", tags=tags)
                    logger.error(f"Erro em {metric_name}", error=str(e), function=func.__name__)
                    raise
        return wrapper
    return decorator

def monitor_api_endpoint(endpoint: str = None):
    """Decorador específico para endpoints da API"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            endpoint_name = endpoint or func.__name__
            tags = {"endpoint": endpoint_name}
            
            with monitoring_service.metrics.timer("api.request", tags):
                try:
                    result = func(*args, **kwargs)
                    monitoring_service.metrics.counter("api.request.success", tags=tags)
                    return result
                except Exception as e:
                    monitoring_service.metrics.counter("api.request.error", tags=tags)
                    logger.error("Erro na API", endpoint=endpoint_name, error=str(e))
                    raise
        return wrapper
    return decorator

# Instâncias globais
logger = StructuredLogger("jurisia.monitoring")
monitoring_service = MonitoringService()

# Funções de conveniência
def start_monitoring():
    """Inicia monitoramento"""
    monitoring_service.start()

def stop_monitoring():
    """Para monitoramento"""
    monitoring_service.stop()

def get_metrics():
    """Obtém métricas atuais"""
    return monitoring_service.metrics.get_metrics()

def record_metric(name: str, value: float, metric_type: str = "gauge", tags: Dict[str, str] = None):
    """Registra métrica"""
    if metric_type == "counter":
        monitoring_service.metrics.counter(name, int(value), tags)
    elif metric_type == "gauge":
        monitoring_service.metrics.gauge(name, value, tags)
    elif metric_type == "histogram":
        monitoring_service.metrics.histogram(name, value, tags) 