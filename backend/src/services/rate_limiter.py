import time
import redis
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from flask import request, g, jsonify
import functools
import hashlib
import json
from dataclasses import dataclass
import structlog

@dataclass
class RateLimitRule:
    """Regra de rate limiting"""
    requests: int  # Número de requests permitidos
    window: int    # Janela de tempo em segundos
    burst: int     # Burst permitido (requests extras em rajada)
    
class RateLimiter:
    """Sistema de rate limiting avançado"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.memory_store = defaultdict(lambda: deque(maxlen=1000))
        self.logger = structlog.get_logger("rate_limiter")
        
        # Regras padrão por endpoint
        self.default_rules = {
            # Autenticação - mais restritivo
            'auth.login': RateLimitRule(requests=5, window=300, burst=2),  # 5 por 5min
            'auth.register': RateLimitRule(requests=3, window=3600, burst=1),  # 3 por hora
            'auth.reset_password': RateLimitRule(requests=3, window=3600, burst=1),
            
            # IA - moderado
            'ai.generate': RateLimitRule(requests=20, window=3600, burst=5),  # 20 por hora
            'ai.review': RateLimitRule(requests=30, window=3600, burst=10),
            'ai.summarize': RateLimitRule(requests=50, window=3600, burst=15),
            
            # Documentos - liberal
            'documents.create': RateLimitRule(requests=100, window=3600, burst=20),
            'documents.update': RateLimitRule(requests=200, window=3600, burst=50),
            'documents.list': RateLimitRule(requests=500, window=3600, burst=100),
            
            # Templates - liberal
            'templates.create': RateLimitRule(requests=50, window=3600, burst=10),
            'templates.list': RateLimitRule(requests=300, window=3600, burst=50),
            
            # Upload - restritivo
            'upload.file': RateLimitRule(requests=20, window=3600, burst=5),
            
            # Geral - padrão
            'default': RateLimitRule(requests=1000, window=3600, burst=200),
        }
        
        # Regras por tipo de usuário
        self.user_type_multipliers = {
            'free': 1.0,
            'premium': 2.0,
            'enterprise': 5.0,
            'admin': 10.0
        }
    
    def _get_client_id(self) -> str:
        """Obter identificador único do cliente"""
        # Prioridade: usuário autenticado > IP + User-Agent
        if hasattr(g, 'current_user') and g.current_user:
            return f"user:{g.current_user.id}"
        
        ip = request.remote_addr or 'unknown'
        user_agent = request.headers.get('User-Agent', 'unknown')
        user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        
        return f"ip:{ip}:ua:{user_agent_hash}"
    
    def _get_endpoint_key(self) -> str:
        """Obter chave do endpoint"""
        endpoint = request.endpoint or 'unknown'
        
        # Mapear endpoints para regras
        for rule_key in self.default_rules.keys():
            if rule_key in endpoint:
                return rule_key
        
        return 'default'
    
    def _get_rule(self, endpoint_key: str) -> RateLimitRule:
        """Obter regra de rate limiting para o endpoint"""
        base_rule = self.default_rules.get(endpoint_key, self.default_rules['default'])
        
        # Aplicar multiplicador baseado no tipo de usuário
        user_type = 'free'
        if hasattr(g, 'current_user') and g.current_user:
            user_type = getattr(g.current_user, 'subscription_type', 'free')
            if getattr(g.current_user, 'is_admin', False):
                user_type = 'admin'
        
        multiplier = self.user_type_multipliers.get(user_type, 1.0)
        
        return RateLimitRule(
            requests=int(base_rule.requests * multiplier),
            window=base_rule.window,
            burst=int(base_rule.burst * multiplier)
        )
    
    def _check_redis_limit(self, key: str, rule: RateLimitRule) -> Tuple[bool, Dict]:
        """Verificar limite usando Redis"""
        try:
            pipe = self.redis_client.pipeline()
            now = time.time()
            window_start = now - rule.window
            
            # Limpar requests antigos
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Contar requests na janela atual
            pipe.zcard(key)
            
            # Adicionar request atual
            pipe.zadd(key, {str(now): now})
            
            # Definir expiração
            pipe.expire(key, rule.window + 60)
            
            results = pipe.execute()
            current_requests = results[1]
            
            # Verificar se excedeu o limite
            allowed = current_requests <= rule.requests
            
            # Calcular tempo para reset
            if current_requests > 0:
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    reset_time = oldest_request[0][1] + rule.window
                else:
                    reset_time = now + rule.window
            else:
                reset_time = now + rule.window
            
            return allowed, {
                'limit': rule.requests,
                'remaining': max(0, rule.requests - current_requests),
                'reset': int(reset_time),
                'retry_after': int(reset_time - now) if not allowed else 0
            }
            
        except Exception as e:
            self.logger.error("redis_rate_limit_error", error=str(e))
            # Fallback para memória em caso de erro no Redis
            return self._check_memory_limit(key, rule)
    
    def _check_memory_limit(self, key: str, rule: RateLimitRule) -> Tuple[bool, Dict]:
        """Verificar limite usando memória local"""
        now = time.time()
        window_start = now - rule.window
        
        # Limpar requests antigos
        requests = self.memory_store[key]
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Adicionar request atual
        requests.append(now)
        
        current_requests = len(requests)
        allowed = current_requests <= rule.requests
        
        # Calcular tempo para reset
        reset_time = (requests[0] + rule.window) if requests else (now + rule.window)
        
        return allowed, {
            'limit': rule.requests,
            'remaining': max(0, rule.requests - current_requests),
            'reset': int(reset_time),
            'retry_after': int(reset_time - now) if not allowed else 0
        }
    
    def check_limit(self, custom_key: Optional[str] = None, custom_rule: Optional[RateLimitRule] = None) -> Tuple[bool, Dict]:
        """Verificar se o request está dentro do limite"""
        client_id = self._get_client_id()
        endpoint_key = self._get_endpoint_key()
        
        # Usar chave customizada se fornecida
        if custom_key:
            key = f"rate_limit:{custom_key}:{client_id}"
        else:
            key = f"rate_limit:{endpoint_key}:{client_id}"
        
        # Usar regra customizada se fornecida
        rule = custom_rule or self._get_rule(endpoint_key)
        
        # Verificar limite
        if self.redis_client:
            try:
                return self._check_redis_limit(key, rule)
            except:
                return self._check_memory_limit(key, rule)
        else:
            return self._check_memory_limit(key, rule)
    
    def is_blocked(self, ip_address: str) -> bool:
        """Verificar se um IP está bloqueado"""
        if not self.redis_client:
            return False
        
        try:
            blocked_key = f"blocked_ip:{ip_address}"
            return self.redis_client.exists(blocked_key)
        except:
            return False
    
    def block_ip(self, ip_address: str, duration: int = 3600):
        """Bloquear um IP por um período"""
        if not self.redis_client:
            return
        
        try:
            blocked_key = f"blocked_ip:{ip_address}"
            self.redis_client.setex(blocked_key, duration, "blocked")
            
            self.logger.warning(
                "ip_blocked",
                ip_address=ip_address,
                duration=duration,
                reason="rate_limit_exceeded"
            )
        except Exception as e:
            self.logger.error("block_ip_error", error=str(e), ip=ip_address)
    
    def get_stats(self, client_id: Optional[str] = None) -> Dict:
        """Obter estatísticas de rate limiting"""
        if not client_id:
            client_id = self._get_client_id()
        
        stats = {
            'client_id': client_id,
            'endpoints': {},
            'total_requests': 0
        }
        
        if not self.redis_client:
            return stats
        
        try:
            # Buscar todas as chaves relacionadas ao cliente
            pattern = f"rate_limit:*:{client_id}"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                endpoint = key_str.split(':')[1]
                
                # Contar requests na janela atual
                count = self.redis_client.zcard(key)
                stats['endpoints'][endpoint] = count
                stats['total_requests'] += count
            
        except Exception as e:
            self.logger.error("get_stats_error", error=str(e))
        
        return stats

# Instância global do rate limiter
rate_limiter = RateLimiter()

def init_rate_limiter(redis_client: Optional[redis.Redis] = None):
    """Inicializar rate limiter com cliente Redis"""
    global rate_limiter
    rate_limiter = RateLimiter(redis_client)

def rate_limit(custom_key: Optional[str] = None, 
               requests: Optional[int] = None,
               window: Optional[int] = None,
               burst: Optional[int] = None):
    """Decorator para aplicar rate limiting"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Criar regra customizada se parâmetros fornecidos
            custom_rule = None
            if requests is not None and window is not None:
                custom_rule = RateLimitRule(
                    requests=requests,
                    window=window,
                    burst=burst or requests // 5
                )
            
            # Verificar limite
            allowed, info = rate_limiter.check_limit(custom_key, custom_rule)
            
            if not allowed:
                # Log da violação
                rate_limiter.logger.warning(
                    "rate_limit_exceeded",
                    client_id=rate_limiter._get_client_id(),
                    endpoint=request.endpoint,
                    limit=info['limit'],
                    retry_after=info['retry_after']
                )
                
                # Bloquear IP se muitas violações
                ip = request.remote_addr
                if ip:
                    violation_key = f"violations:{ip}"
                    if rate_limiter.redis_client:
                        try:
                            violations = rate_limiter.redis_client.incr(violation_key)
                            rate_limiter.redis_client.expire(violation_key, 3600)  # 1 hora
                            
                            if violations >= 10:  # 10 violações em 1 hora
                                rate_limiter.block_ip(ip, 3600)  # Bloquear por 1 hora
                        except:
                            pass
                
                # Retornar erro 429
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Try again in {info["retry_after"]} seconds.',
                    'limit': info['limit'],
                    'remaining': info['remaining'],
                    'reset': info['reset'],
                    'retry_after': info['retry_after']
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
                response.headers['Retry-After'] = str(info['retry_after'])
                
                return response
            
            # Adicionar headers de rate limit na resposta
            response = f(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
            
            return response
        
        return wrapper
    return decorator

def check_blocked_ip():
    """Middleware para verificar IPs bloqueados"""
    ip = request.remote_addr
    if ip and rate_limiter.is_blocked(ip):
        rate_limiter.logger.warning("blocked_ip_access_attempt", ip=ip)
        
        response = jsonify({
            'error': 'Access denied',
            'message': 'Your IP address has been temporarily blocked due to suspicious activity.'
        })
        response.status_code = 403
        return response

def init_rate_limiting_middleware(app):
    """Inicializar middleware de rate limiting"""
    
    @app.before_request
    def before_request():
        # Verificar IPs bloqueados
        blocked_response = check_blocked_ip()
        if blocked_response:
            return blocked_response
    
    @app.route('/api/rate-limit/stats')
    def get_rate_limit_stats():
        """Obter estatísticas de rate limiting (apenas para admins)"""
        if not (hasattr(g, 'current_user') and g.current_user and g.current_user.is_admin):
            return jsonify({'error': 'Access denied'}), 403
        
        client_id = request.args.get('client_id')
        stats = rate_limiter.get_stats(client_id)
        
        return jsonify(stats)
    
    return app 