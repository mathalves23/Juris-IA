"""
Serviço de Cloud Storage com suporte para AWS S3 e Google Cloud Storage
Inclui compressão automática, CDN e otimização de imagens
"""
import os
import io
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
import logging

# Dependências opcionais
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from google.cloud import storage as gcs
    from google.auth.exceptions import DefaultCredentialsError
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    IMAGE_OPTIMIZATION_AVAILABLE = True
except ImportError:
    IMAGE_OPTIMIZATION_AVAILABLE = False

try:
    import zlib
    import gzip
    COMPRESSION_AVAILABLE = True
except ImportError:
    COMPRESSION_AVAILABLE = False

from src.config import Config

logger = logging.getLogger(__name__)

class CloudStorageProvider:
    """Interface base para provedores de cloud storage"""
    
    def upload_file(self, file_data: bytes, file_path: str, content_type: str = None) -> str:
        """Upload de arquivo - retorna URL pública"""
        raise NotImplementedError
    
    def download_file(self, file_path: str) -> bytes:
        """Download de arquivo"""
        raise NotImplementedError
    
    def delete_file(self, file_path: str) -> bool:
        """Delete arquivo"""
        raise NotImplementedError
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Gera URL com expiração"""
        raise NotImplementedError
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """Lista arquivos com metadados"""
        raise NotImplementedError

class AWSS3Provider(CloudStorageProvider):
    """Provedor AWS S3"""
    
    def __init__(self):
        if not AWS_AVAILABLE:
            raise ImportError("boto3 não está instalado")
        
        self.bucket_name = getattr(Config, 'AWS_S3_BUCKET', None)
        self.region = getattr(Config, 'AWS_REGION', 'us-east-1')
        self.cdn_domain = getattr(Config, 'AWS_CLOUDFRONT_DOMAIN', None)
        
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET não configurado")
        
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=getattr(Config, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(Config, 'AWS_SECRET_ACCESS_KEY', None)
            )
            # Testa conexão
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✅ AWS S3 conectado - Bucket: {self.bucket_name}")
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"Erro ao conectar AWS S3: {e}")
            raise
    
    def upload_file(self, file_data: bytes, file_path: str, content_type: str = None) -> str:
        """Upload para S3"""
        try:
            # Detecta content type se não fornecido
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or 'application/octet-stream'
            
            # Configurações do upload
            extra_args = {
                'ContentType': content_type,
                'ACL': 'public-read',  # ou 'private' se preferir
                'CacheControl': 'max-age=31536000',  # 1 ano
                'Metadata': {
                    'uploaded_at': datetime.now().isoformat(),
                    'original_size': str(len(file_data))
                }
            }
            
            # Upload
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=file_data,
                **extra_args
            )
            
            # Retorna URL
            if self.cdn_domain:
                return f"https://{self.cdn_domain}/{file_path}"
            else:
                return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_path}"
            
        except ClientError as e:
            logger.error(f"Erro no upload S3: {e}")
            raise
    
    def download_file(self, file_path: str) -> bytes:
        """Download do S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_path)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Erro no download S3: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """Delete do S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            logger.error(f"Erro ao deletar S3: {e}")
            return False
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """URL com expiração (signed URL)"""
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path},
                ExpiresIn=expires_in
            )
        except ClientError as e:
            logger.error(f"Erro ao gerar URL S3: {e}")
            raise
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """Lista arquivos do S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'path': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"Erro ao listar S3: {e}")
            return []

