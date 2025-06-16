import redis
import json
import pickle
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import hashlib
from flask import current_app
import threading
import time

class CacheStrategy:
    """Estratégias de cache"""
    REDIS = "redis"
    MEMORY = "memory"
    HYBRID = "hybrid"

class CacheService:
    """Serviço de cache avançado"""
    
    def __init__(self, strategy: str = CacheStrategy.HYBRID):
        self.strategy = strategy
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        self.lock = threading.RLock()
        self._setup_cache()
    
    def _setup_cache(self):
        """Configurar sistema de cache"""
        if self.strategy in [CacheStrategy.REDIS, CacheStrategy.HYBRID]:
            try:
                self.redis_client = redis.Redis(
                    host=current_app.config.get('REDIS_HOST', 'localhost') if current_app else 'localhost',
                    port=current_app.config.get('REDIS_PORT', 6379) if current_app else 6379,
                    db=current_app.config.get('REDIS_CACHE_DB', 1) if current_app else 1,
                    decode_responses=False  # Para suportar pickle
                )
                # Testar conexão
                self.redis_client.ping()
                if current_app:
                    current_app.logger.info("Cache Redis configurado com sucesso")
            except Exception as e:
                if current_app:
                    current_app.logger.warning(f"Redis não disponível, usando cache em memória: {e}")
                self.strategy = CacheStrategy.MEMORY
    
    def get(self, key: str) -> Optional[Any]:
        """Obter valor do cache"""
        with self.lock:
            try:
                # Tentar Redis primeiro
                if self.strategy in [CacheStrategy.REDIS, CacheStrategy.HYBRID] and self.redis_client:
                    try:
                        cached_data = self.redis_client.get(key)
                        if cached_data:
                            self.cache_stats['hits'] += 1
                            return pickle.loads(cached_data)
                    except Exception as e:
                        if current_app:
                            current_app.logger.error(f"Erro ao ler do Redis: {e}")
                
                # Fallback para memória
                if key in self.memory_cache:
                    cache_entry = self.memory_cache[key]
                    if cache_entry['expires_at'] > datetime.utcnow():
                        self.cache_stats['hits'] += 1
                        return cache_entry['value']
                    else:
                        # Expirado, remover
                        del self.memory_cache[key]
                
                self.cache_stats['misses'] += 1
                return None
                
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"Erro no cache get: {e}")
                self.cache_stats['misses'] += 1
                return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Definir valor no cache"""
        with self.lock:
            try:
                success = False
                
                # Tentar Redis primeiro
                if self.strategy in [CacheStrategy.REDIS, CacheStrategy.HYBRID] and self.redis_client:
                    try:
                        serialized_value = pickle.dumps(value)
                        self.redis_client.setex(key, ttl, serialized_value)
                        success = True
                    except Exception as e:
                        if current_app:
                            current_app.logger.error(f"Erro ao escrever no Redis: {e}")
                
                # Sempre salvar em memória como backup
                if self.strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID] or not success:
                    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                    self.memory_cache[key] = {
                        'value': value,
                        'expires_at': expires_at
                    }
                    success = True
                
                if success:
                    self.cache_stats['sets'] += 1
                
                return success
                
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"Erro no cache set: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Remover valor do cache"""
        with self.lock:
            try:
                success = False
                
                # Remover do Redis
                if self.strategy in [CacheStrategy.REDIS, CacheStrategy.HYBRID] and self.redis_client:
                    try:
                        self.redis_client.delete(key)
                        success = True
                    except Exception as e:
                        if current_app:
                            current_app.logger.error(f"Erro ao deletar do Redis: {e}")
                
                # Remover da memória
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    success = True
                
                if success:
                    self.cache_stats['deletes'] += 1
                
                return success
                
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"Erro no cache delete: {e}")
                return False
    
    def clear(self, pattern: str = None) -> bool:
        """Limpar cache"""
        with self.lock:
            try:
                # Limpar Redis
                if self.strategy in [CacheStrategy.REDIS, CacheStrategy.HYBRID] and self.redis_client:
                    if pattern:
                        keys = self.redis_client.keys(pattern)
                        if keys:
                            self.redis_client.delete(*keys)
                    else:
                        self.redis_client.flushdb()
                
                # Limpar memória
                if pattern:
                    import fnmatch
                    keys_to_delete = [key for key in self.memory_cache.keys() 
                                    if fnmatch.fnmatch(key, pattern)]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                else:
                    self.memory_cache.clear()
                
                return True
                
            except Exception as e:
                if current_app:
                    current_app.logger.error(f"Erro ao limpar cache: {e}")
                return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'strategy': self.strategy,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'deletes': self.cache_stats['deletes'],
            'hit_rate': round(hit_rate, 2),
            'memory_keys': len(self.memory_cache)
        }
        
        # Estatísticas do Redis se disponível
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats['redis_memory'] = redis_info.get('used_memory_human', 'N/A')
                stats['redis_keys'] = self.redis_client.dbsize()
            except:
                pass
        
        return stats
    
    def cleanup_expired(self):
        """Limpar entradas expiradas da memória"""
        with self.lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if entry['expires_at'] <= now
            ]
            for key in expired_keys:
                del self.memory_cache[key]
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Gerar chave de cache"""
        # Criar string única baseada nos argumentos
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = ":".join(key_parts)
        
        # Hash para evitar chaves muito longas
        if len(key_string) > 100:
            hash_obj = hashlib.md5(key_string.encode())
            return f"{prefix}:{hash_obj.hexdigest()}"
        
        return key_string
    
    def cached(self, ttl: int = 3600, key_prefix: str = None):
        """Decorator para cache de funções"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Gerar chave de cache
                prefix = key_prefix or f"func:{func.__name__}"
                cache_key = self.cache_key(prefix, *args, **kwargs)
                
                # Tentar obter do cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Executar função e cachear resultado
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

