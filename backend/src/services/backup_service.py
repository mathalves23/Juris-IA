import os
import json
import gzip
import shutil
import sqlite3
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import structlog
from pathlib import Path
import hashlib
import boto3
from botocore.exceptions import ClientError
import tempfile
import zipfile

@dataclass
class BackupMetadata:
    """Metadados do backup"""
    id: str
    timestamp: datetime
    type: str  # 'full', 'incremental', 'differential'
    size_bytes: int
    checksum: str
    tables: List[str]
    file_path: str
    compressed: bool
    encrypted: bool
    status: str  # 'created', 'uploading', 'completed', 'failed'
    error_message: Optional[str] = None

class BackupService:
    """Serviço de backup e recuperação"""
    
    def __init__(self, 
                 db_path: str = "jurisia.db",
                 backup_dir: str = "backups",
                 s3_bucket: Optional[str] = None,
                 encryption_key: Optional[str] = None):
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.s3_bucket = s3_bucket
        self.encryption_key = encryption_key
        self.logger = structlog.get_logger("backup_service")
        
        # Configurar cliente S3 se bucket fornecido
        self.s3_client = None
        if s3_bucket:
            try:
                self.s3_client = boto3.client('s3')
                self.logger.info("s3_client_initialized", bucket=s3_bucket)
            except Exception as e:
                self.logger.error("s3_client_init_failed", error=str(e))
        
        # Histórico de backups
        self.backup_history: List[BackupMetadata] = []
        self._load_backup_history()
        
        # Configurar agendamento automático
        self._setup_scheduled_backups()
    
    def _load_backup_history(self):
        """Carregar histórico de backups"""
        history_file = self.backup_dir / "backup_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.backup_history = [
                        BackupMetadata(
                            id=item['id'],
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            type=item['type'],
                            size_bytes=item['size_bytes'],
                            checksum=item['checksum'],
                            tables=item['tables'],
                            file_path=item['file_path'],
                            compressed=item['compressed'],
                            encrypted=item['encrypted'],
                            status=item['status'],
                            error_message=item.get('error_message')
                        )
                        for item in data
                    ]
            except Exception as e:
                self.logger.error("load_backup_history_failed", error=str(e))
    
    def _save_backup_history(self):
        """Salvar histórico de backups"""
        history_file = self.backup_dir / "backup_history.json"
        try:
            data = []
            for backup in self.backup_history:
                item = asdict(backup)
                item['timestamp'] = backup.timestamp.isoformat()
                data.append(item)
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error("save_backup_history_failed", error=str(e))
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calcular checksum MD5 do arquivo"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _compress_file(self, source_path: str, target_path: str) -> bool:
        """Comprimir arquivo usando gzip"""
        try:
            with open(source_path, 'rb') as f_in:
                with gzip.open(target_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            self.logger.error("compression_failed", error=str(e))
            return False
    
    def _encrypt_file(self, file_path: str) -> bool:
        """Criptografar arquivo (implementação básica)"""
        if not self.encryption_key:
            return False
        
        try:
            # Implementação básica - em produção usar bibliotecas como cryptography
            from cryptography.fernet import Fernet
            
            # Gerar chave se não existir
            if not hasattr(self, '_fernet'):
                key = self.encryption_key.encode()[:32].ljust(32, b'0')
                import base64
                key = base64.urlsafe_b64encode(key)
                self._fernet = Fernet(key)
            
            # Ler arquivo
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Criptografar
            encrypted_data = self._fernet.encrypt(data)
            
            # Escrever arquivo criptografado
            with open(file_path + '.enc', 'wb') as f:
                f.write(encrypted_data)
            
            # Remover arquivo original
            os.remove(file_path)
            os.rename(file_path + '.enc', file_path)
            
            return True
        except Exception as e:
            self.logger.error("encryption_failed", error=str(e))
            return False
    
    def _upload_to_s3(self, file_path: str, s3_key: str) -> bool:
        """Upload do backup para S3"""
        if not self.s3_client or not self.s3_bucket:
            return False
        
        try:
            self.s3_client.upload_file(file_path, self.s3_bucket, s3_key)
            self.logger.info("s3_upload_success", file=file_path, key=s3_key)
            return True
        except ClientError as e:
            self.logger.error("s3_upload_failed", error=str(e), file=file_path)
            return False
    
    def create_full_backup(self, compress: bool = True, encrypt: bool = False, upload_s3: bool = False) -> Optional[BackupMetadata]:
        """Criar backup completo do banco de dados"""
        backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now()
        
        try:
            # Criar arquivo de backup
            backup_file = self.backup_dir / f"{backup_id}.sql"
            
            # Fazer backup do SQLite
            with sqlite3.connect(self.db_path) as source_conn:
                with open(backup_file, 'w') as f:
                    for line in source_conn.iterdump():
                        f.write('%s\n' % line)
            
            # Obter lista de tabelas
            tables = self._get_table_list()
            
            # Comprimir se solicitado
            if compress:
                compressed_file = str(backup_file) + '.gz'
                if self._compress_file(str(backup_file), compressed_file):
                    os.remove(backup_file)
                    backup_file = Path(compressed_file)
                else:
                    compress = False
            
            # Criptografar se solicitado
            if encrypt:
                if not self._encrypt_file(str(backup_file)):
                    encrypt = False
            
            # Calcular checksum e tamanho
            file_size = backup_file.stat().st_size
            checksum = self._calculate_checksum(str(backup_file))
            
            # Criar metadados
            metadata = BackupMetadata(
                id=backup_id,
                timestamp=timestamp,
                type='full',
                size_bytes=file_size,
                checksum=checksum,
                tables=tables,
                file_path=str(backup_file),
                compressed=compress,
                encrypted=encrypt,
                status='created'
            )
            
            # Upload para S3 se solicitado
            if upload_s3:
                metadata.status = 'uploading'
                s3_key = f"backups/{backup_id}/{backup_file.name}"
                if self._upload_to_s3(str(backup_file), s3_key):
                    metadata.status = 'completed'
                else:
                    metadata.status = 'failed'
                    metadata.error_message = 'S3 upload failed'
            else:
                metadata.status = 'completed'
            
            # Adicionar ao histórico
            self.backup_history.append(metadata)
            self._save_backup_history()
            
            self.logger.info(
                "backup_created",
                backup_id=backup_id,
                size_mb=file_size / 1024 / 1024,
                compressed=compress,
                encrypted=encrypt,
                status=metadata.status
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error("backup_creation_failed", error=str(e), backup_id=backup_id)
            
            # Criar metadados de falha
            metadata = BackupMetadata(
                id=backup_id,
                timestamp=timestamp,
                type='full',
                size_bytes=0,
                checksum='',
                tables=[],
                file_path='',
                compressed=False,
                encrypted=False,
                status='failed',
                error_message=str(e)
            )
            
            self.backup_history.append(metadata)
            self._save_backup_history()
            
            return None
    
    def create_incremental_backup(self, since: Optional[datetime] = None) -> Optional[BackupMetadata]:
        """Criar backup incremental (apenas dados modificados)"""
        if not since:
            # Usar último backup como referência
            last_backup = self.get_last_backup()
            if last_backup:
                since = last_backup.timestamp
            else:
                # Se não há backup anterior, fazer backup completo
                return self.create_full_backup()
        
        backup_id = f"incr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now()
        
        try:
            # Criar arquivo de backup incremental
            backup_file = self.backup_dir / f"{backup_id}.json"
            
            # Coletar dados modificados desde a data especificada
            incremental_data = self._collect_incremental_data(since)
            
            # Salvar dados incrementais
            with open(backup_file, 'w') as f:
                json.dump(incremental_data, f, indent=2, default=str)
            
            # Comprimir
            compressed_file = str(backup_file) + '.gz'
            if self._compress_file(str(backup_file), compressed_file):
                os.remove(backup_file)
                backup_file = Path(compressed_file)
            
            # Calcular checksum e tamanho
            file_size = backup_file.stat().st_size
            checksum = self._calculate_checksum(str(backup_file))
            
            # Criar metadados
            metadata = BackupMetadata(
                id=backup_id,
                timestamp=timestamp,
                type='incremental',
                size_bytes=file_size,
                checksum=checksum,
                tables=list(incremental_data.keys()),
                file_path=str(backup_file),
                compressed=True,
                encrypted=False,
                status='completed'
            )
            
            # Adicionar ao histórico
            self.backup_history.append(metadata)
            self._save_backup_history()
            
            self.logger.info(
                "incremental_backup_created",
                backup_id=backup_id,
                size_kb=file_size / 1024,
                tables=len(incremental_data)
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error("incremental_backup_failed", error=str(e))
            return None
    
    def _collect_incremental_data(self, since: datetime) -> Dict[str, List[Dict]]:
        """Coletar dados modificados desde uma data"""
        incremental_data = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Tabelas com timestamp de modificação
                tables_with_timestamp = ['users', 'documents', 'templates']
                
                for table in tables_with_timestamp:
                    try:
                        # Verificar se tabela tem coluna updated_at
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        if 'updated_at' in columns:
                            query = f"""
                                SELECT * FROM {table} 
                                WHERE updated_at > ? 
                                ORDER BY updated_at
                            """
                            cursor.execute(query, (since.isoformat(),))
                            rows = cursor.fetchall()
                            
                            if rows:
                                incremental_data[table] = [dict(row) for row in rows]
                    
                    except sqlite3.Error as e:
                        self.logger.warning(f"incremental_data_table_error", table=table, error=str(e))
                        continue
        
        except Exception as e:
            self.logger.error("incremental_data_collection_failed", error=str(e))
        
        return incremental_data
    
    def _get_table_list(self) -> List[str]:
        """Obter lista de tabelas do banco"""
        tables = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error("get_table_list_failed", error=str(e))
        
        return tables
    
    def restore_backup(self, backup_id: str, target_db: Optional[str] = None) -> bool:
        """Restaurar backup"""
        backup = self.get_backup_by_id(backup_id)
        if not backup:
            self.logger.error("backup_not_found", backup_id=backup_id)
            return False
        
        target_db = target_db or self.db_path
        
        try:
            if backup.type == 'full':
                return self._restore_full_backup(backup, target_db)
            elif backup.type == 'incremental':
                return self._restore_incremental_backup(backup, target_db)
            else:
                self.logger.error("unsupported_backup_type", type=backup.type)
                return False
                
        except Exception as e:
            self.logger.error("restore_failed", backup_id=backup_id, error=str(e))
            return False
    
    def _restore_full_backup(self, backup: BackupMetadata, target_db: str) -> bool:
        """Restaurar backup completo"""
        try:
            backup_file = backup.file_path
            
            # Descriptografar se necessário
            if backup.encrypted:
                # Implementar descriptografia
                pass
            
            # Descomprimir se necessário
            if backup.compressed:
                with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_file:
                    with gzip.open(backup_file, 'rb') as f_in:
                        shutil.copyfileobj(f_in, temp_file)
                    backup_file = temp_file.name
            
            # Fazer backup do banco atual
            if os.path.exists(target_db):
                backup_current = f"{target_db}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(target_db, backup_current)
                self.logger.info("current_db_backed_up", backup_file=backup_current)
            
            # Restaurar banco
            with sqlite3.connect(target_db) as conn:
                with open(backup_file, 'r') as f:
                    sql_script = f.read()
                    conn.executescript(sql_script)
            
            # Limpar arquivo temporário se foi descomprimido
            if backup.compressed and backup_file != backup.file_path:
                os.unlink(backup_file)
            
            self.logger.info("full_backup_restored", backup_id=backup.id, target=target_db)
            return True
            
        except Exception as e:
            self.logger.error("full_backup_restore_failed", error=str(e))
            return False
    
    def _restore_incremental_backup(self, backup: BackupMetadata, target_db: str) -> bool:
        """Restaurar backup incremental"""
        try:
            backup_file = backup.file_path
            
            # Descomprimir se necessário
            if backup.compressed:
                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                    with gzip.open(backup_file, 'rb') as f_in:
                        shutil.copyfileobj(f_in, temp_file)
                    backup_file = temp_file.name
            
            # Carregar dados incrementais
            with open(backup_file, 'r') as f:
                incremental_data = json.load(f)
            
            # Aplicar dados ao banco
            with sqlite3.connect(target_db) as conn:
                for table, rows in incremental_data.items():
                    for row in rows:
                        # Implementar lógica de upsert baseada na estrutura da tabela
                        self._upsert_row(conn, table, row)
            
            # Limpar arquivo temporário se foi descomprimido
            if backup.compressed and backup_file != backup.file_path:
                os.unlink(backup_file)
            
            self.logger.info("incremental_backup_restored", backup_id=backup.id)
            return True
            
        except Exception as e:
            self.logger.error("incremental_backup_restore_failed", error=str(e))
            return False
    
    def _upsert_row(self, conn: sqlite3.Connection, table: str, row: Dict):
        """Inserir ou atualizar linha na tabela"""
        try:
            cursor = conn.cursor()
            
            # Obter estrutura da tabela
            cursor.execute(f"PRAGMA table_info({table})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            primary_keys = [col[1] for col in columns_info if col[5] == 1]
            
            # Filtrar colunas que existem na tabela
            filtered_row = {k: v for k, v in row.items() if k in columns}
            
            if primary_keys and all(pk in filtered_row for pk in primary_keys):
                # Fazer UPDATE se registro existe
                pk_conditions = ' AND '.join([f"{pk} = ?" for pk in primary_keys])
                pk_values = [filtered_row[pk] for pk in primary_keys]
                
                cursor.execute(f"SELECT 1 FROM {table} WHERE {pk_conditions}", pk_values)
                if cursor.fetchone():
                    # UPDATE
                    set_clause = ', '.join([f"{k} = ?" for k in filtered_row.keys() if k not in primary_keys])
                    if set_clause:
                        update_values = [v for k, v in filtered_row.items() if k not in primary_keys]
                        query = f"UPDATE {table} SET {set_clause} WHERE {pk_conditions}"
                        cursor.execute(query, update_values + pk_values)
                    return
            
            # INSERT
            columns_str = ', '.join(filtered_row.keys())
            placeholders = ', '.join(['?' for _ in filtered_row])
            query = f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({placeholders})"
            cursor.execute(query, list(filtered_row.values()))
            
        except Exception as e:
            self.logger.error("upsert_row_failed", table=table, error=str(e))
    
    def get_backup_by_id(self, backup_id: str) -> Optional[BackupMetadata]:
        """Obter backup por ID"""
        for backup in self.backup_history:
            if backup.id == backup_id:
                return backup
        return None
    
    def get_last_backup(self, backup_type: Optional[str] = None) -> Optional[BackupMetadata]:
        """Obter último backup"""
        filtered_backups = [
            b for b in self.backup_history 
            if b.status == 'completed' and (not backup_type or b.type == backup_type)
        ]
        
        if filtered_backups:
            return max(filtered_backups, key=lambda b: b.timestamp)
        return None
    
    def list_backups(self, limit: int = 50) -> List[BackupMetadata]:
        """Listar backups"""
        return sorted(self.backup_history, key=lambda b: b.timestamp, reverse=True)[:limit]
    
    def delete_backup(self, backup_id: str) -> bool:
        """Deletar backup"""
        backup = self.get_backup_by_id(backup_id)
        if not backup:
            return False
        
        try:
            # Remover arquivo local
            if os.path.exists(backup.file_path):
                os.remove(backup.file_path)
            
            # Remover do S3 se aplicável
            if self.s3_client and self.s3_bucket:
                s3_key = f"backups/{backup_id}/{Path(backup.file_path).name}"
                try:
                    self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                except ClientError:
                    pass  # Arquivo pode não existir no S3
            
            # Remover do histórico
            self.backup_history = [b for b in self.backup_history if b.id != backup_id]
            self._save_backup_history()
            
            self.logger.info("backup_deleted", backup_id=backup_id)
            return True
            
        except Exception as e:
            self.logger.error("backup_deletion_failed", backup_id=backup_id, error=str(e))
            return False
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10):
        """Limpar backups antigos"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        # Manter sempre os últimos keep_count backups
        sorted_backups = sorted(self.backup_history, key=lambda b: b.timestamp, reverse=True)
        keep_backups = set(b.id for b in sorted_backups[:keep_count])
        
        deleted_count = 0
        for backup in self.backup_history[:]:
            if backup.timestamp < cutoff_date and backup.id not in keep_backups:
                if self.delete_backup(backup.id):
                    deleted_count += 1
        
        self.logger.info("old_backups_cleaned", deleted_count=deleted_count, keep_days=keep_days)
    
    def _setup_scheduled_backups(self):
        """Configurar backups automáticos"""
        # Backup completo diário às 2:00
        schedule.every().day.at("02:00").do(self._scheduled_full_backup)
        
        # Backup incremental a cada 6 horas
        schedule.every(6).hours.do(self._scheduled_incremental_backup)
        
        # Limpeza semanal
        schedule.every().sunday.at("03:00").do(self.cleanup_old_backups)
        
        # Iniciar thread do scheduler
        def run_scheduler():
            while True:
                schedule.run_pending()
                import time
                time.sleep(60)  # Verificar a cada minuto
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("scheduled_backups_configured")
    
    def _scheduled_full_backup(self):
        """Backup completo agendado"""
        self.logger.info("starting_scheduled_full_backup")
        backup = self.create_full_backup(compress=True, upload_s3=bool(self.s3_bucket))
        if backup:
            self.logger.info("scheduled_full_backup_completed", backup_id=backup.id)
        else:
            self.logger.error("scheduled_full_backup_failed")
    
    def _scheduled_incremental_backup(self):
        """Backup incremental agendado"""
        self.logger.info("starting_scheduled_incremental_backup")
        backup = self.create_incremental_backup()
        if backup:
            self.logger.info("scheduled_incremental_backup_completed", backup_id=backup.id)
        else:
            self.logger.error("scheduled_incremental_backup_failed")

# Instância global do serviço de backup
backup_service = BackupService()

def init_backup_service(db_path: str, backup_dir: str = "backups", 
                       s3_bucket: Optional[str] = None, 
                       encryption_key: Optional[str] = None):
    """Inicializar serviço de backup"""
    global backup_service
    backup_service = BackupService(db_path, backup_dir, s3_bucket, encryption_key)
    return backup_service 