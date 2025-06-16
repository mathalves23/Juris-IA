"""
Serviço de Backup Automático para PostgreSQL e SQLite
Suporta backup local e para S3
"""
import os
import gzip
import shutil
import subprocess
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class BackupService:
    """Serviço de backup automático do banco de dados"""
    
    def __init__(self, config=None):
        from src.config import Config
        self.config = config or Config()
        self.backup_path = self.config.get_backup_path()
        self.s3_client = None
        
        if getattr(self.config, 'BACKUP_S3_ENABLED', False):
            self._init_s3_client()
    
    def _init_s3_client(self):
        """Inicializa cliente S3 para backup em nuvem"""
        try:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.BACKUP_S3_ACCESS_KEY,
                aws_secret_access_key=self.config.BACKUP_S3_SECRET_KEY,
                region_name=getattr(self.config, 'BACKUP_S3_REGION', 'us-east-1')
            )
            logger.info("Cliente S3 inicializado para backup")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente S3: {e}")
            self.s3_client = None
    
    def create_backup(self, comment: Optional[str] = None) -> Dict[str, any]:
        """
        Cria backup do banco de dados
        
        Args:
            comment: Comentário opcional para o backup
            
        Returns:
            Dict com informações do backup criado
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_info = {
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'comment': comment,
                'success': False,
                'files': [],
                'size_bytes': 0,
                'database_type': 'postgresql' if self.config.is_postgresql() else 'sqlite',
                's3_upload': False
            }
            
            if self.config.is_postgresql():
                backup_file = self._backup_postgresql(timestamp)
            else:
                backup_file = self._backup_sqlite(timestamp)
            
            if backup_file and os.path.exists(backup_file):
                backup_info['files'].append(backup_file)
                backup_info['size_bytes'] = os.path.getsize(backup_file)
                backup_info['success'] = True
                
                # Comprimir backup
                compressed_file = self._compress_backup(backup_file)
                if compressed_file:
                    backup_info['files'] = [compressed_file]
                    backup_info['size_bytes'] = os.path.getsize(compressed_file)
                    os.remove(backup_file)  # Remove arquivo original
                
                # Upload para S3 se configurado
                if getattr(self.config, 'BACKUP_S3_ENABLED', False) and self.s3_client:
                    s3_success = self._upload_to_s3(
                        compressed_file or backup_file,
                        timestamp
                    )
                    backup_info['s3_upload'] = s3_success
                
                # Salvar metadados do backup
                self._save_backup_metadata(backup_info)
                
                logger.info(f"Backup criado com sucesso: {backup_file}")
                
            return backup_info
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            backup_info['success'] = False
            backup_info['error'] = str(e)
            return backup_info
    
    def _backup_postgresql(self, timestamp: str) -> Optional[str]:
        """Cria backup do PostgreSQL usando pg_dump"""
        try:
            backup_filename = f"jurisia_backup_{timestamp}.sql"
            backup_file = os.path.join(self.backup_path, backup_filename)
            
            # Extrair informações da URL do banco
            db_url = self.config.SQLALCHEMY_DATABASE_URI
            
            # Comando pg_dump
            cmd = [
                'pg_dump',
                '--no-password',
                '--format=plain',
                '--clean',
                '--create',
                '--verbose',
                '--file', backup_file,
                db_url
            ]
            
            # Executar backup
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hora de timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Backup PostgreSQL criado: {backup_file}")
                return backup_file
            else:
                logger.error(f"Erro no pg_dump: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout no backup PostgreSQL")
            return None
        except FileNotFoundError:
            logger.error("pg_dump não encontrado. Instale PostgreSQL client tools.")
            return None
        except Exception as e:
            logger.error(f"Erro no backup PostgreSQL: {e}")
            return None
    
    def _backup_sqlite(self, timestamp: str) -> Optional[str]:
        """Cria backup do SQLite copiando o arquivo"""
        try:
            # Encontrar arquivo SQLite
            db_url = self.config.SQLALCHEMY_DATABASE_URI
            if 'sqlite:///' in db_url:
                sqlite_file = db_url.replace('sqlite:///', '')
                
                if os.path.exists(sqlite_file):
                    backup_filename = f"jurisia_backup_{timestamp}.db"
                    backup_file = os.path.join(self.backup_path, backup_filename)
                    
                    # Fazer backup usando cópia simples (mais confiável)
                    shutil.copy2(sqlite_file, backup_file)
                    
                    if os.path.exists(backup_file):
                        logger.info(f"Backup SQLite criado: {backup_file}")
                        return backup_file
                        
        except Exception as e:
            logger.error(f"Erro no backup SQLite: {e}")
            return None
    
    def _compress_backup(self, backup_file: str) -> Optional[str]:
        """Comprime o arquivo de backup"""
        try:
            compressed_file = f"{backup_file}.gz"
            
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"Backup comprimido: {compressed_file}")
            return compressed_file
            
        except Exception as e:
            logger.error(f"Erro ao comprimir backup: {e}")
            return None
    
    def _upload_to_s3(self, backup_file: str, timestamp: str) -> bool:
        """Upload do backup para S3"""
        try:
            if not self.s3_client:
                return False
                
            filename = os.path.basename(backup_file)
            s3_key = f"backups/{timestamp}/{filename}"
            
            self.s3_client.upload_file(
                backup_file,
                getattr(self.config, 'BACKUP_S3_BUCKET', ''),
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'backup_date': timestamp,
                        'app': 'jurisia',
                        'version': getattr(self.config, 'APP_VERSION', '2.0.0')
                    }
                }
            )
            
            logger.info(f"Backup uploaded para S3: s3://{self.config.BACKUP_S3_BUCKET}/{s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro no upload S3: {e}")
            return False
    
    def _save_backup_metadata(self, backup_info: Dict):
        """Salva metadados do backup"""
        try:
            metadata_file = os.path.join(
                self.backup_path,
                f"backup_metadata_{backup_info['timestamp']}.json"
            )
            
            with open(metadata_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar metadados: {e}")
    
    def list_backups(self, limit: int = 50) -> List[Dict]:
        """Lista backups disponíveis"""
        backups = []
        
        try:
            # Buscar arquivos de backup
            backup_files = []
            for file in os.listdir(self.backup_path):
                if file.startswith('jurisia_backup_') and (file.endswith('.sql.gz') or file.endswith('.db.gz') or file.endswith('.sql') or file.endswith('.db')):
                    backup_files.append(file)
            
            # Ordenar por data (mais recente primeiro)
            backup_files.sort(reverse=True)
            
            for file in backup_files[:limit]:
                backup_info = self._get_backup_info(file)
                if backup_info:
                    backups.append(backup_info)
        
        except Exception as e:
            logger.error(f"Erro ao listar backups: {e}")
        
        return backups
    
    def _get_backup_info(self, filename: str) -> Optional[Dict]:
        """Obtém informações de um backup"""
        try:
            file_path = os.path.join(self.backup_path, filename)
            
            # Extrair timestamp do nome do arquivo
            parts = filename.split('_')
            if len(parts) >= 3:
                timestamp = parts[2].split('.')[0]
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Verificar se existe arquivo de metadados
            metadata_file = os.path.join(
                self.backup_path,
                f"backup_metadata_{timestamp}.json"
            )
            
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            else:
                # Criar info básica se não houver metadados
                stat = os.stat(file_path)
                return {
                    'timestamp': timestamp,
                    'datetime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'filename': filename,
                    'size_bytes': stat.st_size,
                    'database_type': 'postgresql' if '.sql' in filename else 'sqlite'
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter info do backup {filename}: {e}")
            return None
    
    def cleanup_old_backups(self) -> int:
        """Remove backups antigos baseado na política de retenção"""
        removed_count = 0
        
        try:
            retention_days = getattr(self.config, 'BACKUP_RETENTION_DAYS', 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for file in os.listdir(self.backup_path):
                if file.startswith('jurisia_backup_') or file.startswith('backup_metadata_'):
                    file_path = os.path.join(self.backup_path, file)
                    file_date = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_date < cutoff_date:
                        os.remove(file_path)
                        removed_count += 1
                        logger.info(f"Backup antigo removido: {file}")
            
            logger.info(f"Limpeza concluída. {removed_count} arquivos removidos.")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de backups: {e}")
        
        return removed_count
    
    def get_backup_status(self) -> Dict:
        """Retorna status geral do sistema de backup"""
        try:
            backups = self.list_backups(limit=10)
            
            return {
                'enabled': getattr(self.config, 'BACKUP_ENABLED', True),
                'database_type': 'postgresql' if self.config.is_postgresql() else 'sqlite',
                'backup_path': self.backup_path,
                's3_enabled': getattr(self.config, 'BACKUP_S3_ENABLED', False),
                's3_bucket': getattr(self.config, 'BACKUP_S3_BUCKET', None),
                'retention_days': getattr(self.config, 'BACKUP_RETENTION_DAYS', 30),
                'interval_hours': getattr(self.config, 'BACKUP_INTERVAL_HOURS', 24),
                'total_backups': len(backups),
                'latest_backup': backups[0] if backups else None,
                'total_size_mb': sum(b.get('size_bytes', 0) for b in backups) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status do backup: {e}")
            return {'error': str(e)}


class BackupScheduler:
    """Agendador de backups automáticos"""
    
    def __init__(self, backup_service: BackupService):
        self.backup_service = backup_service
        self.config = backup_service.config
    
    def should_create_backup(self) -> bool:
        """Verifica se é hora de criar um novo backup"""
        try:
            backups = self.backup_service.list_backups(limit=1)
            
            if not backups:
                return True  # Nenhum backup existe
            
            latest_backup = backups[0]
            latest_date = datetime.fromisoformat(latest_backup['datetime'])
            
            time_since_backup = datetime.now() - latest_date
            interval_hours = getattr(self.config, 'BACKUP_INTERVAL_HOURS', 24)
            interval_threshold = timedelta(hours=interval_hours)
            
            return time_since_backup >= interval_threshold
            
        except Exception as e:
            logger.error(f"Erro ao verificar necessidade de backup: {e}")
            return True  # Em caso de erro, criar backup
    
    def run_scheduled_backup(self) -> Optional[Dict]:
        """Executa backup agendado se necessário"""
        backup_enabled = getattr(self.config, 'BACKUP_ENABLED', True)
        
        if not backup_enabled:
            return None
        
        if self.should_create_backup():
            logger.info("Iniciando backup automático agendado")
            result = self.backup_service.create_backup(
                comment="Backup automático agendado"
            )
            
            # Limpar backups antigos após criar novo
            if result.get('success'):
                self.backup_service.cleanup_old_backups()
            
            return result
        
        return None


# Instância global do serviço de backup
backup_service = BackupService()
backup_scheduler = BackupScheduler(backup_service) 