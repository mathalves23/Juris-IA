import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from flask import request, g, current_app
from functools import wraps
import time

from src.config import Config

class SecurityMiddleware:
    """Middleware de segurança para aplicação"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.rate_limit_storage = {}  # Em produção, usar Redis
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa middleware com a aplicação Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown)
    
    def before_request(self):
        """Executado antes de cada requisição"""
        g.start_time = time.time()
        
        # Log da requisição
        self.log_request()
        
        # Verificar rate limiting
        if self.is_rate_limited():
            from flask import jsonify
            return jsonify({
                'success': False,
                'error': 'RATE_LIMIT_EXCEEDED',
                'message': 'Muitas requisições. Tente novamente mais tarde.'
            }), 429
        
        # Validar User-Agent
        self.validate_user_agent()
        
        # Detectar possíveis ataques
        self.detect_attacks()
    
    def after_request(self, response):
        """Executado após cada requisição"""
        # Adicionar headers de segurança
        self.add_security_headers(response)
        
        # Log da resposta
        self.log_response(response)
        
        return response
    
    def teardown(self, exception=None):
        """Limpeza após requisição"""
        if exception:
            self.logger.error(f"Erro na requisição: {str(exception)}")
    
    def add_security_headers(self, response):
        """Adiciona headers de segurança à resposta"""
        headers = Config.SECURITY_HEADERS
        
        for header, value in headers.items():
            response.headers[header] = value
        
        return response
    
    def is_rate_limited(self) -> bool:
        """Verifica se a requisição deve ser limitada por rate limiting"""
        try:
            client_id = self.get_client_identifier()
            current_time = datetime.utcnow()
            
            # Limpar entradas antigas
            self.cleanup_rate_limit_storage()
            
            # Verificar histórico de requisições
            if client_id not in self.rate_limit_storage:
                self.rate_limit_storage[client_id] = []
            
            requests_history = self.rate_limit_storage[client_id]
            
            # Filtrar apenas requisições recentes (última hora)
            cutoff_time = current_time - timedelta(seconds=Config.RATE_LIMIT_PERIOD)
            recent_requests = [
                req_time for req_time in requests_history 
                if req_time > cutoff_time
            ]
            
            # Verificar se excedeu o limite
            if len(recent_requests) >= Config.RATE_LIMIT_REQUESTS:
                self.logger.warning(f"Rate limit exceeded for {client_id}")
                return True
            
            # Registrar a requisição atual
            recent_requests.append(current_time)
            self.rate_limit_storage[client_id] = recent_requests
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro no rate limiting: {str(e)}")
            return False  # Em caso de erro, não bloquear
    
    def get_client_identifier(self) -> str:
        """Obtém identificador único do cliente"""
        # Priorizar IP real se disponível
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip:
            ip = ip.split(',')[0].strip()
        
        # Combinar com User-Agent para identificação mais precisa
        user_agent = request.headers.get('User-Agent', '')
        return f"{ip}:{hash(user_agent) % 10000}"
    
    def cleanup_rate_limit_storage(self):
        """Remove entradas antigas do storage de rate limiting"""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(seconds=Config.RATE_LIMIT_PERIOD * 2)
        
        for client_id in list(self.rate_limit_storage.keys()):
            self.rate_limit_storage[client_id] = [
                req_time for req_time in self.rate_limit_storage[client_id]
                if req_time > cutoff_time
            ]
            
            # Remove clientes sem requisições recentes
            if not self.rate_limit_storage[client_id]:
                del self.rate_limit_storage[client_id]
    
    def validate_user_agent(self):
        """Valida User-Agent para detectar bots maliciosos"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        # Lista de User-Agents suspeitos
        suspicious_agents = [
            'scanner', 'crawler', 'bot', 'spider', 'scraper',
            'curl', 'wget', 'python-requests', 'exploit'
        ]
        
        # Verificar se contém strings suspeitas
        for suspicious in suspicious_agents:
            if suspicious in user_agent:
                self.logger.warning(f"Suspicious User-Agent detected: {user_agent}")
                g.suspicious_request = True
                break
    
    def detect_attacks(self):
        """Detecta possíveis ataques na requisição"""
        try:
            # SQL Injection patterns
            sql_patterns = [
                'union', 'select', 'insert', 'delete', 'drop', 'create',
                'alter', 'exec', 'execute', 'script', 'xp_'
            ]
            
            # XSS patterns  
            xss_patterns = [
                '<script', 'javascript:', 'onerror=', 'onload=',
                'alert(', 'eval(', 'document.cookie'
            ]
            
            # Verificar query parameters
            for key, value in request.args.items():
                value_lower = str(value).lower()
                
                # Verificar SQL Injection
                if any(pattern in value_lower for pattern in sql_patterns):
                    self.logger.warning(f"Possible SQL injection attempt: {key}={value}")
                    g.potential_attack = 'sql_injection'
                
                # Verificar XSS
                if any(pattern in value_lower for pattern in xss_patterns):
                    self.logger.warning(f"Possible XSS attempt: {key}={value}")
                    g.potential_attack = 'xss'
                    
        except Exception as e:
            self.logger.error(f"Erro na detecção de ataques: {str(e)}")
    
    def log_request(self):
        """Log detalhado da requisição"""
        try:
            ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')
            
            self.logger.info(
                f"Request: {request.method} {request.path} - "
                f"IP: {ip} - "
                f"User-Agent: {user_agent[:100]}..."
            )
            
        except Exception as e:
            self.logger.error(f"Erro no log da requisição: {str(e)}")
    
    def log_response(self, response):
        """Log da resposta"""
        try:
            duration = time.time() - g.get('start_time', time.time())
            
            self.logger.info(
                f"Response: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
        except Exception as e:
            self.logger.error(f"Erro no log da resposta: {str(e)}")

# Instância global do middleware
security_middleware = SecurityMiddleware() 