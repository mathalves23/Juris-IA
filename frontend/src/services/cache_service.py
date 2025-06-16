import json
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import logging
from functools import wraps
import pickle
import os

logger = logging.getLogger(__name__)


class CacheService:
    """Serviço de cache em memória e arquivo."""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.memory_cache: Dict[str, Dict] = {}
        
        # Criar diretório de cache
        os.makedirs(cache_dir, exist_ok=True)
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Gerar chave única para cache."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_expired(self, cached_item: Dict) -> bool:
        """Verificar se item do cache expirou."""
        if 'expires_at' not in cached_item:
            return True
        return datetime.now() > cached_item['expires_at']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Armazenar item no cache."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        cached_item = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'ttl': ttl
        }
        
        # Cache em memória
        self.memory_cache[key] = cached_item
        
        # Cache em arquivo para persistência
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_item, f)
        except Exception as e:
            logger.warning(f"Erro ao salvar cache em arquivo: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Recuperar item do cache."""
        # Tentar cache em memória primeiro
        if key in self.memory_cache:
            cached_item = self.memory_cache[key]
            if not self._is_expired(cached_item):
                return cached_item['value']
            else:
                del self.memory_cache[key]
        
        # Tentar cache em arquivo
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    cached_item = pickle.load(f)
                
                if not self._is_expired(cached_item):
                    # Restaurar para memória
                    self.memory_cache[key] = cached_item
                    return cached_item['value']
                else:
                    os.remove(cache_file)
        except Exception as e:
            logger.warning(f"Erro ao ler cache de arquivo: {e}")
        
        return None
    
    def delete(self, key: str) -> None:
        """Remover item do cache."""
        # Remover da memória
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remover arquivo
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except Exception as e:
            logger.warning(f"Erro ao remover cache de arquivo: {e}")
    
    def clear(self) -> None:
        """Limpar todo o cache."""
        # Limpar memória
        self.memory_cache.clear()
        
        # Limpar arquivos
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception as e:
            logger.warning(f"Erro ao limpar cache de arquivos: {e}")
    
    def cleanup_expired(self) -> int:
        """Limpar itens expirados do cache."""
        expired_count = 0
        
        # Limpar memória
        expired_keys = []
        for key, cached_item in self.memory_cache.items():
            if self._is_expired(cached_item):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
            expired_count += 1
        
        # Limpar arquivos
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        with open(cache_file, 'rb') as f:
                            cached_item = pickle.load(f)
                        
                        if self._is_expired(cached_item):
                            os.remove(cache_file)
                            expired_count += 1
                    except Exception:
                        # Arquivo corrompido, remover
                        os.remove(cache_file)
                        expired_count += 1
        except Exception as e:
            logger.warning(f"Erro na limpeza de arquivos: {e}")
        
        return expired_count
    
    def get_stats(self) -> Dict:
        """Obter estatísticas do cache."""
        memory_items = len(self.memory_cache)
        file_items = 0
        
        try:
            file_items = len([f for f in os.listdir(self.cache_dir) if f.endswith('.cache')])
        except Exception:
            pass
        
        return {
            'memory_items': memory_items,
            'file_items': file_items,
            'total_items': memory_items + file_items,
            'cache_dir': self.cache_dir
        }


# Instância global do cache
cache = CacheService()


def cached(prefix: str = "default", ttl: Optional[int] = None):
    """Decorator para cache de funções."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave do cache
            cache_key = cache._generate_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # Tentar recuperar do cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {func.__name__}")
                return cached_result
            
            # Executar função e cachear resultado
            logger.debug(f"Cache miss para {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class TemplateCache:
    """Cache específico para templates."""
    
    @staticmethod
    @cached("templates", ttl=1800)  # 30 minutos
    def get_public_templates():
        """Cache de templates públicos."""
        from src.models.template import Template
        return Template.query.filter_by(publico=True).all()
    
    @staticmethod
    @cached("templates", ttl=900)  # 15 minutos
    def get_user_templates(user_id: int):
        """Cache de templates do usuário."""
        from src.models.template import Template
        return Template.query.filter_by(usuario_id=user_id).all()
    
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Invalidar cache de templates do usuário."""
        cache_key = cache._generate_key("templates:get_user_templates", user_id)
        cache.delete(cache_key)
    
    @staticmethod
    def invalidate_public_cache():
        """Invalidar cache de templates públicos."""
        cache_key = cache._generate_key("templates:get_public_templates")
        cache.delete(cache_key)


class DocumentCache:
    """Cache específico para documentos."""
    
    @staticmethod
    @cached("documents", ttl=600)  # 10 minutos
    def get_user_documents(user_id: int, page: int = 1, per_page: int = 10):
        """Cache de documentos do usuário."""
        from src.models.document import Document
        return Document.query.filter_by(usuario_id=user_id)\
                           .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Invalidar cache de documentos do usuário."""
        # Invalidar todas as páginas (simplificado)
        for page in range(1, 11):  # Até 10 páginas
            cache_key = cache._generate_key("documents:get_user_documents", user_id, page, 10)
            cache.delete(cache_key)


class AICache:
    """Cache específico para IA."""
    
    @staticmethod
    @cached("ai", ttl=7200)  # 2 horas
    def get_ai_response(prompt_hash: str, model: str):
        """Cache de respostas da IA."""
        # Este método seria usado internamente pelo serviço de IA
        pass
    
    @staticmethod
    def cache_ai_response(prompt: str, model: str, response: str):
        """Cachear resposta da IA."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_key = cache._generate_key("ai:get_ai_response", prompt_hash, model)
        cache.set(cache_key, response, ttl=7200)
    
    @staticmethod
    def get_cached_ai_response(prompt: str, model: str) -> Optional[str]:
        """Recuperar resposta cacheada da IA."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_key = cache._generate_key("ai:get_ai_response", prompt_hash, model)
        return cache.get(cache_key)


# Função para limpeza automática do cache
def setup_cache_cleanup():
    """Configurar limpeza automática do cache."""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            try:
                expired_count = cache.cleanup_expired()
                if expired_count > 0:
                    logger.info(f"Removidos {expired_count} itens expirados do cache")
                time.sleep(3600)  # Executar a cada hora
            except Exception as e:
                logger.error(f"Erro na limpeza do cache: {e}")
                time.sleep(3600)
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("Sistema de limpeza automática do cache iniciado") 