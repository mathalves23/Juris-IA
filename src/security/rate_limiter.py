import time
import redis
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, Optional, Tuple
import hashlib
import json

class RateLimiter:
    """Sistema de Rate Limiting avançado com Redis"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or self._get_redis_client()
        self.default_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 tentativas por 5 min
            'register': {'requests': 3, 'window': 3600},  # 3 registros por hora
            'api': {'requests': 100, 'window': 3600},  # 100 requests por hora
            'upload': {'requests': 10, 'window': 3600},  # 10 uploads por hora
            'ai': {'requests': 20, 'window': 3600}  # 20 requests IA por hora
        }
    
    def _get_redis_client(self):
        """Conectar ao Redis ou usar fallback em memória"""
        try:
            import redis
            return redis.Redis(
                host=current_app.config.get('REDIS_HOST', 'localhost'),
                port=current_app.config.get('REDIS_PORT', 6379),
                db=current_app.config.get('REDIS_DB', 0),
                decode_responses=True
            )
        except:
            # Fallback para armazenamento em memória
            return InMemoryStore()
    
    def _get_client_id(self, request) -> str:
        """Obter identificador único do cliente"""
        # Tentar obter user_id do JWT
        try:
            from flask_jwt_extended import get_jwt_identity, jwt_required
            user_id = get_jwt_identity()
            if user_id:
                return f"user:{user_id}"
        except:
            pass
        
        # Usar IP como fallback
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        return f"ip:{ip}"
    
    def is_allowed(self, key: str, limit_type: str = 'api') -> Tuple[bool, Dict]:
        """Verificar se request é permitido"""
        limits = self.default_limits.get(limit_type, self.default_limits['api'])
        
        current_time = int(time.time())
        window_start = current_time - limits['window']
        
        # Chave Redis
        redis_key = f"rate_limit:{limit_type}:{key}"
        
        try:
            # Obter requests atuais
            current_requests = self.redis_client.zcount(redis_key, window_start, current_time)
            
            if current_requests >= limits['requests']:
                # Obter tempo de reset
                oldest_request = self.redis_client.zrange(redis_key, 0, 0, withscores=True)
                reset_time = int(oldest_request[0][1]) + limits['window'] if oldest_request else current_time + limits['window']
                
                return False, {
                    'allowed': False,
                    'limit': limits['requests'],
                    'remaining': 0,
                    'reset_time': reset_time,
                    'retry_after': reset_time - current_time
                }
            
            # Adicionar request atual
            self.redis_client.zadd(redis_key, {str(current_time): current_time})
            
            # Limpar requests antigos
            self.redis_client.zremrangebyscore(redis_key, 0, window_start)
            
            # Definir TTL
            self.redis_client.expire(redis_key, limits['window'])
            
            remaining = limits['requests'] - current_requests - 1
            
            return True, {
                'allowed': True,
                'limit': limits['requests'],
                'remaining': remaining,
                'reset_time': current_time + limits['window']
            }
            
        except Exception as e:
            # Em caso de erro, permitir request
            current_app.logger.error(f"Rate limiter error: {e}")
            return True, {'allowed': True, 'error': str(e)}
    
    def decorator(self, limit_type: str = 'api'):
        """Decorator para aplicar rate limiting"""
        def decorator_wrapper(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                client_id = self._get_client_id(request)
                allowed, info = self.is_allowed(client_id, limit_type)
                
                if not allowed:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Muitas tentativas. Tente novamente em {info["retry_after"]} segundos.',
                        'retry_after': info['retry_after']
                    }), 429
                
                # Adicionar headers de rate limiting
                response = func(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = info['limit']
                    response.headers['X-RateLimit-Remaining'] = info['remaining']
                    response.headers['X-RateLimit-Reset'] = info.get('reset_time', '')
                
                return response
            return wrapper
        return decorator_wrapper

class InMemoryStore:
    """Fallback para armazenamento em memória"""
    
    def __init__(self):
        self.data = {}
    
    def zadd(self, key, mapping):
        if key not in self.data:
            self.data[key] = []
        for value, score in mapping.items():
            self.data[key].append((value, score))
    
    def zcount(self, key, min_score, max_score):
        if key not in self.data:
            return 0
        return len([x for x in self.data[key] if min_score <= x[1] <= max_score])
    
    def zrange(self, key, start, end, withscores=False):
        if key not in self.data:
            return []
        result = sorted(self.data[key], key=lambda x: x[1])[start:end+1]
        return result if withscores else [x[0] for x in result]
    
    def zremrangebyscore(self, key, min_score, max_score):
        if key in self.data:
            self.data[key] = [x for x in self.data[key] if not (min_score <= x[1] <= max_score)]
    
    def expire(self, key, seconds):
        pass  # Não implementado no fallback

# Instância global
rate_limiter = RateLimiter()

# Decorators prontos para uso
def rate_limit_login(func):
    return rate_limiter.decorator('login')(func)

def rate_limit_register(func):
    return rate_limiter.decorator('register')(func)

def rate_limit_api(func):
    return rate_limiter.decorator('api')(func)

def rate_limit_upload(func):
    return rate_limiter.decorator('upload')(func)

def rate_limit_ai(func):
    return rate_limiter.decorator('ai')(func) 