"""
Sistema de Monitoramento de Performance
Métricas em tempo real para aplicação jurídica
"""
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """Métricas do sistema"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    response_time: float

@dataclass
class ApplicationMetrics:
    """Métricas da aplicação"""
    timestamp: datetime
    active_users: int
    requests_per_minute: int
    error_rate: float
    average_response_time: float
    database_connections: int
    cache_hit_rate: float

class PerformanceMonitor:
    """Monitor de performance em tempo real"""
    
    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.max_samples = retention_minutes * 6  # 1 sample a cada 10s
        
        # Buffers circulares para métricas
        self.system_metrics = deque(maxlen=self.max_samples)
        self.app_metrics = deque(maxlen=self.max_samples)
        self.request_logs = deque(maxlen=1000)
        
        # Threading para coleta contínua
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Contadores para métricas da aplicação
        self.request_counter = 0
        self.error_counter = 0
        self.response_times = deque(maxlen=100)
        self.last_reset_time = datetime.now()
        
        # Alertas configurados
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'response_time': 5000.0,  # ms
            'error_rate': 5.0  # %
        }
        
        self.active_alerts = []
    
    def start_monitoring(self):
        """Iniciar monitoramento contínuo"""
        if self.monitoring_active:
            logger.warning("Monitoramento já está ativo")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Monitoramento de performance iniciado")
    
    def stop_monitoring(self):
        """Parar monitoramento"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitoramento de performance parado")
    
    def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.monitoring_active:
            try:
                # Coletar métricas do sistema
                system_metrics = self._collect_system_metrics()
                self.system_metrics.append(system_metrics)
                
                # Coletar métricas da aplicação
                app_metrics = self._collect_app_metrics()
                self.app_metrics.append(app_metrics)
                
                # Verificar alertas
                self._check_alerts(system_metrics, app_metrics)
                
                time.sleep(10)  # Coleta a cada 10 segundos
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(30)  # Aguardar mais tempo em caso de erro
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Coletar métricas do sistema operacional"""
        
        # CPU
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memória
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disco
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # Rede
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }
        
        # Conexões ativas (simulado)
        active_connections = len(psutil.net_connections())
        
        # Tempo de resposta simulado
        response_time = self._get_average_response_time()
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            active_connections=active_connections,
            response_time=response_time
        )
    
    def _collect_app_metrics(self) -> ApplicationMetrics:
        """Coletar métricas da aplicação"""
        
        current_time = datetime.now()
        time_diff = (current_time - self.last_reset_time).total_seconds() / 60  # minutos
        
        # Requests por minuto
        rpm = self.request_counter / max(time_diff, 1)
        
        # Taxa de erro
        error_rate = (self.error_counter / max(self.request_counter, 1)) * 100
        
        # Tempo médio de resposta
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        # Usuários ativos (simulado)
        active_users = self._estimate_active_users()
        
        # Conexões do banco (simulado)
        db_connections = 8
        
        # Cache hit rate (simulado)
        cache_hit_rate = 85.5
        
        return ApplicationMetrics(
            timestamp=current_time,
            active_users=active_users,
            requests_per_minute=int(rpm),
            error_rate=error_rate,
            average_response_time=avg_response_time,
            database_connections=db_connections,
            cache_hit_rate=cache_hit_rate
        )
    
    def _estimate_active_users(self) -> int:
        """Estimar usuários ativos baseado em requests recentes"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_requests = [log for log in self.request_logs if log['timestamp'] >= cutoff_time]
        unique_ips = len(set(log.get('ip', 'unknown') for log in recent_requests))
        return max(unique_ips, 1)
    
    def _get_average_response_time(self) -> float:
        """Obter tempo médio de resposta"""
        if not self.response_times:
            return 250.0  # Default 250ms
        return sum(self.response_times) / len(self.response_times)
    
    def _check_alerts(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Verificar condições de alerta"""
        
        new_alerts = []
        
        # Alertas de sistema
        if system_metrics.cpu_usage > self.alert_thresholds['cpu_usage']:
            new_alerts.append({
                'type': 'system',
                'level': 'warning',
                'metric': 'cpu_usage',
                'value': system_metrics.cpu_usage,
                'threshold': self.alert_thresholds['cpu_usage'],
                'message': f"Alto uso de CPU: {system_metrics.cpu_usage:.1f}%"
            })
        
        if system_metrics.memory_usage > self.alert_thresholds['memory_usage']:
            new_alerts.append({
                'type': 'system',
                'level': 'warning',
                'metric': 'memory_usage',
                'value': system_metrics.memory_usage,
                'threshold': self.alert_thresholds['memory_usage'],
                'message': f"Alto uso de memória: {system_metrics.memory_usage:.1f}%"
            })
        
        if system_metrics.disk_usage > self.alert_thresholds['disk_usage']:
            new_alerts.append({
                'type': 'system',
                'level': 'critical',
                'metric': 'disk_usage',
                'value': system_metrics.disk_usage,
                'threshold': self.alert_thresholds['disk_usage'],
                'message': f"Espaço em disco baixo: {system_metrics.disk_usage:.1f}%"
            })
        
        # Alertas de aplicação
        if app_metrics.average_response_time > self.alert_thresholds['response_time']:
            new_alerts.append({
                'type': 'application',
                'level': 'warning',
                'metric': 'response_time',
                'value': app_metrics.average_response_time,
                'threshold': self.alert_thresholds['response_time'],
                'message': f"Tempo de resposta alto: {app_metrics.average_response_time:.0f}ms"
            })
        
        if app_metrics.error_rate > self.alert_thresholds['error_rate']:
            new_alerts.append({
                'type': 'application',
                'level': 'critical',
                'metric': 'error_rate',
                'value': app_metrics.error_rate,
                'threshold': self.alert_thresholds['error_rate'],
                'message': f"Taxa de erro alta: {app_metrics.error_rate:.1f}%"
            })
        
        # Atualizar alertas ativos
        for alert in new_alerts:
            alert['timestamp'] = datetime.now()
            alert['id'] = f"{alert['metric']}_{int(time.time())}"
            
            # Verificar se já existe alerta similar ativo
            existing = any(
                a['metric'] == alert['metric'] and a['level'] == alert['level'] 
                for a in self.active_alerts
            )
            
            if not existing:
                self.active_alerts.append(alert)
                logger.warning(f"Novo alerta: {alert['message']}")
        
        # Remover alertas antigos (>30 minutos)
        cutoff_time = datetime.now() - timedelta(minutes=30)
        self.active_alerts = [
            alert for alert in self.active_alerts 
            if alert['timestamp'] > cutoff_time
        ]
    
    def log_request(self, ip: str, endpoint: str, method: str, 
                   response_time: float, status_code: int):
        """Registrar request para métricas"""
        
        self.request_counter += 1
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.error_counter += 1
        
        # Log do request
        request_log = {
            'timestamp': datetime.now(),
            'ip': ip,
            'endpoint': endpoint,
            'method': method,
            'response_time': response_time,
            'status_code': status_code,
            'is_error': status_code >= 400
        }
        
        self.request_logs.append(request_log)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Obter status atual do sistema"""
        
        if not self.system_metrics or not self.app_metrics:
            return {
                'status': 'initializing',
                'message': 'Coletando métricas iniciais...'
            }
        
        latest_system = self.system_metrics[-1]
        latest_app = self.app_metrics[-1]
        
        # Determinar status geral
        critical_alerts = [a for a in self.active_alerts if a['level'] == 'critical']
        warning_alerts = [a for a in self.active_alerts if a['level'] == 'warning']
        
        if critical_alerts:
            overall_status = 'critical'
            status_message = f"{len(critical_alerts)} alerta(s) crítico(s) ativo(s)"
        elif warning_alerts:
            overall_status = 'warning'
            status_message = f"{len(warning_alerts)} alerta(s) de atenção ativo(s)"
        else:
            overall_status = 'healthy'
            status_message = 'Sistema operando normalmente'
        
        return {
            'status': overall_status,
            'message': status_message,
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                'cpu_usage': latest_system.cpu_usage,
                'memory_usage': latest_system.memory_usage,
                'disk_usage': latest_system.disk_usage,
                'active_connections': latest_system.active_connections,
                'response_time': latest_system.response_time
            },
            'application_metrics': {
                'active_users': latest_app.active_users,
                'requests_per_minute': latest_app.requests_per_minute,
                'error_rate': latest_app.error_rate,
                'average_response_time': latest_app.average_response_time,
                'database_connections': latest_app.database_connections,
                'cache_hit_rate': latest_app.cache_hit_rate
            },
            'active_alerts': len(self.active_alerts),
            'uptime': self._get_uptime()
        }
    
    def get_metrics_history(self, minutes: int = 30) -> Dict[str, Any]:
        """Obter histórico de métricas"""
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # Filtrar métricas do período
        system_history = [
            {
                'timestamp': m.timestamp.isoformat(),
                'cpu_usage': m.cpu_usage,
                'memory_usage': m.memory_usage,
                'disk_usage': m.disk_usage,
                'response_time': m.response_time
            }
            for m in self.system_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        app_history = [
            {
                'timestamp': m.timestamp.isoformat(),
                'active_users': m.active_users,
                'requests_per_minute': m.requests_per_minute,
                'error_rate': m.error_rate,
                'average_response_time': m.average_response_time
            }
            for m in self.app_metrics
            if m.timestamp >= cutoff_time
        ]
        
        return {
            'period_minutes': minutes,
            'system_metrics': system_history,
            'application_metrics': app_history,
            'total_samples': len(system_history)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obter resumo de performance"""
        
        if not self.system_metrics or not self.app_metrics:
            return {'error': 'Dados insuficientes'}
        
        # Métricas dos últimos 30 minutos
        cutoff_time = datetime.now() - timedelta(minutes=30)
        recent_system = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
        recent_app = [m for m in self.app_metrics if m.timestamp >= cutoff_time]
        
        if not recent_system or not recent_app:
            return {'error': 'Dados insuficientes para o período'}
        
        # Calcular estatísticas
        system_stats = {
            'cpu_avg': sum(m.cpu_usage for m in recent_system) / len(recent_system),
            'cpu_max': max(m.cpu_usage for m in recent_system),
            'memory_avg': sum(m.memory_usage for m in recent_system) / len(recent_system),
            'memory_max': max(m.memory_usage for m in recent_system),
            'response_time_avg': sum(m.response_time for m in recent_system) / len(recent_system),
            'response_time_max': max(m.response_time for m in recent_system)
        }
        
        app_stats = {
            'users_avg': sum(m.active_users for m in recent_app) / len(recent_app),
            'users_max': max(m.active_users for m in recent_app),
            'rpm_avg': sum(m.requests_per_minute for m in recent_app) / len(recent_app),
            'rpm_max': max(m.requests_per_minute for m in recent_app),
            'error_rate_avg': sum(m.error_rate for m in recent_app) / len(recent_app),
            'error_rate_max': max(m.error_rate for m in recent_app)
        }
        
        return {
            'summary_period': '30 minutos',
            'system_performance': system_stats,
            'application_performance': app_stats,
            'health_score': self._calculate_health_score(system_stats, app_stats),
            'recommendations': self._generate_performance_recommendations(system_stats, app_stats)
        }
    
    def _calculate_health_score(self, system_stats: Dict, app_stats: Dict) -> int:
        """Calcular score de saúde do sistema (0-100)"""
        
        score = 100
        
        # Penalizar por alto uso de recursos
        if system_stats['cpu_avg'] > 70:
            score -= (system_stats['cpu_avg'] - 70) * 0.5
        
        if system_stats['memory_avg'] > 80:
            score -= (system_stats['memory_avg'] - 80) * 0.8
        
        # Penalizar por alta taxa de erro
        if app_stats['error_rate_avg'] > 2:
            score -= app_stats['error_rate_avg'] * 3
        
        # Penalizar por tempo de resposta alto
        if system_stats['response_time_avg'] > 1000:
            score -= (system_stats['response_time_avg'] - 1000) * 0.01
        
        return max(0, min(100, int(score)))
    
    def _generate_performance_recommendations(self, system_stats: Dict, app_stats: Dict) -> List[str]:
        """Gerar recomendações de performance"""
        
        recommendations = []
        
        if system_stats['cpu_avg'] > 70:
            recommendations.append("Considere otimizar processos que consomem CPU ou aumentar recursos")
        
        if system_stats['memory_avg'] > 80:
            recommendations.append("Monitorar uso de memória - possível vazamento ou necessidade de mais RAM")
        
        if app_stats['error_rate_avg'] > 3:
            recommendations.append("Investigar causa de erros frequentes na aplicação")
        
        if system_stats['response_time_avg'] > 2000:
            recommendations.append("Otimizar queries de banco de dados e implementar cache")
        
        if app_stats['rpm_max'] > 1000:
            recommendations.append("Considerar implementar rate limiting para controlar carga")
        
        if not recommendations:
            recommendations.append("Sistema operando dentro dos parâmetros normais")
        
        return recommendations
    
    def _get_uptime(self) -> Dict[str, Any]:
        """Obter tempo de atividade"""
        
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            'boot_time': boot_time.isoformat(),
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': str(uptime).split('.')[0]  # Remove microssegundos
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Exportar métricas em formato específico"""
        
        data = {
            'export_time': datetime.now().isoformat(),
            'current_status': self.get_current_status(),
            'performance_summary': self.get_performance_summary(),
            'active_alerts': self.active_alerts,
            'metrics_history': self.get_metrics_history(60)
        }
        
        if format.lower() == 'json':
            return json.dumps(data, indent=2, default=str)
        else:
            return str(data)

# Instância global do monitor
monitor = PerformanceMonitor()

# Funções para API
def get_system_health() -> Dict:
    """Obter saúde do sistema"""
    try:
        return {'success': True, **monitor.get_current_status()}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_performance_metrics(minutes: int = 30) -> Dict:
    """Obter métricas de performance"""
    try:
        return {'success': True, **monitor.get_metrics_history(minutes)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_performance_summary() -> Dict:
    """Obter resumo de performance"""
    try:
        return {'success': True, **monitor.get_performance_summary()}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def start_monitoring():
    """Iniciar monitoramento"""
    monitor.start_monitoring()

def stop_monitoring():
    """Parar monitoramento"""
    monitor.stop_monitoring()
