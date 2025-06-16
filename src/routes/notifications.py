from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.extensions import db
from src.models.notification import Notification
from datetime import datetime
from services.notification_service import notification_service
from models.notification import NotificationType, NotificationPriority
import logging

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    """Busca notificações do usuário"""
    try:
        user_id = get_jwt_identity()
        
        # Parâmetros de query
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        
        result = notification_service.get_user_notifications(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar notificações: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar notificações'
        }), 500

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Retorna contador de notificações não lidas"""
    try:
        user_id = get_jwt_identity()
        
        from models.notification import Notification
        count = Notification.get_unread_count(user_id)
        
        return jsonify({
            'success': True,
            'data': {'count': count}
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar contador: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar contador'
        }), 500

@notifications_bp.route('/', methods=['POST'])
@jwt_required()
def create_notification():
    """Cria uma nova notificação (para admins/sistema)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validação básica
        if not data.get('title') or not data.get('message'):
            return jsonify({
                'success': False,
                'message': 'Título e mensagem são obrigatórios'
            }), 400
        
        # Determinar usuário de destino (por padrão o próprio usuário)
        target_user_id = data.get('user_id', user_id)
        
        # Converter strings para enums
        notification_type = NotificationType(data.get('type', 'info'))
        priority = NotificationPriority(data.get('priority', 'medium'))
        
        notification = notification_service.create_notification(
            user_id=target_user_id,
            title=data['title'],
            message=data['message'],
            type=notification_type,
            priority=priority,
            category=data.get('category'),
            action_url=data.get('action_url'),
            action_text=data.get('action_text'),
            expires_at=data.get('expires_at'),
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'success': True,
            'data': notification.to_dict(),
            'message': 'Notificação criada com sucesso'
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Valor inválido: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Erro ao criar notificação: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao criar notificação'
        }), 500

@notifications_bp.route('/<int:notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_as_read(notification_id):
    """Marca notificação como lida"""
    try:
        user_id = get_jwt_identity()
        
        success = notification_service.mark_as_read(notification_id, user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Notificação não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Notificação marcada como lida'
        })
        
    except Exception as e:
        logger.error(f"Erro ao marcar como lida: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao marcar notificação como lida'
        }), 500

@notifications_bp.route('/mark-all-read', methods=['PATCH'])
@jwt_required()
def mark_all_as_read():
    """Marca todas as notificações como lidas"""
    try:
        user_id = get_jwt_identity()
        
        success = notification_service.mark_all_as_read(user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Erro ao marcar todas como lidas'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Todas as notificações foram marcadas como lidas'
        })
        
    except Exception as e:
        logger.error(f"Erro ao marcar todas como lidas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao marcar todas as notificações como lidas'
        }), 500

@notifications_bp.route('/<int:notification_id>/archive', methods=['PATCH'])
@jwt_required()
def archive_notification(notification_id):
    """Arquiva uma notificação"""
    try:
        user_id = get_jwt_identity()
        
        success = notification_service.archive_notification(notification_id, user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Notificação não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Notificação arquivada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao arquivar notificação: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao arquivar notificação'
        }), 500

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Deleta uma notificação permanentemente"""
    try:
        user_id = get_jwt_identity()
        
        success = notification_service.delete_notification(notification_id, user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Notificação não encontrada'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Notificação deletada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao deletar notificação: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao deletar notificação'
        }), 500

@notifications_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Busca configurações de notificação do usuário"""
    try:
        user_id = get_jwt_identity()
        
        settings = notification_service.get_notification_settings(user_id)
        
        return jsonify({
            'success': True,
            'data': settings
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar configurações: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar configurações de notificação'
        }), 500

@notifications_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """Atualiza configurações de notificação do usuário"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos'
            }), 400
        
        success = notification_service.update_notification_settings(user_id, data)
        
        if not success:
            return jsonify({
                'success': False,
                'message': 'Erro ao atualizar configurações'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Configurações atualizadas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar configurações: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao atualizar configurações'
        }), 500

@notifications_bp.route('/bulk', methods=['POST'])
@jwt_required()
def create_bulk_notifications():
    """Cria múltiplas notificações em lote (admin)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Verificar se é admin (implementar verificação de role se necessário)
        notifications_data = data.get('notifications', [])
        
        if not notifications_data:
            return jsonify({
                'success': False,
                'message': 'Lista de notificações não fornecida'
            }), 400
        
        notifications = notification_service.create_bulk_notifications(notifications_data)
        
        return jsonify({
            'success': True,
            'data': [n.to_dict() for n in notifications],
            'message': f'{len(notifications)} notificações criadas com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar notificações em lote: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao criar notificações em lote'
        }), 500

@notifications_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_notification_stats():
    """Retorna estatísticas de notificações do usuário"""
    try:
        user_id = get_jwt_identity()
        
        from models.notification import Notification
        from sqlalchemy import func, and_
        from datetime import datetime, timedelta
        
        # Estatísticas básicas
        total = Notification.query.filter_by(user_id=user_id, is_archived=False).count()
        unread = Notification.get_unread_count(user_id)
        archived = Notification.query.filter_by(user_id=user_id, is_archived=True).count()
        
        # Estatísticas por tipo (últimos 30 dias)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        type_stats = db.session.query(
            Notification.type,
            func.count(Notification.id).label('count')
        ).filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= thirty_days_ago
            )
        ).group_by(Notification.type).all()
        
        # Estatísticas por prioridade (últimos 30 dias)
        priority_stats = db.session.query(
            Notification.priority,
            func.count(Notification.id).label('count')
        ).filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= thirty_days_ago
            )
        ).group_by(Notification.priority).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'unread': unread,
                'archived': archived,
                'read': total - unread,
                'by_type': {stat.type.value if stat.type else 'info': stat.count for stat in type_stats},
                'by_priority': {stat.priority.value if stat.priority else 'medium': stat.count for stat in priority_stats}
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar estatísticas'
        }), 500

@notifications_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_notification_templates():
    """Lista templates de notificação disponíveis"""
    try:
        from models.notification import NotificationTemplate
        
        templates = NotificationTemplate.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': t.id,
                'name': t.name,
                'title_template': t.title_template,
                'message_template': t.message_template,
                'type': t.type.value if t.type else 'info',
                'priority': t.priority.value if t.priority else 'medium',
                'category': t.category
            } for t in templates]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar templates: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao buscar templates'
        }), 500

# Funções utilitárias para criar notificações
def create_deadline_notification(user_id, titulo, mensagem, link=None, entity_type=None, entity_id=None):
    """Criar notificação de prazo"""
    try:
        notification = Notification(
            usuario_id=user_id,
            tipo='Prazo',
            titulo=titulo,
            mensagem=mensagem,
            link=link,
            prioridade='Alta',
            entidade_tipo=entity_type,
            entidade_id=entity_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar notificação: {e}")
        return None

def create_task_notification(user_id, titulo, mensagem, link=None, entity_type=None, entity_id=None):
    """Criar notificação de tarefa"""
    try:
        notification = Notification(
            usuario_id=user_id,
            tipo='Tarefa',
            titulo=titulo,
            mensagem=mensagem,
            link=link,
            prioridade='Normal',
            entidade_tipo=entity_type,
            entidade_id=entity_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar notificação: {e}")
        return None 