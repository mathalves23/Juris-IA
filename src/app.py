from flask import Flask, request, jsonify, make_response, make_response, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Flask
app = Flask(__name__)

# Configuração de CORS MUITO PERMISSIVA para produção
CORS(app, 
     resources={
         r"/api/*": {
             "origins": ["*"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": ["*"],
             "supports_credentials": True
         }
     }
)

# Configurações do Flask
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'jurisia-dev-key-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///jurisia.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configurações de APIs externas
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')
app.config['STRIPE_WEBHOOK_SECRET'] = os.getenv('STRIPE_WEBHOOK_SECRET')

# Inicializar extensões
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Headers de segurança para produção - CORS CORRIGIDO
@app.after_request
def after_request(response):
    # CORS Headers mais permissivos
    origin = request.headers.get('Origin')
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', '*')
    
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    
    # Security Headers apenas para produção
    if os.getenv('FLASK_ENV') == 'production':
        response.headers.add('X-Content-Type-Options', 'nosniff')
        response.headers.add('X-Frame-Options', 'SAMEORIGIN')  # Mudado de DENY para SAMEORIGIN
        response.headers.add('X-XSS-Protection', '1; mode=block')
    
    return response

# Lidar com preflight requests - MELHORADO
@app.before_request
def handle_preflight():
    from flask import request
    if request.method == "OPTIONS":
        from flask import make_response
        response = make_response()
        origin = request.headers.get('Origin')
        if origin:
            response.headers.add("Access-Control-Allow-Origin", origin)
        else:
            response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

# Importar modelos
from src.models.user import User
from src.models.document import Document
from src.models.template import Template
from src.models.notification import Notification
from src.models.wiki import WikiArticle
from src.models.kanban import KanbanBoard
# from src.models.analytics import Analytics

# Loader para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Registrar blueprints
def register_blueprints():
    from src.routes.auth import auth_bp
    from src.routes.documents import documents_bp
    from src.routes.templates import templates_bp
    from src.routes.ai import ai_bp
    from src.routes.analytics import analytics_bp
    from src.routes.notifications import notifications_bp
    from src.routes.wiki import wiki_bp
    from src.routes.contract_analyzer import bp as contract_analyzer_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(wiki_bp, url_prefix='/api/wiki')
    app.register_blueprint(contract_analyzer_bp, url_prefix='/api/contract-analyzer')

# Rota de health check
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'service': 'JurisIA API',
        'version': '2.0.0',
        'environment': os.getenv('FLASK_ENV', 'development')
    }

# === ROTAS DE TESTE PARA RESOLVER CORS ===
@app.route('/api/ai/generate', methods=['POST', 'OPTIONS'])
def api_ai_generate():
    """Rota de teste para IA sem autenticação"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response
    
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Teste IA')
        
        import time, random
        time.sleep(0.5)
        
        response_data = {
            "success": True,
            "generated_text": f"IA respondeu: {prompt}. Texto jurídico gerado com sucesso!",
            "confidence": 0.95
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = make_response(jsonify({"success": False, "error": str(e)}))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.route('/api/contract-analyzer/analyses', methods=['GET', 'OPTIONS'])
def api_contract_analyses():
    """Rota de teste para análises"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response
    
    try:
        response_data = {
            "success": True,
            "data": [
                {"id": 1, "title": "Contrato Teste", "status": "completed"}
            ]
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = make_response(jsonify({"success": False, "error": str(e)}))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.route('/api/contract-analyzer/stats', methods=['GET', 'OPTIONS'])
def api_contract_stats():
    """Rota de teste para estatísticas"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response
    
    try:
        response_data = {
            "success": True,
            "data": {
                "total_analyses": 10,
                "completed_analyses": 8
            }
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = make_response(jsonify({"success": False, "error": str(e)}))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

# Rota raiz
@app.route('/')
def root():
    return {
        'message': 'JurisIA API is running',
        'version': '2.0.0',
        'endpoints': {
            'auth': '/api/auth',
            'documents': '/api/documents', 
            'templates': '/api/templates',
            'ai': '/api/ai',
            'analytics': '/api/analytics',
            'notifications': '/api/notifications',
            'wiki': '/api/wiki',
            'health': '/health'
        }
    }

# Inicializar banco de dados
def create_tables():
    with app.app_context():
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")

if __name__ == '__main__':
    register_blueprints()
    create_tables()
    
    # Configurações para desenvolvimento e produção
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    port = int(os.getenv('PORT', 5000))
    
    print(f"🚀 Iniciando JurisIA API na porta {port}")
    print(f"🔧 Modo debug: {debug_mode}")
    print(f"🌍 CORS configurado para Netlify")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode) 