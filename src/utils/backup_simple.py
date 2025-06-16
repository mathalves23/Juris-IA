import os
import shutil
import subprocess
import gzip
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
import threading

logger = logging.getLogger(__name__)

class BackupManager:
    """Gerenciador de backups do banco de dados (versão simplificada)"""
    
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = None
        self.retention_days = 30
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar com app Flask"""
        self.app = app
        self.backup_dir = Path(app.config.get('BACKUP_DIR', 'backups'))
        self.retention_days = app.config.get('BACKUP_RETENTION_DAYS', 30)
        
        # Criar diretório de backup
        self.backup_dir.mkdir(exist_ok=True)
        
        app.logger.info("Backup manager initialized")
    
    def create_backup(self):
        """Criar backup completo"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"jurisia_backup_{timestamp}"
            
            # Determinar tipo de banco
            db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
            
            if db_uri.startswith('sqlite'):
                backup_file = self.backup_sqlite(backup_name)
            else:
                raise ValueError(f"Unsupported database type for simple backup: {db_uri}")
            
            # Comprimir backup
            compressed_file = self.compress_backup(backup_file)
            
            # Limpar backups antigos
            self.cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {compressed_file}")
            return compressed_file
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
    
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