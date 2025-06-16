"""
Sistema de Cache Avançado com Redis e Otimizações de Performance
"""
import redis
import json
import hashlib
from typing import Any, Optional, List, Dict, Union
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import asyncio
import pickle
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Configuração do sistema de cache"""
    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hora
    max_memory_cache: int = 1000  # Máximo de itens em memória
    compression_threshold: int = 1024  # Comprimir dados > 1KB
    enable_query_cache: bool = True
    enable_response_cache: bool = True

class AdvancedCacheManager:
    """Gerenciador de cache avançado com múltiplas estratégias"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client = redis.from_url(config.redis_url, decode_responses=False)
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'redis_hits': 0,
            'invalidations': 0
        }
        
    def _generate_key(self, prefix: str, *args: Any) -> str:
        """Gerar chave única para cache"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serializar dados com compressão opcional"""
        serialized = pickle.dumps(data)
        
        if len(serialized) > self.config.compression_threshold:
            import gzip
            serialized = gzip.compress(serialized)
            
        return serialized
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserializar dados com descompressão"""
        try:
            # Tentar descomprimir primeiro
            import gzip
            data = gzip.decompress(data)
        except:
            pass  # Dados não comprimidos
            
        return pickle.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """Buscar item no cache (memória -> Redis)"""
        # Tentar memória primeiro
        if key in self.memory_cache:
            self.cache_stats['hits'] += 1
            self.cache_stats['memory_hits'] += 1
            return self.memory_cache[key]['data']
        
        # Tentar Redis
        try:
            data = self.redis_client.get(key)
            if data:
                deserialized = self._deserialize_data(data)
                
                # Adicionar à memória se há espaço
                if len(self.memory_cache) < self.config.max_memory_cache:
                    self.memory_cache[key] = {
                        'data': deserialized,
                        'timestamp': time.time()
                    }
                
                self.cache_stats['hits'] += 1
                self.cache_stats['redis_hits'] += 1
                return deserialized
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
        
        self.cache_stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Armazenar item no cache"""
        ttl = ttl or self.config.default_ttl
        
        try:
            # Armazenar no Redis
            serialized = self._serialize_data(value)
            self.redis_client.setex(key, ttl, serialized)
            
            # Armazenar na memória se há espaço
            if len(self.memory_cache) < self.config.max_memory_cache:
                self.memory_cache[key] = {
                    'data': value,
                    'timestamp': time.time()
                }
            
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def invalidate(self, pattern: str) -> int:
        """Invalidar cache por padrão"""
        count = 0
        
        # Invalidar memória
        keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.memory_cache[key]
            count += 1
        
        # Invalidar Redis
        try:
            redis_keys = self.redis_client.keys(f"*{pattern}*")
            if redis_keys:
                self.redis_client.delete(*redis_keys)
                count += len(redis_keys)
        except Exception as e:
            logger.error(f"Redis invalidation error: {e}")
        
        self.cache_stats['invalidations'] += count
        return count
    
    def get_stats(self) -> Dict:
        """Obter estatísticas do cache"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'memory_cache_size': len(self.memory_cache),
            'redis_connected': self._redis_health_check(),
            **self.cache_stats
        }
    
    def _redis_health_check(self) -> bool:
        """Verificar saúde do Redis"""
        try:
            self.redis_client.ping()
            return True
        except:
            return False

# Decoradores para cache automático
def cache_result(key_prefix: str, ttl: Optional[int] = None, invalidate_on: Optional[List[str]] = None):
    """Decorator para cache automático de resultados"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = getattr(wrapper, '_cache_manager', None)
            if not cache_manager:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Gerar chave do cache
            cache_key = cache_manager._generate_key(key_prefix, *args, **kwargs)
            
            # Tentar buscar no cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Armazenar resultado
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

class QueryOptimizer:
    """Otimizador de queries SQL"""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 segundo
    
    def track_query(self, statement, parameters, execution_time):
        """Rastrear performance de queries"""
        query_hash = hashlib.md5(str(statement).encode()).hexdigest()[:8]
        
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                'statement': str(statement),
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'slow_queries': 0
            }
        
        stats = self.query_stats[query_hash]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], execution_time)
        
        if execution_time > self.slow_query_threshold:
            stats['slow_queries'] += 1
            logger.warning(f"Slow query detected: {execution_time:.2f}s - {statement}")
    
    def get_slow_queries(self) -> List[Dict]:
        """Obter queries lentas"""
        slow_queries = []
        for query_hash, stats in self.query_stats.items():
            if stats['slow_queries'] > 0:
                slow_queries.append({
                    'hash': query_hash,
                    'avg_time': stats['avg_time'],
                    'slow_count': stats['slow_queries'],
                    'total_count': stats['count'],
                    'statement': stats['statement'][:200] + '...' if len(stats['statement']) > 200 else stats['statement']
                })
        
        return sorted(slow_queries, key=lambda x: x['avg_time'], reverse=True)

# Singleton para gerenciador global
cache_manager = None
query_optimizer = QueryOptimizer()

def init_performance_optimizations(app, config: CacheConfig):
    """Inicializar otimizações de performance"""
    global cache_manager
    cache_manager = AdvancedCacheManager(config)
    
    # Configurar interceptação de queries
    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()
    
    @event.listens_for(Engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        execution_time = time.time() - context._query_start_time
        query_optimizer.track_query(statement, parameters, execution_time)
    
    # Adicionar rotas de monitoramento
    @app.route('/api/performance/cache-stats')
    def get_cache_stats():
        return cache_manager.get_stats()
    
    @app.route('/api/performance/slow-queries')
    def get_slow_queries():
        return {'slow_queries': query_optimizer.get_slow_queries()}
    
    # Middleware de compressão de resposta
    @app.after_request
    def compress_response(response):
        if response.content_length and response.content_length > 1024:
            # Comprimir respostas grandes
            response.headers['Content-Encoding'] = 'gzip'
        return response
    
    return cache_manager

# Utilitários de performance
class PerformanceMonitor:
    """Monitor de performance da aplicação"""
    
    def __init__(self):
        self.metrics = {
            'request_times': [],
            'memory_usage': [],
            'active_connections': 0
        }
    
    def track_request(self, endpoint: str, duration: float):
        """Rastrear tempo de request"""
        self.metrics['request_times'].append({
            'endpoint': endpoint,
            'duration': duration,
            'timestamp': datetime.utcnow()
        })
        
        # Manter apenas últimas 1000 requests
        if len(self.metrics['request_times']) > 1000:
            self.metrics['request_times'] = self.metrics['request_times'][-1000:]
    
    def get_avg_response_time(self, minutes: int = 5) -> float:
        """Obter tempo médio de resposta"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent_requests = [
            req for req in self.metrics['request_times']
            if req['timestamp'] > cutoff
        ]
        
        if not recent_requests:
            return 0.0
        
        return sum(req['duration'] for req in recent_requests) / len(recent_requests)

performance_monitor = PerformanceMonitor()

# Middleware para rastreamento automático
def performance_middleware(app):
    """Middleware para rastreamento de performance"""
    
    @app.before_request
    def before_request():
        from flask import g, request
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        from flask import g, request
        
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            performance_monitor.track_request(request.endpoint or 'unknown', duration)
            
            # Adicionar header de tempo de resposta
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    return app 