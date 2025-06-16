from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import or_, and_
import logging
from extensions import db, socketio
from models.notification import Notification, NotificationType, NotificationPriority, NotificationTemplate, NotificationSettings
from models.user import User
from services.email_service import EmailService
import json

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.email_service = EmailService()
    
    def create_notification(self, user_id: int, title: str, message: str, 
                          type: NotificationType = NotificationType.INFO,
                          priority: NotificationPriority = NotificationPriority.MEDIUM,
                          **kwargs) -> Notification:
        """Cria uma nova notificação e a envia em tempo real"""
        try:
            # Criar notificação no banco
            notification = Notification.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                type=type,
                priority=priority,
                **kwargs
            )
            
            # Enviar em tempo real via WebSocket
            self._send_realtime_notification(notification)
            
            # Verificar se deve enviar por email
            if self._should_send_email(user_id, type):
                self._send_email_notification(notification)
            
            logger.info(f"Notificação criada: {notification.id} para usuário {user_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Erro ao criar notificação: {str(e)}")
            raise
    
    def create_from_template(self, template_name: str, user_id: int, **template_vars) -> Notification:
        """Cria notificação usando template"""
        try:
            template = NotificationTemplate.query.filter_by(
                name=template_name, 
                is_active=True
            ).first()
            
            if not template:
                raise ValueError(f"Template '{template_name}' não encontrado")
            
            return template.create_notification(user_id, **template_vars)
            
        except Exception as e:
            logger.error(f"Erro ao criar notificação por template: {str(e)}")
            raise
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False, 
                             limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Busca notificações do usuário com paginação"""
        try:
            query = Notification.query.filter_by(user_id=user_id, is_archived=False)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            # Total de notificações
            total = query.count()
            
            # Buscar com paginação
            notifications = query.order_by(Notification.created_at.desc())\
                                .offset(offset)\
                                .limit(limit)\
                                .all()
            
            # Contar não lidas
            unread_count = Notification.get_unread_count(user_id)
            
            return {
                'notifications': [n.to_dict() for n in notifications],
                'total': total,
                'unread_count': unread_count,
                'has_more': (offset + limit) < total
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar notificações: {str(e)}")
            raise
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Marca notificação como lida"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if not notification:
                return False
            
            notification.mark_as_read()
            
            # Atualizar contadores em tempo real
            self._update_unread_count(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao marcar notificação como lida: {str(e)}")
            return False
    
    def mark_all_as_read(self, user_id: int) -> bool:
        """Marca todas as notificações como lidas"""
        try:
            Notification.mark_all_as_read(user_id)
            
            # Atualizar contadores em tempo real
            self._update_unread_count(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao marcar todas como lidas: {str(e)}")
            return False
    
    def archive_notification(self, notification_id: int, user_id: int) -> bool:
        """Arquiva uma notificação"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if not notification:
                return False
            
            notification.archive()
            
            # Atualizar contadores em tempo real
            self._update_unread_count(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao arquivar notificação: {str(e)}")
            return False
    
    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Deleta uma notificação permanentemente"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if not notification:
                return False
            
            db.session.delete(notification)
            db.session.commit()
            
            # Atualizar contadores em tempo real
            self._update_unread_count(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar notificação: {str(e)}")
            return False
    
    def get_notification_settings(self, user_id: int) -> Dict[str, Any]:
        """Busca configurações de notificação do usuário"""
        try:
            settings = NotificationSettings.query.filter_by(user_id=user_id).first()
            
            if not settings:
                # Criar configurações padrão
                settings = NotificationSettings(user_id=user_id)
                db.session.add(settings)
                db.session.commit()
            
            return settings.to_dict()
            
        except Exception as e:
            logger.error(f"Erro ao buscar configurações: {str(e)}")
            raise
    
    def update_notification_settings(self, user_id: int, settings_data: Dict[str, Any]) -> bool:
        """Atualiza configurações de notificação"""
        try:
            settings = NotificationSettings.query.filter_by(user_id=user_id).first()
            
            if not settings:
                settings = NotificationSettings(user_id=user_id)
                db.session.add(settings)
            
            # Atualizar campos
            for key, value in settings_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configurações: {str(e)}")
            return False
    
    def create_bulk_notifications(self, notifications_data: List[Dict[str, Any]]) -> List[Notification]:
        """Cria múltiplas notificações em lote"""
        try:
            notifications = []
            
            for data in notifications_data:
                notification = Notification(**data)
                db.session.add(notification)
                notifications.append(notification)
            
            db.session.commit()
            
            # Enviar notificações em tempo real
            for notification in notifications:
                self._send_realtime_notification(notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Erro ao criar notificações em lote: {str(e)}")
            raise
    
    def cleanup_old_notifications(self, days: int = 30) -> int:
        """Remove notificações antigas"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Deletar notificações arquivadas antigas
            deleted = Notification.query.filter(
                and_(
                    Notification.is_archived == True,
                    Notification.created_at < cutoff_date
                )
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Removidas {deleted} notificações antigas")
            return deleted
            
        except Exception as e:
            logger.error(f"Erro ao limpar notificações antigas: {str(e)}")
            return 0
    
    # Métodos privados para WebSocket e email
    
    def _send_realtime_notification(self, notification: Notification):
        """Envia notificação em tempo real via WebSocket"""
        try:
            if socketio:
                # Enviar para o usuário específico
                socketio.emit(
                    'new_notification',
                    notification.to_dict(),
                    room=f'user_{notification.user_id}'
                )
                
                # Atualizar contador de não lidas
                self._update_unread_count(notification.user_id)
                
        except Exception as e:
            logger.error(f"Erro ao enviar notificação em tempo real: {str(e)}")
    
    def _update_unread_count(self, user_id: int):
        """Atualiza contador de notificações não lidas em tempo real"""
        try:
            if socketio:
                unread_count = Notification.get_unread_count(user_id)
                socketio.emit(
                    'unread_count_updated',
                    {'count': unread_count},
                    room=f'user_{user_id}'
                )
                
        except Exception as e:
            logger.error(f"Erro ao atualizar contador: {str(e)}")
    
    def _should_send_email(self, user_id: int, notification_type: NotificationType) -> bool:
        """Verifica se deve enviar notificação por email"""
        try:
            settings = NotificationSettings.query.filter_by(user_id=user_id).first()
            
            if not settings or not settings.email_enabled:
                return False
            
            # Verificar configurações específicas por tipo
            type_mapping = {
                NotificationType.LEGAL: settings.legal_notifications,
                NotificationType.TASK: settings.task_notifications,
                NotificationType.DOCUMENT: settings.document_notifications,
                NotificationType.AI: settings.ai_notifications,
                NotificationType.SYSTEM: settings.system_notifications,
            }
            
            return type_mapping.get(notification_type, True)
            
        except Exception as e:
            logger.error(f"Erro ao verificar configurações de email: {str(e)}")
            return False
    
    def _send_email_notification(self, notification: Notification):
        """Envia notificação por email"""
        try:
            user = User.query.get(notification.user_id)
            if not user or not user.email:
                return
            
            # Template de email para notificação
            subject = f"[JurisIA] {notification.title}"
            
            body = f"""
            <h2>{notification.title}</h2>
            <p>{notification.message}</p>
            
            {f'<p><a href="{notification.action_url}" style="background: #1890ff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">{notification.action_text}</a></p>' if notification.action_url else ''}
            
            <hr>
            <p><small>Esta é uma notificação automática do sistema JurisIA. Para alterar suas preferências de notificação, acesse seu perfil no sistema.</small></p>
            """
            
            self.email_service.send_email(
                to_email=user.email,
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de notificação: {str(e)}")


# Instância global do serviço
notification_service = NotificationService()


# Templates de notificação padrão
DEFAULT_NOTIFICATION_TEMPLATES = [
    {
        'name': 'document_created',
        'title_template': 'Documento "{document_name}" criado',
        'message_template': 'Um novo documento foi criado com sucesso: {document_name}',
        'type': NotificationType.DOCUMENT,
        'priority': NotificationPriority.LOW,
        'category': 'document'
    },
    {
        'name': 'document_shared',
        'title_template': 'Documento "{document_name}" compartilhado',
        'message_template': '{shared_by} compartilhou o documento "{document_name}" com você',
        'type': NotificationType.DOCUMENT,
        'priority': NotificationPriority.MEDIUM,
        'category': 'document'
    },
    {
        'name': 'ai_analysis_complete',
        'title_template': 'Análise de IA concluída',
        'message_template': 'A análise do documento "{document_name}" foi concluída com sucesso',
        'type': NotificationType.AI,
        'priority': NotificationPriority.MEDIUM,
        'category': 'ai'
    },
    {
        'name': 'deadline_approaching',
        'title_template': 'Prazo se aproximando',
        'message_template': 'O prazo para "{task_name}" vence em {days_remaining} dias',
        'type': NotificationType.WARNING,
        'priority': NotificationPriority.HIGH,
        'category': 'legal'
    },
    {
        'name': 'system_maintenance',
        'title_template': 'Manutenção programada',
        'message_template': 'O sistema entrará em manutenção em {maintenance_date}. Duração estimada: {duration}',
        'type': NotificationType.SYSTEM,
        'priority': NotificationPriority.MEDIUM,
        'category': 'system'
    }
]


def init_notification_templates():
    """Inicializa templates padrão de notificação"""
    try:
        for template_data in DEFAULT_NOTIFICATION_TEMPLATES:
            existing = NotificationTemplate.query.filter_by(
                name=template_data['name']
            ).first()
            
            if not existing:
                template = NotificationTemplate(**template_data)
                db.session.add(template)
        
        db.session.commit()
        logger.info("Templates de notificação inicializados")
        
    except Exception as e:
        logger.error(f"Erro ao inicializar templates: {str(e)}")
        db.session.rollback() 