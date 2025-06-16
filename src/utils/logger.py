import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from functools import wraps
import time
import traceback
from flask import request, g, current_app

class CustomFormatter(logging.Formatter):
    """Formatter personalizado com cores para terminal"""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging(app):
    """Configurar sistema de logging"""
    
    # Criar diretório de logs se não existir
    log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/jurisia.log'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar nível de logging
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    app.logger.setLevel(log_level)
    
    # Remover handlers existentes
    app.logger.handlers.clear()
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        app.config.get('LOG_FILE', 'logs/jurisia.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s:%(lineno)d: %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    app.logger.addHandler(file_handler)
    
    # Handler para console em desenvolvimento
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(CustomFormatter())
        app.logger.addHandler(console_handler)
    
    # Handler específico para erros críticos
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    app.logger.addHandler(error_handler)
    
    # Configurar outros loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if app.config.get('SQL_DEBUG') else logging.WARNING
    )

def log_request():
    """Log de requisições HTTP"""
    g.start_time = time.time()

def log_response(response):
    """Log de respostas HTTP"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        
        # Log detalhado para requisições lentas
        if duration > 1.0:  # > 1 segundo
            current_app.logger.warning(
                f"SLOW REQUEST: {request.method} {request.path} - "
                f"{response.status_code} - {duration:.2f}s - "
                f"IP: {request.remote_addr} - UA: {request.user_agent}"
            )
        else:
            current_app.logger.info(
                f"{request.method} {request.path} - "
                f"{response.status_code} - {duration:.3f}s"
            )
    
    return response

def log_api_call(func):
    """Decorator para log de chamadas de API"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import current_app
        
        start_time = time.time()
        function_name = f"{func.__module__}.{func.__name__}"
        
        current_app.logger.info(f"API_CALL_START: {function_name}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            current_app.logger.info(
                f"API_CALL_SUCCESS: {function_name} - {duration:.3f}s"
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            current_app.logger.error(
                f"API_CALL_ERROR: {function_name} - {duration:.3f}s - "
                f"Error: {str(e)}\n{traceback.format_exc()}"
            )
            raise
    
    return wrapper

def log_database_operation(operation, table, record_id=None, details=None):
    """Log operações no banco de dados"""
    from flask import current_app
    
    log_message = f"DB_OPERATION: {operation} on {table}"
    if record_id:
        log_message += f" (ID: {record_id})"
    if details:
        log_message += f" - {details}"
    
    current_app.logger.info(log_message)

def log_ai_operation(operation, model, tokens_used=None, duration=None, success=True):
    """Log operações com IA"""
    from flask import current_app
    
    status = "SUCCESS" if success else "ERROR"
    log_message = f"AI_OPERATION_{status}: {operation} with {model}"
    
    if tokens_used:
        log_message += f" - Tokens: {tokens_used}"
    if duration:
        log_message += f" - Duration: {duration:.2f}s"
    
    current_app.logger.info(log_message)

def log_security_event(event_type, details, severity="WARNING"):
    """Log eventos de segurança"""
    from flask import current_app
    
    log_level = getattr(logging, severity.upper())
    current_app.logger.log(
        log_level,
        f"SECURITY_EVENT: {event_type} - {details} - "
        f"IP: {request.remote_addr if request else 'Unknown'}"
    )

def log_error(message):
    """Log de erro"""
    try:
        current_app.logger.error(message)
    except:
        print(f"ERROR: {message}")

class MetricsCollector:
    """Coletor de métricas da aplicação"""
    
    def __init__(self):
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'slow_requests': 0,
            'db_operations': 0,
            'ai_operations': 0,
            'users_active': set(),
            'documents_created': 0,
            'templates_used': 0
        }
    
    def increment(self, metric, value=1):
        """Incrementar métrica"""
        if metric in self.metrics:
            if isinstance(self.metrics[metric], set):
                self.metrics[metric].add(value)
            else:
                self.metrics[metric] += value
    
    def get_metrics(self):
        """Obter métricas atuais"""
        metrics_copy = self.metrics.copy()
        # Converter set para count
        if 'users_active' in metrics_copy:
            metrics_copy['users_active'] = len(metrics_copy['users_active'])
        return metrics_copy
    
    def reset_daily_metrics(self):
        """Reset métricas diárias"""
        self.metrics['requests'] = 0
        self.metrics['errors'] = 0
        self.metrics['slow_requests'] = 0
        self.metrics['users_active'] = set()

# Instância global do coletor de métricas
metrics_collector = MetricsCollector() 