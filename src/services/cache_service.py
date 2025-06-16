"""
Serviço de Cache Redis Estratégico para JurisIA
"""
import redis
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from functools import wraps
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        self._connect()
    
    def _connect(self):
        """Conecta ao Redis se disponível"""
        try:
            redis_url = getattr(Config, 'REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            
            # Testa a conexão
            self.redis_client.ping()
            self.enabled = True
            logger.info("✅ Redis conectado e cache habilitado")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis não disponível, cache desabilitado: {e}")
            self.enabled = False
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Gera chave única para cache"""
        return f"jurisia:{prefix}:{identifier}"
    
    def _serialize(self, data: Any) -> bytes:
        """Serializa dados para armazenamento"""
        try:
            # Tenta JSON primeiro (mais rápido)
            return json.dumps(data, default=str).encode('utf-8')
        except (TypeError, ValueError):
            # Usa pickle para objetos complexos
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserializa dados do cache"""
        try:
            # Tenta JSON primeiro
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Usa pickle
            return pickle.loads(data)
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Define valor no cache com TTL"""
        if not self.enabled:
            return False
            
        try:
            serialized = self._serialize(value)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Erro ao definir cache {key}: {e}")
            return False
    
    def get(self, key: str) -> Any:
        """Obtém valor do cache"""
        if not self.enabled:
            return None
            
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Erro ao obter cache {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Remove chave do cache"""
        if not self.enabled:
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Erro ao deletar cache {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Remove chaves por padrão"""
        if not self.enabled:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Erro ao deletar padrão {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Verifica se chave existe"""
        if not self.enabled:
            return False
            
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Erro ao verificar existência {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementa contador"""
        if not self.enabled:
            return None
            
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Erro ao incrementar {key}: {e}")
            return None
    
    def set_hash(self, key: str, mapping: Dict[str, Any], ttl: int = 3600) -> bool:
        """Define hash no cache"""
        if not self.enabled:
            return False
            
        try:
            # Serializa valores do mapping
            serialized_mapping = {
                k: self._serialize(v) for k, v in mapping.items()
            }
            
            pipe = self.redis_client.pipeline()
            pipe.hset(key, mapping=serialized_mapping)
            pipe.expire(key, ttl)
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao definir hash {key}: {e}")
            return False
    
    def get_hash(self, key: str, field: Optional[str] = None) -> Any:
        """Obtém hash do cache"""
        if not self.enabled:
            return None
            
        try:
            if field:
                data = self.redis_client.hget(key, field)
                return self._deserialize(data) if data else None
            else:
                data = self.redis_client.hgetall(key)
                return {
                    k.decode('utf-8'): self._deserialize(v) 
                    for k, v in data.items()
                } if data else {}
        except Exception as e:
            logger.error(f"Erro ao obter hash {key}: {e}")
            return None


# Cache estratégico por funcionalidade
class StrategicCache:
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    # Cache de usuários
    def cache_user(self, user_id: int, user_data: Dict, ttl: int = 1800):
        """Cache dados do usuário por 30min"""
        key = self.cache._make_key("user", str(user_id))
        return self.cache.set(key, user_data, ttl)
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Obtém usuário do cache"""
        key = self.cache._make_key("user", str(user_id))
        return self.cache.get(key)
    
    def invalidate_user(self, user_id: int):
        """Invalida cache do usuário"""
        key = self.cache._make_key("user", str(user_id))
        return self.cache.delete(key)
    
    # Cache de documentos
    def cache_document(self, doc_id: int, doc_data: Dict, ttl: int = 3600):
        """Cache documento por 1h"""
        key = self.cache._make_key("document", str(doc_id))
        return self.cache.set(key, doc_data, ttl)
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Obtém documento do cache"""
        key = self.cache._make_key("document", str(doc_id))
        return self.cache.get(key)
    
    def invalidate_document(self, doc_id: int):
        """Invalida cache do documento"""
        key = self.cache._make_key("document", str(doc_id))
        return self.cache.delete(key)
    
    # Cache de templates
    def cache_template(self, template_id: int, template_data: Dict, ttl: int = 7200):
        """Cache template por 2h"""
        key = self.cache._make_key("template", str(template_id))
        return self.cache.set(key, template_data, ttl)
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Obtém template do cache"""
        key = self.cache._make_key("template", str(template_id))
        return self.cache.get(key)
    
    # Cache de busca
    def cache_search(self, query_hash: str, results: List, ttl: int = 1800):
        """Cache resultados de busca por 30min"""
        key = self.cache._make_key("search", query_hash)
        return self.cache.set(key, results, ttl)
    
    def get_search(self, query_hash: str) -> Optional[List]:
        """Obtém resultados de busca do cache"""
        key = self.cache._make_key("search", query_hash)
        return self.cache.get(key)
    
    # Cache de sessão
    def cache_session(self, session_id: str, session_data: Dict, ttl: int = 3600):
        """Cache dados da sessão por 1h"""
        key = self.cache._make_key("session", session_id)
        return self.cache.set(key, session_data, ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Obtém dados da sessão"""
        key = self.cache._make_key("session", session_id)
        return self.cache.get(key)
    
    # Cache de estatísticas
    def cache_stats(self, stats_type: str, stats_data: Dict, ttl: int = 600):
        """Cache estatísticas por 10min"""
        key = self.cache._make_key("stats", stats_type)
        return self.cache.set(key, stats_data, ttl)
    
    def get_stats(self, stats_type: str) -> Optional[Dict]:
        """Obtém estatísticas do cache"""
        key = self.cache._make_key("stats", stats_type)
        return self.cache.get(key)


# Decorador para cache automático
def cached(prefix: str, ttl: int = 3600, key_func=None):
    """Decorador para cache automático de funções"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave baseada nos argumentos
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Hash dos argumentos
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = hashlib.md5(args_str.encode()).hexdigest()
            
            full_key = cache_service._make_key(prefix, cache_key)
            
            # Tenta obter do cache
            cached_result = cache_service.get(full_key)
            if cached_result is not None:
                return cached_result
            
            # Executa e armazena no cache
            result = func(*args, **kwargs)
            if result is not None:
                cache_service.set(full_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Instâncias globais
cache_service = CacheService()
strategic_cache = StrategicCache(cache_service)

# Funções de conveniência
def cache_get(key: str) -> Any:
    """Função de conveniência para obter do cache"""
    return cache_service.get(key)

def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Função de conveniência para definir no cache"""
    return cache_service.set(key, value, ttl)

def cache_delete(key: str) -> bool:
    """Função de conveniência para deletar do cache"""
    return cache_service.delete(key)

def cache_invalidate_pattern(pattern: str) -> int:
    """Função de conveniência para invalidar por padrão"""
    return cache_service.delete_pattern(pattern) 