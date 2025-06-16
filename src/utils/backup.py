import os
import shutil
import subprocess
import gzip
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
import logging
import boto3
from botocore.exceptions import ClientError
import schedule
import time
import threading

logger = logging.getLogger(__name__)

class BackupManager:
    """Gerenciador de backups do banco de dados"""
    
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = None
        self.retention_days = 30
        self.s3_client = None
        self.s3_bucket = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar com app Flask"""
        self.app = app
        self.backup_dir = Path(app.config.get('BACKUP_DIR', 'backups'))
        self.retention_days = app.config.get('BACKUP_RETENTION_DAYS', 30)
        
        # Configurar AWS S3 se disponível
        aws_access_key = app.config.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = app.config.get('AWS_SECRET_ACCESS_KEY')
        self.s3_bucket = app.config.get('AWS_S3_BACKUP_BUCKET')
        
        if aws_access_key and aws_secret_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=app.config.get('AWS_REGION', 'us-east-1')
            )
        
        # Criar diretório de backup
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configurar schedule de backup
        schedule_time = app.config.get('BACKUP_SCHEDULE', '02:00')
        schedule.every().day.at(schedule_time).do(self.create_backup)
        
        # Iniciar thread de backup em produção
        if not app.debug:
            self.start_backup_scheduler()
    
    def start_backup_scheduler(self):
        """Iniciar scheduler de backup em thread separada"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        backup_thread = threading.Thread(target=run_scheduler, daemon=True)
        backup_thread.start()
        logger.info("Backup scheduler started")
    
    def create_backup(self):
        """Criar backup completo"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"jurisia_backup_{timestamp}"
            
            # Determinar tipo de banco
            db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
            
            if db_uri.startswith('postgresql'):
                backup_file = self.backup_postgresql(backup_name)
            elif db_uri.startswith('sqlite'):
                backup_file = self.backup_sqlite(backup_name)
            else:
                raise ValueError(f"Unsupported database type: {db_uri}")
            
            # Comprimir backup
            compressed_file = self.compress_backup(backup_file)
            
            # Upload para S3 se configurado
            if self.s3_client:
                self.upload_to_s3(compressed_file, backup_name)
            
            # Limpar backups antigos
            self.cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {compressed_file}")
            return compressed_file
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
    def backup_postgresql(self, backup_name):
        """Backup PostgreSQL usando pg_dump"""
        db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        # Extrair informações de conexão da URI
        import urllib.parse
        parsed = urllib.parse.urlparse(db_uri)
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'pg_dump',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path[1:],  # Remove leading '/'
            '-f', str(backup_file),
            '--no-owner',
            '--no-privileges',
            '--clean',
            '--if-exists'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump failed: {result.stderr}")
        
        return backup_file
    
    def backup_sqlite(self, backup_name):
        """Backup SQLite copiando arquivo"""
        db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        backup_file = self.backup_dir / f"{backup_name}.db"
        
        # Copiar arquivo SQLite
        shutil.copy2(db_path, backup_file)
        
        return backup_file
    
    def compress_backup(self, backup_file):
        """Comprimir arquivo de backup"""
        compressed_file = Path(str(backup_file) + '.tar.gz')
        
        with tarfile.open(compressed_file, 'w:gz') as tar:
            tar.add(backup_file, arcname=backup_file.name)
        
        # Remover arquivo original não comprimido
        backup_file.unlink()
        
        return compressed_file
    
    def upload_to_s3(self, backup_file, backup_name):
        """Upload backup para S3"""
        if not self.s3_client or not self.s3_bucket:
            return
        
        try:
            s3_key = f"backups/{backup_name}.tar.gz"
            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Cheaper storage for backups
                }
            )
            logger.info(f"Backup uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
            
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
    
    def cleanup_old_backups(self):
        """Limpar backups antigos baseado em retention policy"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # Limpar backups locais
        for backup_file in self.backup_dir.glob('jurisia_backup_*.tar.gz'):
            try:
                # Extrair timestamp do nome do arquivo
                timestamp_str = backup_file.stem.split('_')[-2] + '_' + backup_file.stem.split('_')[-1]
                file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Deleted old backup: {backup_file}")
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse backup file date: {backup_file}")
        
        # Limpar backups no S3
        if self.s3_client and self.s3_bucket:
            self.cleanup_s3_backups(cutoff_date)
    
    def cleanup_s3_backups(self, cutoff_date):
        """Limpar backups antigos no S3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix='backups/'
            )
            
            if 'Contents' not in response:
                return
            
            for obj in response['Contents']:
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    self.s3_client.delete_object(
                        Bucket=self.s3_bucket,
                        Key=obj['Key']
                    )
                    logger.info(f"Deleted old S3 backup: {obj['Key']}")
                    
        except ClientError as e:
            logger.error(f"Failed to cleanup S3 backups: {e}")
    
    def restore_backup(self, backup_file, confirm=False):
        """Restaurar backup (USE COM CUIDADO!)"""
        if not confirm:
            raise ValueError("Restore operation requires explicit confirmation")
        
        try:
            # Descomprimir backup
            backup_path = Path(backup_file)
            if backup_path.suffix == '.gz':
                extracted_dir = self.backup_dir / 'restore_temp'
                extracted_dir.mkdir(exist_ok=True)
                
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(extracted_dir)
                
                # Encontrar arquivo SQL ou DB
                sql_files = list(extracted_dir.glob('*.sql'))
                db_files = list(extracted_dir.glob('*.db'))
                
                if sql_files:
                    restore_file = sql_files[0]
                    self.restore_postgresql(restore_file)
                elif db_files:
                    restore_file = db_files[0]
                    self.restore_sqlite(restore_file)
                else:
                    raise ValueError("No valid backup file found in archive")
                
                # Limpar arquivos temporários
                shutil.rmtree(extracted_dir)
            
            logger.info(f"Database restored from backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            raise
    
    def restore_postgresql(self, sql_file):
        """Restaurar PostgreSQL usando psql"""
        db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
        import urllib.parse
        parsed = urllib.parse.urlparse(db_uri)
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        cmd = [
            'psql',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path[1:],
            '-f', str(sql_file)
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"psql restore failed: {result.stderr}")
    
    def restore_sqlite(self, db_file):
        """Restaurar SQLite substituindo arquivo"""
        db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        
        # Fazer backup do arquivo atual
        if os.path.exists(db_path):
            backup_current = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_current)
        
        # Restaurar arquivo
        shutil.copy2(db_file, db_path)
    
    def list_backups(self):
        """Listar backups disponíveis"""
        backups = []
        
        # Backups locais
        for backup_file in sorted(self.backup_dir.glob('jurisia_backup_*.tar.gz')):
            try:
                timestamp_str = backup_file.stem.split('_')[-2] + '_' + backup_file.stem.split('_')[-1]
                file_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'date': file_date,
                    'size': backup_file.stat().st_size,
                    'location': 'local'
                })
            except (ValueError, IndexError):
                continue
        
        # Backups no S3
        if self.s3_client and self.s3_bucket:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix='backups/'
                )
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        backups.append({
                            'name': obj['Key'].split('/')[-1],
                            'path': f"s3://{self.s3_bucket}/{obj['Key']}",
                            'date': obj['LastModified'].replace(tzinfo=None),
                            'size': obj['Size'],
                            'location': 's3'
                        })
            except ClientError as e:
                logger.error(f"Failed to list S3 backups: {e}")
        
        return sorted(backups, key=lambda x: x['date'], reverse=True)

# CLI commands para backup manual
def create_backup_command():
    """Comando CLI para criar backup manual"""
    from flask import current_app
    backup_manager = current_app.extensions.get('backup_manager')
    if backup_manager:
        backup_file = backup_manager.create_backup()
        print(f"Backup created: {backup_file}")
    else:
        print("Backup manager not initialized")

def list_backups_command():
    """Comando CLI para listar backups"""
    from flask import current_app
    backup_manager = current_app.extensions.get('backup_manager')
    if backup_manager:
        backups = backup_manager.list_backups()
        print(f"{'Name':<40} {'Date':<20} {'Size':<10} {'Location'}")
        print("-" * 80)
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            print(f"{backup['name']:<40} {backup['date'].strftime('%Y-%m-%d %H:%M'):<20} {size_mb:.1f}MB {backup['location']}")
    else:
        print("Backup manager not initialized") 