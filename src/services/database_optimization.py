"""
Serviço de Otimização e Indexação Avançada do Banco de Dados
"""
from sqlalchemy import text, create_engine, inspect
from sqlalchemy.engine import Engine
from extensions import db
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    def __init__(self, engine: Engine = None):
        self.engine = engine or db.engine
        self.inspector = inspect(self.engine)
    
    def create_indexes(self):
        """Cria índices otimizados para performance"""
        indexes = [
            # Índices para tabela users
            {
                'table': 'users',
                'name': 'idx_users_email_active',
                'columns': ['email', 'ativo'],
                'unique': False
            },
            {
                'table': 'users',
                'name': 'idx_users_created_at',
                'columns': ['created_at'],
                'unique': False
            },
            {
                'table': 'users',
                'name': 'idx_users_last_login',
                'columns': ['last_login'],
                'unique': False
            },
            
            # Índices para documentos
            {
                'table': 'documents',
                'name': 'idx_documents_user_created',
                'columns': ['user_id', 'created_at'],
                'unique': False
            },
            {
                'table': 'documents',
                'name': 'idx_documents_title_search',
                'columns': ['title'],
                'unique': False
            },
            {
                'table': 'documents',
                'name': 'idx_documents_status_updated',
                'columns': ['status', 'updated_at'],
                'unique': False
            },
            
            # Índices para templates
            {
                'table': 'templates',
                'name': 'idx_templates_category_active',
                'columns': ['category', 'active'],
                'unique': False
            },
            {
                'table': 'templates',
                'name': 'idx_templates_name_search',
                'columns': ['name'],
                'unique': False
            },
            
            # Índices para clientes
            {
                'table': 'clients',
                'name': 'idx_clients_document_type',
                'columns': ['document_type'],
                'unique': False
            },
            {
                'table': 'clients',
                'name': 'idx_clients_name_search',
                'columns': ['name'],
                'unique': False
            },
            {
                'table': 'clients',
                'name': 'idx_clients_user_created',
                'columns': ['user_id', 'created_at'],
                'unique': False
            },
            
            # Índices para processos
            {
                'table': 'processes',
                'name': 'idx_processes_client_status',
                'columns': ['client_id', 'status'],
                'unique': False
            },
            {
                'table': 'processes',
                'name': 'idx_processes_case_number',
                'columns': ['case_number'],
                'unique': True
            },
            {
                'table': 'processes',
                'name': 'idx_processes_court_type',
                'columns': ['court_type'],
                'unique': False
            },
            
            # Índices para Kanban
            {
                'table': 'kanban_cards',
                'name': 'idx_kanban_cards_list_position',
                'columns': ['list_id', 'position'],
                'unique': False
            },
            {
                'table': 'kanban_cards',
                'name': 'idx_kanban_cards_assigned_user',
                'columns': ['assigned_user_id'],
                'unique': False
            },
            {
                'table': 'kanban_cards',
                'name': 'idx_kanban_cards_due_date',
                'columns': ['due_date'],
                'unique': False
            },
            
            # Índices para Wiki
            {
                'table': 'wiki_articles',
                'name': 'idx_wiki_articles_category_status',
                'columns': ['category_id', 'status'],
                'unique': False
            },
            {
                'table': 'wiki_articles',
                'name': 'idx_wiki_articles_title_search',
                'columns': ['title'],
                'unique': False
            },
            {
                'table': 'wiki_articles',
                'name': 'idx_wiki_articles_tags',
                'columns': ['tags'],
                'unique': False
            },
            
            # Índices para notificações
            {
                'table': 'notifications',
                'name': 'idx_notifications_user_read',
                'columns': ['user_id', 'is_read'],
                'unique': False
            },
            {
                'table': 'notifications',
                'name': 'idx_notifications_type_created',
                'columns': ['type', 'created_at'],
                'unique': False
            },
            
            # Índices para publicações
            {
                'table': 'publications',
                'name': 'idx_publications_date_court',
                'columns': ['publication_date', 'court'],
                'unique': False
            },
            {
                'table': 'publications',
                'name': 'idx_publications_processed',
                'columns': ['processed'],
                'unique': False
            }
        ]
        
        created_count = 0
        for index in indexes:
            if self._create_index(index):
                created_count += 1
        
        logger.info(f"✅ Criados {created_count} índices de otimização")
        return created_count
    
    def _create_index(self, index_config: Dict) -> bool:
        """Cria um índice específico"""
        try:
            table_name = index_config['table']
            index_name = index_config['name']
            columns = index_config['columns']
            unique = index_config.get('unique', False)
            
            # Verifica se tabela existe
            if not self.inspector.has_table(table_name):
                logger.warning(f"Tabela {table_name} não existe, pulando índice {index_name}")
                return False
            
            # Verifica se índice já existe
            existing_indexes = self.inspector.get_indexes(table_name)
            if any(idx['name'] == index_name for idx in existing_indexes):
                logger.debug(f"Índice {index_name} já existe")
                return False
            
            # Cria o índice
            columns_str = ', '.join(columns)
            unique_str = 'UNIQUE' if unique else ''
            
            sql = f"""
            CREATE {unique_str} INDEX IF NOT EXISTS {index_name} 
            ON {table_name} ({columns_str})
            """
            
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            
            logger.info(f"✓ Índice criado: {index_name} em {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar índice {index_config.get('name', 'unknown')}: {e}")
            return False
    
    def analyze_tables(self):
        """Analisa tabelas para estatísticas otimizadas"""
        try:
            tables = self.inspector.get_table_names()
            
            for table in tables:
                try:
                    # Para SQLite, usa ANALYZE
                    if 'sqlite' in str(self.engine.url):
                        with self.engine.connect() as conn:
                            conn.execute(text(f"ANALYZE {table}"))
                    
                    # Para PostgreSQL, usa ANALYZE VERBOSE
                    elif 'postgresql' in str(self.engine.url):
                        with self.engine.connect() as conn:
                            conn.execute(text(f"ANALYZE {table}"))
                    
                except Exception as e:
                    logger.warning(f"Erro ao analisar tabela {table}: {e}")
            
            logger.info(f"✅ Análise concluída para {len(tables)} tabelas")
            
        except Exception as e:
            logger.error(f"Erro na análise de tabelas: {e}")
    
    def vacuum_database(self):
        """Executa limpeza e compactação do banco"""
        try:
            if 'sqlite' in str(self.engine.url):
                with self.engine.connect() as conn:
                    conn.execute(text("VACUUM"))
                    logger.info("✅ VACUUM executado (SQLite)")
            
            elif 'postgresql' in str(self.engine.url):
                # PostgreSQL VACUUM precisa ser fora de transação
                with self.engine.connect() as conn:
                    conn.execute(text("COMMIT"))
                    conn.execute(text("VACUUM ANALYZE"))
                    logger.info("✅ VACUUM ANALYZE executado (PostgreSQL)")
            
        except Exception as e:
            logger.error(f"Erro no VACUUM: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do banco de dados"""
        stats = {
            'tables': {},
            'total_size': 0,
            'index_count': 0,
            'last_analysis': datetime.now().isoformat()
        }
        
        try:
            tables = self.inspector.get_table_names()
            
            for table_name in tables:
                table_stats = {
                    'columns': len(self.inspector.get_columns(table_name)),
                    'indexes': len(self.inspector.get_indexes(table_name)),
                    'foreign_keys': len(self.inspector.get_foreign_keys(table_name))
                }
                
                # Conta registros
                try:
                    with self.engine.connect() as conn:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        table_stats['row_count'] = result.scalar()
                except:
                    table_stats['row_count'] = 0
                
                stats['tables'][table_name] = table_stats
                stats['index_count'] += table_stats['indexes']
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return stats
    
    def optimize_queries(self):
        """Otimiza consultas comuns com views materializadas"""
        views = [
            {
                'name': 'user_document_stats',
                'sql': """
                CREATE VIEW IF NOT EXISTS user_document_stats AS
                SELECT 
                    u.id as user_id,
                    u.nome as user_name,
                    COUNT(d.id) as document_count,
                    COUNT(CASE WHEN d.status = 'draft' THEN 1 END) as draft_count,
                    COUNT(CASE WHEN d.status = 'published' THEN 1 END) as published_count,
                    MAX(d.updated_at) as last_document_update
                FROM users u
                LEFT JOIN documents d ON u.id = d.user_id
                GROUP BY u.id, u.nome
                """
            },
            {
                'name': 'client_process_summary',
                'sql': """
                CREATE VIEW IF NOT EXISTS client_process_summary AS
                SELECT 
                    c.id as client_id,
                    c.name as client_name,
                    c.document_number,
                    COUNT(p.id) as process_count,
                    COUNT(CASE WHEN p.status = 'active' THEN 1 END) as active_processes,
                    COUNT(CASE WHEN p.status = 'closed' THEN 1 END) as closed_processes,
                    MAX(p.updated_at) as last_update
                FROM clients c
                LEFT JOIN processes p ON c.id = p.client_id
                GROUP BY c.id, c.name, c.document_number
                """
            },
            {
                'name': 'kanban_board_stats',
                'sql': """
                CREATE VIEW IF NOT EXISTS kanban_board_stats AS
                SELECT 
                    b.id as board_id,
                    b.title as board_title,
                    COUNT(DISTINCT l.id) as list_count,
                    COUNT(c.id) as card_count,
                    COUNT(CASE WHEN c.due_date < datetime('now') THEN 1 END) as overdue_cards,
                    COUNT(CASE WHEN c.due_date >= datetime('now') AND c.due_date <= datetime('now', '+7 days') THEN 1 END) as due_soon_cards
                FROM kanban_boards b
                LEFT JOIN kanban_lists l ON b.id = l.board_id
                LEFT JOIN kanban_cards c ON l.id = c.list_id
                GROUP BY b.id, b.title
                """
            }
        ]
        
        created_views = 0
        for view in views:
            try:
                with self.engine.connect() as conn:
                    conn.execute(text(view['sql']))
                    conn.commit()
                    created_views += 1
                    logger.info(f"✓ View criada: {view['name']}")
            except Exception as e:
                logger.error(f"Erro ao criar view {view['name']}: {e}")
        
        logger.info(f"✅ {created_views} views de otimização criadas")
        return created_views
    
    def full_optimization(self):
        """Executa otimização completa do banco"""
        logger.info("🚀 Iniciando otimização completa do banco...")
        
        results = {
            'indexes_created': 0,
            'views_created': 0,
            'tables_analyzed': False,
            'vacuum_executed': False,
            'stats': {}
        }
        
        try:
            # 1. Criar índices
            results['indexes_created'] = self.create_indexes()
            
            # 2. Criar views otimizadas
            results['views_created'] = self.optimize_queries()
            
            # 3. Analisar tabelas
            self.analyze_tables()
            results['tables_analyzed'] = True
            
            # 4. Executar vacuum
            self.vacuum_database()
            results['vacuum_executed'] = True
            
            # 5. Obter estatísticas
            results['stats'] = self.get_database_stats()
            
            logger.info("✅ Otimização completa do banco finalizada")
            return results
            
        except Exception as e:
            logger.error(f"Erro na otimização completa: {e}")
            return results


# Instância global
db_optimizer = DatabaseOptimizer()

# Funções de conveniência
def optimize_database():
    """Função de conveniência para otimização completa"""
    return db_optimizer.full_optimization()

def create_database_indexes():
    """Função de conveniência para criar índices"""
    return db_optimizer.create_indexes()

def get_db_stats():
    """Função de conveniência para estatísticas"""
    return db_optimizer.get_database_stats() 