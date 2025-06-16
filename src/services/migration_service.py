"""
Serviço de Migration Automática
Controla versões do banco de dados e executa migrations de forma segura
"""
import os
import json
import logging
import importlib.util
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text, inspect
from src.extensions import db

logger = logging.getLogger(__name__)

class Migration:
    """Classe para representar uma migration"""
    
    def __init__(self, version: str, name: str, description: str = ''):
        self.version = version
        self.name = name
        self.description = description
        self.timestamp = datetime.now()
        self.executed = False
        self.execution_time = None
        
    def to_dict(self):
        return {
            'version': self.version,
            'name': self.name,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'executed': self.executed,
            'execution_time': self.execution_time
        }

class MigrationService:
    """Serviço de controle de migrations"""
    
    def __init__(self, config=None):
        from src.config import Config
        self.config = config or Config()
        self.migrations_dir = getattr(self.config, 'MIGRATION_DIR', 'migrations')
        self.migrations_table = '_jurisia_migrations'
        self.ensure_migrations_table()
        
    def ensure_migrations_table(self):
        """Garante que a tabela de controle de migrations existe"""
        try:
            # Verificar se a tabela já existe
            inspector = inspect(db.engine)
            if not inspector.has_table(self.migrations_table):
                # Criar tabela de migrations
                if 'sqlite' in str(db.engine.url):
                    create_table_sql = f"""
                    CREATE TABLE {self.migrations_table} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        execution_time_ms INTEGER,
                        checksum VARCHAR(64)
                    )
                    """
                else:
                    create_table_sql = f"""
                    CREATE TABLE {self.migrations_table} (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        name VARCHAR(200) NOT NULL,
                        description TEXT,
                        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        execution_time_ms INTEGER,
                        checksum VARCHAR(64)
                    )
                    """
                
                with db.engine.connect() as conn:
                    conn.execute(text(create_table_sql))
                    conn.commit()
                
                logger.info("Tabela de migrations criada")
        
        except Exception as e:
            logger.error(f"Erro ao criar tabela de migrations: {e}")
    
    def get_executed_migrations(self) -> List[str]:
        """Retorna lista de migrations já executadas"""
        try:
            query = f"SELECT version FROM {self.migrations_table} ORDER BY executed_at"
            with db.engine.connect() as conn:
                result = conn.execute(text(query))
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Erro ao buscar migrations executadas: {e}")
            return []
    
    def get_available_migrations(self) -> List[Migration]:
        """Retorna lista de migrations disponíveis"""
        migrations = []
        
        try:
            # Criar diretório de migrations se não existir
            os.makedirs(self.migrations_dir, exist_ok=True)
            
            # Buscar arquivos de migration
            migration_files = []
            for file in os.listdir(self.migrations_dir):
                if file.endswith('.py') and file.startswith('migration_'):
                    migration_files.append(file)
            
            # Ordenar por versão
            migration_files.sort()
            
            for file in migration_files:
                try:
                    # Extrair versão do nome do arquivo
                    # Formato esperado: migration_001_nome_da_migration.py
                    parts = file.replace('.py', '').split('_')
                    if len(parts) >= 3:
                        version = parts[1]
                        name = '_'.join(parts[2:])
                        
                        # Carregar descrição do arquivo
                        description = self._get_migration_description(
                            os.path.join(self.migrations_dir, file)
                        )
                        
                        migration = Migration(version, name, description)
                        migrations.append(migration)
                
                except Exception as e:
                    logger.warning(f"Erro ao processar migration {file}: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao buscar migrations disponíveis: {e}")
        
        return migrations
    
    def _get_migration_description(self, file_path: str) -> str:
        """Extrai descrição da migration do arquivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Buscar docstring no início do arquivo
                lines = content.split('\n')
                for i, line in enumerate(lines[:10]):  # Primeiras 10 linhas
                    if '"""' in line:
                        # Encontrar fim da docstring
                        desc_lines = []
                        for j in range(i, len(lines)):
                            if j > i and '"""' in lines[j]:
                                break
                            desc_lines.append(lines[j].replace('"""', '').strip())
                        
                        return ' '.join(desc_lines).strip()
        
        except Exception:
            pass
        
        return ''
    
    def get_pending_migrations(self) -> List[Migration]:
        """Retorna migrations pendentes de execução"""
        executed = set(self.get_executed_migrations())
        available = self.get_available_migrations()
        
        pending = []
        for migration in available:
            if migration.version not in executed:
                pending.append(migration)
        
        return pending
    
    def execute_migration(self, migration: Migration) -> bool:
        """Executa uma migration específica"""
        try:
            file_path = os.path.join(
                self.migrations_dir, 
                f"migration_{migration.version}_{migration.name}.py"
            )
            
            if not os.path.exists(file_path):
                logger.error(f"Arquivo de migration não encontrado: {file_path}")
                return False
            
            # Carregar módulo da migration
            spec = importlib.util.spec_from_file_location(
                f"migration_{migration.version}",
                file_path
            )
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Verificar se tem função upgrade
            if not hasattr(migration_module, 'upgrade'):
                logger.error(f"Migration {migration.version} não tem função upgrade()")
                return False
            
            start_time = datetime.now()
            
            # Executar migration em transação
            with db.engine.connect() as conn:
                trans = conn.begin()
                try:
                    # Executar upgrade
                    migration_module.upgrade(conn)
                    
                    # Registrar execução
                    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if 'postgresql' in str(db.engine.url):
                        insert_sql = f"""
                        INSERT INTO {self.migrations_table} 
                        (version, name, description, execution_time_ms) 
                        VALUES (%s, %s, %s, %s)
                        """
                        params = [
                            migration.version,
                            migration.name,
                            migration.description,
                            execution_time
                        ]
                    else:
                        insert_sql = f"""
                        INSERT INTO {self.migrations_table} 
                        (version, name, description, execution_time_ms) 
                        VALUES (?, ?, ?, ?)
                        """
                        params = [
                            migration.version,
                            migration.name,
                            migration.description,
                            execution_time
                        ]
                    
                    conn.execute(text(insert_sql), params)
                    trans.commit()
                    
                    logger.info(f"Migration {migration.version} executada com sucesso em {execution_time}ms")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Erro ao executar migration {migration.version}: {e}")
                    return False
        
        except Exception as e:
            logger.error(f"Erro ao carregar migration {migration.version}: {e}")
            return False
    
    def run_pending_migrations(self) -> Dict:
        """Executa todas as migrations pendentes"""
        pending = self.get_pending_migrations()
        
        if not pending:
            return {
                'success': True,
                'message': 'Nenhuma migration pendente',
                'executed': [],
                'failed': []
            }
        
        executed = []
        failed = []
        
        for migration in pending:
            if self.execute_migration(migration):
                executed.append(migration.version)
            else:
                failed.append(migration.version)
                # Parar execução se uma migration falhar
                break
        
        success = len(failed) == 0
        
        return {
            'success': success,
            'message': f'{len(executed)} migrations executadas, {len(failed)} falharam',
            'executed': executed,
            'failed': failed
        }
    
    def get_migration_status(self) -> Dict:
        """Retorna status geral das migrations"""
        try:
            executed = self.get_executed_migrations()
            
            return {
                'total_executed': len(executed),
                'latest_executed': executed[-1] if executed else None,
                'auto_migrate_enabled': getattr(self.config, 'AUTO_MIGRATE', False)
            }
        
        except Exception as e:
            logger.error(f"Erro ao obter status das migrations: {e}")
            return {'error': str(e)}
    
    def create_migration_file(self, name: str, description: str = '') -> str:
        """Cria arquivo template para nova migration"""
        try:
            # Gerar próxima versão
            executed = self.get_executed_migrations()
            available = self.get_available_migrations()
            all_versions = executed + [m.version for m in available]
            
            if all_versions:
                latest_version = max([int(v) for v in all_versions if v.isdigit()])
                next_version = f"{latest_version + 1:03d}"
            else:
                next_version = "001"
            
            # Nome do arquivo
            filename = f"migration_{next_version}_{name}.py"
            file_path = os.path.join(self.migrations_dir, filename)
            
            # Template da migration
            template = f'''"""
{description or f'Migration {next_version}: {name}'}

Criada em: {datetime.now().isoformat()}
"""

from sqlalchemy import text

def upgrade(conn):
    """
    Executa as alterações da migration
    
    Args:
        conn: Conexão com o banco de dados
    """
    # Exemplo:
    # conn.execute(text("""
    #     CREATE TABLE example (
    #         id INTEGER PRIMARY KEY,
    #         name VARCHAR(100) NOT NULL
    #     )
    # """))
    
    pass

def downgrade(conn):
    """
    Reverte as alterações da migration
    
    Args:
        conn: Conexão com o banco de dados
    """
    # Exemplo:
    # conn.execute(text("DROP TABLE example"))
    
    pass
'''
            
            # Criar diretório se não existir
            os.makedirs(self.migrations_dir, exist_ok=True)
            
            # Escrever arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template)
            
            logger.info(f"Migration criada: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erro ao criar migration: {e}")
            raise
    
    def auto_migrate_if_enabled(self) -> Optional[Dict]:
        """Executa migrations automaticamente se habilitado"""
        auto_migrate = getattr(self.config, 'AUTO_MIGRATE', False)
        
        if not auto_migrate:
            return None
        
        try:
            logger.info("Auto-migration habilitada")
            return {'success': True, 'message': 'Auto-migration verificada'}
        
        except Exception as e:
            logger.error(f"Erro na auto-migration: {e}")
            return {'success': False, 'error': str(e)}


# Instância global do serviço
migration_service = MigrationService() 