class GCPStorageProvider(CloudStorageProvider):
    """Provedor Google Cloud Storage"""
    
    def __init__(self):
        if not GCP_AVAILABLE:
            raise ImportError("google-cloud-storage não está instalado")
        
        self.bucket_name = getattr(Config, 'GCP_STORAGE_BUCKET', None)
        self.cdn_domain = getattr(Config, 'GCP_CDN_DOMAIN', None)
        
        if not self.bucket_name:
            raise ValueError("GCP_STORAGE_BUCKET não configurado")
        
        try:
            self.client = gcs.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            # Testa acesso
            self.bucket.reload()
            logger.info(f"✅ Google Cloud Storage conectado - Bucket: {self.bucket_name}")
            
        except DefaultCredentialsError as e:
            logger.error(f"Erro de credenciais GCP: {e}")
            raise
    
    def upload_file(self, file_data: bytes, file_path: str, content_type: str = None) -> str:
        """Upload para GCS"""
        try:
            blob = self.bucket.blob(file_path)
            
            # Detecta content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                content_type = content_type or 'application/octet-stream'
            
            # Upload com metadados
            blob.upload_from_string(
                file_data,
                content_type=content_type
            )
            
            # Define cache e metadados
            blob.cache_control = 'max-age=31536000'
            blob.metadata = {
                'uploaded_at': datetime.now().isoformat(),
                'original_size': str(len(file_data))
            }
            blob.patch()
            
            # Torna público se necessário
            blob.make_public()
            
            # Retorna URL
            if self.cdn_domain:
                return f"https://{self.cdn_domain}/{file_path}"
            else:
                return blob.public_url
            
        except Exception as e:
            logger.error(f"Erro no upload GCS: {e}")
            raise
    
    def download_file(self, file_path: str) -> bytes:
        """Download do GCS"""
        try:
            blob = self.bucket.blob(file_path)
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"Erro no download GCS: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """Delete do GCS"""
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar GCS: {e}")
            return False
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """URL com expiração"""
        try:
            blob = self.bucket.blob(file_path)
            return blob.generate_signed_url(
                expiration=datetime.now() + timedelta(seconds=expires_in),
                method='GET'
            )
        except Exception as e:
            logger.error(f"Erro ao gerar URL GCS: {e}")
            raise
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """Lista arquivos do GCS"""
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            files = []
            
            for blob in blobs:
                files.append({
                    'path': blob.name,
                    'size': blob.size,
                    'last_modified': blob.time_created,
                    'etag': blob.etag
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Erro ao listar GCS: {e}")
            return []

class LocalStorageProvider(CloudStorageProvider):
    """Provedor local para desenvolvimento/fallback"""
    
    def __init__(self):
        self.base_path = getattr(Config, 'LOCAL_STORAGE_PATH', 'uploads')
        self.base_url = getattr(Config, 'LOCAL_STORAGE_URL', 'http://localhost:5005/uploads')
        
        # Cria diretório se não existir
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"✅ Storage local configurado - Path: {self.base_path}")
    
    def upload_file(self, file_data: bytes, file_path: str, content_type: str = None) -> str:
        """Upload local"""
        try:
            full_path = os.path.join(self.base_path, file_path)
            
            # Cria diretórios necessários
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Salva arquivo
            with open(full_path, 'wb') as f:
                f.write(file_data)
            
            return f"{self.base_url}/{file_path}"
            
        except Exception as e:
            logger.error(f"Erro no upload local: {e}")
            raise
    
    def download_file(self, file_path: str) -> bytes:
        """Download local"""
        try:
            full_path = os.path.join(self.base_path, file_path)
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro no download local: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """Delete local"""
        try:
            full_path = os.path.join(self.base_path, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao deletar local: {e}")
            return False
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """URL local (sem expiração)"""
        return f"{self.base_url}/{file_path}"
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """Lista arquivos locais"""
        try:
            files = []
            search_path = os.path.join(self.base_path, prefix)
            
            for root, dirs, filenames in os.walk(search_path):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, self.base_path)
                    stat = os.stat(full_path)
                    
                    files.append({
                        'path': rel_path.replace('\\', '/'),
                        'size': stat.st_size,
                        'last_modified': datetime.fromtimestamp(stat.st_mtime),
                        'etag': hashlib.md5(open(full_path, 'rb').read()).hexdigest()
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Erro ao listar local: {e}")
            return []

class ImageOptimizer:
    """Otimizador de imagens"""
    
    @staticmethod
    def optimize_image(image_data: bytes, max_width: int = 1920, max_height: int = 1080, 
                      quality: int = 85, format: str = 'JPEG') -> Tuple[bytes, str]:
        """Otimiza imagem reduzindo tamanho e qualidade"""
        if not IMAGE_OPTIMIZATION_AVAILABLE:
            return image_data, 'image/jpeg'
        
        try:
            # Abre imagem
            image = Image.open(io.BytesIO(image_data))
            
            # Converte para RGB se necessário
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Redimensiona se necessário
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Salva otimizada
            output = io.BytesIO()
            image.save(output, format=format, quality=quality, optimize=True)
            optimized_data = output.getvalue()
            
            content_type = f'image/{format.lower()}'
            
            logger.info(f"Imagem otimizada: {len(image_data)} -> {len(optimized_data)} bytes")
            return optimized_data, content_type
            
        except Exception as e:
            logger.error(f"Erro na otimização de imagem: {e}")
            return image_data, 'image/jpeg'
    
    @staticmethod
    def create_thumbnails(image_data: bytes) -> Dict[str, bytes]:
        """Cria thumbnails em diferentes tamanhos"""
        if not IMAGE_OPTIMIZATION_AVAILABLE:
            return {}
        
        try:
            image = Image.open(io.BytesIO(image_data))
            
            thumbnails = {}
            sizes = {
                'thumb_small': (150, 150),
                'thumb_medium': (300, 300),
                'thumb_large': (600, 600)
            }
            
            for size_name, (width, height) in sizes.items():
                thumb = image.copy()
                thumb.thumbnail((width, height), Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                thumb.save(output, format='JPEG', quality=80)
                thumbnails[size_name] = output.getvalue()
            
            return thumbnails
            
        except Exception as e:
            logger.error(f"Erro ao criar thumbnails: {e}")
            return {}

class FileCompressor:
    """Compressor de arquivos"""
    
    @staticmethod
    def compress_data(data: bytes, compression_level: int = 6) -> bytes:
        """Comprime dados usando gzip"""
        if not COMPRESSION_AVAILABLE:
            return data
        
        try:
            return gzip.compress(data, compresslevel=compression_level)
        except Exception as e:
            logger.error(f"Erro na compressão: {e}")
            return data
    
    @staticmethod
    def decompress_data(compressed_data: bytes) -> bytes:
        """Descomprime dados gzip"""
        if not COMPRESSION_AVAILABLE:
            return compressed_data
        
        try:
            return gzip.decompress(compressed_data)
        except Exception as e:
            logger.error(f"Erro na descompressão: {e}")
            return compressed_data

class CloudStorageService:
    """Serviço principal de cloud storage"""
    
    def __init__(self):
        self.provider = self._initialize_provider()
        self.image_optimizer = ImageOptimizer()
        self.compressor = FileCompressor()
    
    def _initialize_provider(self) -> CloudStorageProvider:
        """Inicializa provedor baseado na configuração"""
        provider_name = getattr(Config, 'CLOUD_STORAGE_PROVIDER', 'local').lower()
        
        try:
            if provider_name == 'aws' and AWS_AVAILABLE:
                return AWSS3Provider()
            elif provider_name == 'gcp' and GCP_AVAILABLE:
                return GCPStorageProvider()
            else:
                logger.warning(f"Provedor {provider_name} não disponível, usando storage local")
                return LocalStorageProvider()
                
        except Exception as e:
            logger.error(f"Erro ao inicializar provedor {provider_name}: {e}")
            logger.warning("Fallback para storage local")
            return LocalStorageProvider()
    
    def upload_file(self, file_data: bytes, filename: str, user_id: int,
                   optimize_images: bool = True, compress: bool = True) -> Dict[str, Any]:
        """Upload completo com otimizações"""
        try:
            # Gera path único
            file_extension = os.path.splitext(filename)[1].lower()
            file_hash = hashlib.md5(file_data).hexdigest()
            timestamp = datetime.now().strftime('%Y/%m/%d')
            file_path = f"users/{user_id}/{timestamp}/{file_hash}{file_extension}"
            
            # Detecta tipo de arquivo
            content_type, _ = mimetypes.guess_type(filename)
            is_image = content_type and content_type.startswith('image/')
            
            original_size = len(file_data)
            processed_data = file_data
            thumbnails = {}
            
            # Otimiza imagens
            if is_image and optimize_images:
                processed_data, content_type = self.image_optimizer.optimize_image(file_data)
                thumbnails = self.image_optimizer.create_thumbnails(file_data)
            
            # Comprime se necessário (exceto imagens já otimizadas)
            elif compress and not is_image:
                compressed = self.compressor.compress_data(processed_data)
                if len(compressed) < len(processed_data):
                    processed_data = compressed
                    content_type = 'application/gzip'
            
            # Upload do arquivo principal
            file_url = self.provider.upload_file(processed_data, file_path, content_type)
            
            # Upload dos thumbnails
            thumbnail_urls = {}
            for thumb_name, thumb_data in thumbnails.items():
                thumb_path = f"users/{user_id}/{timestamp}/{file_hash}_{thumb_name}.jpg"
                thumbnail_urls[thumb_name] = self.provider.upload_file(
                    thumb_data, thumb_path, 'image/jpeg'
                )
            
            return {
                'success': True,
                'file_url': file_url,
                'file_path': file_path,
                'thumbnails': thumbnail_urls,
                'metadata': {
                    'original_filename': filename,
                    'content_type': content_type,
                    'original_size': original_size,
                    'processed_size': len(processed_data),
                    'compression_ratio': original_size / len(processed_data) if len(processed_data) > 0 else 1,
                    'is_image': is_image,
                    'has_thumbnails': len(thumbnails) > 0,
                    'uploaded_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Erro no upload: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Obtém URL do arquivo"""
        return self.provider.get_file_url(file_path, expires_in)
    
    def delete_file(self, file_path: str) -> bool:
        """Delete arquivo"""
        return self.provider.delete_file(file_path)
    
    def list_user_files(self, user_id: int) -> List[Dict[str, Any]]:
        """Lista arquivos do usuário"""
        return self.provider.list_files(f"users/{user_id}/")

# Instância global
storage_service = CloudStorageService()

# Funções de conveniência
def upload_file(file_data: bytes, filename: str, user_id: int, **kwargs) -> Dict[str, Any]:
    """Função de conveniência para upload"""
    return storage_service.upload_file(file_data, filename, user_id, **kwargs)

def get_file_url(file_path: str, expires_in: int = 3600) -> str:
    """Função de conveniência para obter URL"""
    return storage_service.get_file_url(file_path, expires_in)

def delete_file(file_path: str) -> bool:
    """Função de conveniência para deletar"""
    return storage_service.delete_file(file_path) 