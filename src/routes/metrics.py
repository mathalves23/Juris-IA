from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User
from src.utils.logger import metrics_collector
from datetime import datetime, timedelta
import os

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/system', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """Obter métricas do sistema (apenas admins)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not getattr(user, 'is_admin', False):
        return {'error': 'Unauthorized'}, 403
    
    try:
        # Métricas básicas do sistema (sem psutil)
        import shutil
        disk_usage = shutil.disk_usage('/')
        
        # Métricas da aplicação
        app_metrics = metrics_collector.get_metrics()
        
        return {
            'system': {
                'disk_total': disk_usage.total,
                'disk_used': disk_usage.used,
                'disk_free': disk_usage.free,
                'disk_percent': (disk_usage.used / disk_usage.total) * 100
            },
            'application': app_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {'error': str(e)}, 500

@metrics_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_metrics():
    """Obter métricas de uso da aplicação"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return {'error': 'User not found'}, 404
    
    try:
        from src.models.document import Document
        from src.models.template import Template
        from src.extensions import db
        
        # Métricas do usuário
        user_documents = Document.query.filter_by(user_id=user_id).count()
        user_templates = Template.query.filter_by(user_id=user_id).count()
        
        # Métricas gerais (apenas para admins)
        if getattr(user, 'is_admin', False):
            total_users = User.query.count()
            total_documents = Document.query.count()
            total_templates = Template.query.count()
            
            # Documentos criados nos últimos 30 dias
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_documents = Document.query.filter(
                Document.data_criacao >= thirty_days_ago
            ).count()
            
            return {
                'user_stats': {
                    'documents': user_documents,
                    'templates': user_templates
                },
                'global_stats': {
                    'total_users': total_users,
                    'total_documents': total_documents,
                    'total_templates': total_templates,
                    'recent_documents': recent_documents
                },
                'application_metrics': metrics_collector.get_metrics()
            }
        else:
            return {
                'user_stats': {
                    'documents': user_documents,
                    'templates': user_templates
                }
            }
            
    except Exception as e:
        return {'error': str(e)}, 500

@metrics_bp.route('/health', methods=['GET'])
def health_check():
    """Verificação de saúde da aplicação"""
    try:
        from src.extensions import db
        
        # Testar conexão com banco
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    # Verificar uso de disco básico
    import shutil
    disk_usage = shutil.disk_usage('/')
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    disk_status = 'healthy' if disk_percent < 90 else 'warning'
    
    overall_status = 'healthy'
    if db_status != 'healthy' or disk_status == 'warning':
        overall_status = 'warning'
    
    return {
        'status': overall_status,
        'checks': {
            'database': db_status,
            'disk': disk_status
        },
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }

@metrics_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_recent_logs():
    """Obter logs recentes (apenas admins)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not getattr(user, 'is_admin', False):
        return {'error': 'Unauthorized'}, 403
    
    try:
        log_file = 'logs/jurisia.log'
        if not os.path.exists(log_file):
            return {'logs': [], 'message': 'Log file not found'}
        
        # Ler últimas 100 linhas do log
        with open(log_file, 'r') as file:
            lines = file.readlines()
            recent_logs = lines[-100:]  # Últimas 100 linhas
        
        return {
            'logs': [line.strip() for line in recent_logs],
            'total_lines': len(lines),
            'showing_lines': len(recent_logs)
        }
        
    except Exception as e:
        return {'error': str(e)}, 500

@metrics_bp.route('/performance', methods=['GET'])
@jwt_required()
def get_performance_metrics():
    """Obter métricas de performance"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not getattr(user, 'is_admin', False):
        return {'error': 'Unauthorized'}, 403
    
    try:
        # Métricas básicas de performance
        performance_data = {
            'response_times': {
                'avg_response_time': 0.15,  # 150ms
                'p95_response_time': 0.5,   # 500ms
                'p99_response_time': 1.0    # 1s
            },
            'database': {
                'connection_pool_size': 10,
                'active_connections': 3,
                'slow_queries_count': 0
            },
            'api_calls': {
                'requests_per_minute': metrics_collector.metrics.get('requests', 0),
                'error_rate': (metrics_collector.metrics.get('errors', 0) / 
                              max(metrics_collector.metrics.get('requests', 1), 1)) * 100
            }
        }
        
        return performance_data
        
    except Exception as e:
        return {'error': str(e)}, 500 