class QueryCache:
    """Cache específico para queries de banco"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def cache_query(self, query_hash: str, result: Any, ttl: int = 600):
        """Cache resultado de query"""
        key = f"query:{query_hash}"
        return self.cache.set(key, result, ttl)
    
    def get_cached_query(self, query_hash: str) -> Optional[Any]:
        """Obter resultado cached de query"""
        key = f"query:{query_hash}"
        return self.cache.get(key)
    
    def invalidate_query_pattern(self, pattern: str):
        """Invalidar queries por padrão"""
        return self.cache.clear(f"query:*{pattern}*")

class SessionCache:
    """Cache para dados de sessão"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def set_user_session(self, user_id: int, session_data: Dict[str, Any], ttl: int = 7200):
        """Cachear dados de sessão do usuário"""
        key = f"session:user:{user_id}"
        return self.cache.set(key, session_data, ttl)
    
    def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obter dados de sessão do usuário"""
        key = f"session:user:{user_id}"
        return self.cache.get(key)
    
    def invalidate_user_session(self, user_id: int):
        """Invalidar sessão do usuário"""
        key = f"session:user:{user_id}"
        return self.cache.delete(key)

class TemplateCache:
    """Cache para templates compilados"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def cache_template(self, template_id: int, compiled_template: Any, ttl: int = 3600):
        """Cache template compilado"""
        key = f"template:compiled:{template_id}"
        return self.cache.set(key, compiled_template, ttl)
    
    def get_cached_template(self, template_id: int) -> Optional[Any]:
        """Obter template compilado do cache"""
        key = f"template:compiled:{template_id}"
        return self.cache.get(key)
    
    def invalidate_template(self, template_id: int):
        """Invalidar cache do template"""
        key = f"template:compiled:{template_id}"
        return self.cache.delete(key)

# Instâncias globais
cache_service = CacheService()
query_cache = QueryCache(cache_service)
session_cache = SessionCache(cache_service)
template_cache = TemplateCache(cache_service)

# Decorator para fácil uso
def cached(ttl: int = 3600, key_prefix: str = None):
    """Decorator de cache simplificado"""
    return cache_service.cached(ttl=ttl, key_prefix=key_prefix)

# Função para limpeza automática
def setup_cache_cleanup():
    """Configurar limpeza automática do cache"""
    def cleanup_thread():
        while True:
            time.sleep(300)  # 5 minutos
            cache_service.cleanup_expired()
    
    thread = threading.Thread(target=cleanup_thread, daemon=True)
    thread.start() 