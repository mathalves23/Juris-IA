#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask, jsonify, request, g, current_app
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório raiz ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from src.extensions import db, jwt, cors, migrate, init_extensions, bcrypt
from src.config import config
from src.utils.logger import setup_logging, log_request, log_response, metrics_collector
from src.utils.backup_simple import BackupManager

# Importar sistemas de monitoramento e auditoria
try:
    from backend.src.services.monitoring_service import init_monitoring, monitor_request
    from backend.src.services.audit_service import init_audit_system, audit_logger, AuditEventType
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    print("Sistemas de monitoramento não disponíveis - continuando sem eles")

def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configuração
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Configurar logging
    setup_logging(app)
    app.logger.info(f"Starting Juris IA application in {config_name} mode")
    
    # Certificar que o diretório instance existe
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Inicializar extensões
    init_extensions(app)
    
    # Configurar backup manager
    backup_manager = BackupManager(app)
    app.extensions['backup_manager'] = backup_manager
    
    # Configurar middleware de segurança
    from src.middleware.security import security_middleware
    security_middleware.init_app(app)
    
    # Middleware para logging e métricas
    @app.before_request
    def before_request():
        log_request()
        metrics_collector.increment('requests')
        
        # Log user activity for metrics
        from flask_jwt_extended import get_jwt_identity
        try:
            if request.endpoint and request.endpoint != 'static':
                user_id = get_jwt_identity()
                if user_id:
                    metrics_collector.increment('users_active', user_id)
        except:
            pass  # JWT not required for this endpoint
    
    @app.after_request
    def after_request(response):
        log_response(response)
        
        # Count errors
        if response.status_code >= 400:
            metrics_collector.increment('errors')
        
        return response
    
    # Importar modelos
    from src.models.user import User
    from src.models.document import Document
    from src.models.template import Template
    from src.models.process import Process
    from src.models.client import Client
    from src.models.contract_analysis import ContractAnalysis
    # Importar novos modelos de segurança
    from src.models.user_security import (
        TokenBlacklist, LoginAttempt, PasswordResetToken, 
        EmailVerificationToken, UserSession
    )

    # Importar e registrar blueprints
    from src.routes.auth import auth_bp
    from src.routes.auth_secure import bp as auth_secure_bp  # Nova rota de autenticação segura
    from src.routes.documents import documents_bp
    from src.routes.templates import templates_bp
    from src.routes.ai import ai_bp
    from src.routes.clients import clients_bp
    from src.routes.wiki import wiki_bp
    from src.routes.notifications import notifications_bp
    from src.routes.metrics import metrics_bp
    from src.routes.contract_analyzer import bp as contract_analyzer_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(auth_secure_bp)  # Nova rota de autenticação segura
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(wiki_bp, url_prefix='/api')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
    app.register_blueprint(contract_analyzer_bp, url_prefix='/api/contract-analyzer')

    # Criar tabelas se não existirem
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tabelas criadas/verificadas com sucesso")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")

    # Rota de saúde
    @app.route('/api/health')
    def health_check():
        database_status = 'disconnected'
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine) 
            if inspector.has_table('users'):
                database_status = 'connected'
        except Exception as e:
            database_status = 'disconnected'
            app.logger.error(f"Database health check failed: {e}")
            
        return {
            'status': 'healthy',
            'version': '2.0.0',
            'database': database_status,
            'environment': config_name
        }
    
    # Rota de métricas admin
    @app.route('/api/admin/metrics')
    def get_metrics():
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        # Verificar se é admin
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or not getattr(user, 'is_admin', False):
                return {'error': 'Unauthorized'}, 403
        except:
            return {'error': 'Authentication required'}, 401
        
        return {
            'metrics': metrics_collector.get_metrics(),
            'backups': backup_manager.list_backups()[:5]  # Last 5 backups
        }
    
    # CLI Commands
    @app.cli.command()
    def create_backup():
        """Create database backup"""
        from src.utils.backup_simple import create_backup_command
        create_backup_command()
    
    @app.cli.command()
    def list_backups():
        """List available backups"""
        from src.utils.backup_simple import list_backups_command
        list_backups_command()
    
    @app.cli.command()
    def init_db():
        """Initialize database with sample data"""
        with app.app_context():
            db.create_all()
            
            # Criar usuário admin se não existir
            admin = User.query.filter_by(email='admin@jurisia.com').first()
            if not admin:
                admin = User(
                    nome='Administrador',
                    email='admin@jurisia.com',
                    senha_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                    is_admin=True,
                    email_verificado=True
                )
                db.session.add(admin)
                db.session.commit()
                app.logger.info('Admin user created: admin@jurisia.com / admin123')
    
    return app

# Criar uma instância global para as rotas
app = create_app()

# Rota raiz para teste
@app.route('/')
def index():
    return {"message": "Juris IA API está funcionando!", "version": "2.0.0"}

if __name__ == '__main__':
    try:
        print("🚀 Iniciando servidor Flask...")
        print("📁 Diretório atual:", os.getcwd())
        print("🐍 Python Path:", sys.path[0])
        
        app = create_app()
        
        print("🌐 Servidor rodando em: http://localhost:5005")
        print("📚 Documentação da API: http://localhost:5005/api")
        print("❤️  Status da aplicação: http://localhost:5005/api/health")
        print("\n✨ Para parar o servidor, pressione Ctrl+C")
        
        app.run(debug=True, host='0.0.0.0', port=5005)
        
    except Exception as e:
        print(f"💥 Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
