from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, and_, or_, desc, extract, text
from extensions import db
import logging
import json

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        pass
    
    def get_dashboard_overview(self, user_id: int, date_range: str = '30days') -> Dict[str, Any]:
        """Retorna visão geral do dashboard com métricas principais"""
        try:
            # Calcular período
            end_date = datetime.utcnow()
            if date_range == '7days':
                start_date = end_date - timedelta(days=7)
            elif date_range == '30days':
                start_date = end_date - timedelta(days=30)
            elif date_range == '90days':
                start_date = end_date - timedelta(days=90)
            elif date_range == '1year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            overview = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'range': date_range
                },
                'documents': self._get_documents_metrics(user_id, start_date, end_date),
                'kanban': self._get_kanban_metrics(user_id, start_date, end_date),
                'wiki': self._get_wiki_metrics(user_id, start_date, end_date),
                'ai_usage': self._get_ai_usage_metrics(user_id, start_date, end_date),
                'productivity': self._get_productivity_metrics(user_id, start_date, end_date),
                'notifications': self._get_notifications_metrics(user_id, start_date, end_date)
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Erro ao obter overview do dashboard: {str(e)}")
            raise
    
    def get_detailed_analytics(self, user_id: int, category: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Retorna analytics detalhadas por categoria"""
        try:
            if category == 'documents':
                return self._get_detailed_documents_analytics(user_id, filters)
            elif category == 'kanban':
                return self._get_detailed_kanban_analytics(user_id, filters)
            elif category == 'wiki':
                return self._get_detailed_wiki_analytics(user_id, filters)
            elif category == 'ai':
                return self._get_detailed_ai_analytics(user_id, filters)
            elif category == 'productivity':
                return self._get_detailed_productivity_analytics(user_id, filters)
            else:
                raise ValueError(f"Categoria de analytics não suportada: {category}")
                
        except Exception as e:
            logger.error(f"Erro ao obter analytics detalhadas: {str(e)}")
            raise
    
    def get_charts_data(self, user_id: int, chart_type: str, period: str = '30days') -> Dict[str, Any]:
        """Retorna dados para gráficos específicos"""
        try:
            if chart_type == 'documents_timeline':
                return self._get_documents_timeline_chart(user_id, period)
            elif chart_type == 'kanban_progress':
                return self._get_kanban_progress_chart(user_id, period)
            elif chart_type == 'wiki_engagement':
                return self._get_wiki_engagement_chart(user_id, period)
            elif chart_type == 'ai_usage_trends':
                return self._get_ai_usage_trends_chart(user_id, period)
            elif chart_type == 'productivity_heatmap':
                return self._get_productivity_heatmap(user_id, period)
            else:
                raise ValueError(f"Tipo de gráfico não suportado: {chart_type}")
                
        except Exception as e:
            logger.error(f"Erro ao obter dados do gráfico: {str(e)}")
            raise
    
    # === MÉTRICAS DE DOCUMENTOS ===
    
    def _get_documents_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Métricas de documentos"""
        try:
            from models.document import Document
            
            # Total de documentos criados no período
            documents_created = Document.query.filter(
                Document.usuario_id == user_id,
                Document.data_criacao.between(start_date, end_date)
            ).count()
            
            # Total de documentos atualizados no período
            documents_updated = Document.query.filter(
                Document.usuario_id == user_id,
                Document.data_modificacao.between(start_date, end_date),
                Document.data_criacao < start_date
            ).count()
            
            # Total geral de documentos do usuário
            total_documents = Document.query.filter(Document.usuario_id == user_id).count()
            
            # Documentos por tipo
            documents_by_type = db.session.query(
                Document.tipo,
                func.count(Document.id).label('count')
            ).filter(
                Document.usuario_id == user_id,
                Document.data_criacao.between(start_date, end_date)
            ).group_by(Document.tipo).all()
            
            # Tamanho médio dos documentos
            avg_size = db.session.query(
                func.avg(Document.tamanho)
            ).filter(
                Document.usuario_id == user_id,
                Document.data_criacao.between(start_date, end_date)
            ).scalar() or 0
            
            return {
                'created': documents_created,
                'updated': documents_updated,
                'total': total_documents,
                'by_type': [{'type': doc.tipo, 'count': doc.count} for doc in documents_by_type],
                'avg_size_kb': round(avg_size / 1024, 2) if avg_size else 0,
                'growth_rate': self._calculate_growth_rate(
                    Document, 'data_criacao', user_id, start_date, end_date
                )
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de documentos: {str(e)}")
            return {'created': 0, 'updated': 0, 'total': 0, 'by_type': [], 'avg_size_kb': 0, 'growth_rate': 0}
    
    # === MÉTRICAS DE KANBAN ===
    
    def _get_kanban_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Métricas do sistema Kanban"""
        try:
            from models.kanban import KanbanBoard, KanbanCard, KanbanTimeEntry
            
            # Boards do usuário
            user_boards = KanbanBoard.query.filter(
                or_(
                    KanbanBoard.owner_id == user_id,
                    KanbanBoard.team_ids.contains([user_id])
                )
            ).count()
            
            # Cards criados no período
            cards_created = KanbanCard.query.join(KanbanBoard).filter(
                or_(
                    KanbanBoard.owner_id == user_id,
                    KanbanBoard.team_ids.contains([user_id])
                ),
                KanbanCard.created_at.between(start_date, end_date)
            ).count()
            
            # Cards completados no período
            cards_completed = KanbanCard.query.join(KanbanBoard).filter(
                or_(
                    KanbanBoard.owner_id == user_id,
                    KanbanBoard.team_ids.contains([user_id])
                ),
                KanbanCard.completed_at.between(start_date, end_date)
            ).count()
            
            # Tempo total trabalhado
            total_time = db.session.query(
                func.sum(KanbanTimeEntry.duration_minutes)
            ).join(KanbanCard).join(KanbanBoard).filter(
                KanbanTimeEntry.user_id == user_id,
                KanbanTimeEntry.start_time.between(start_date, end_date)
            ).scalar() or 0
            
            # Horas faturáveis
            billable_hours = db.session.query(
                func.sum(KanbanTimeEntry.duration_minutes)
            ).join(KanbanCard).join(KanbanBoard).filter(
                KanbanTimeEntry.user_id == user_id,
                KanbanTimeEntry.is_billable == True,
                KanbanTimeEntry.start_time.between(start_date, end_date)
            ).scalar() or 0
            
            # Taxa de conclusão
            completion_rate = (cards_completed / cards_created * 100) if cards_created > 0 else 0
            
            return {
                'boards': user_boards,
                'cards_created': cards_created,
                'cards_completed': cards_completed,
                'completion_rate': round(completion_rate, 1),
                'total_hours': round(total_time / 60, 1) if total_time else 0,
                'billable_hours': round(billable_hours / 60, 1) if billable_hours else 0,
                'productivity_score': self._calculate_productivity_score(user_id, start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de Kanban: {str(e)}")
            return {
                'boards': 0, 'cards_created': 0, 'cards_completed': 0, 
                'completion_rate': 0, 'total_hours': 0, 'billable_hours': 0, 'productivity_score': 0
            }
    
    # === MÉTRICAS DE WIKI ===
    
    def _get_wiki_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Métricas da Wiki"""
        try:
            from models.wiki import WikiArticle, WikiComment, WikiLike
            
            # Artigos criados pelo usuário
            articles_created = WikiArticle.query.filter(
                WikiArticle.author_id == user_id,
                WikiArticle.created_at.between(start_date, end_date)
            ).count()
            
            # Visualizações dos artigos do usuário
            total_views = db.session.query(
                func.sum(WikiArticle.view_count)
            ).filter(
                WikiArticle.author_id == user_id
            ).scalar() or 0
            
            # Curtidas recebidas
            likes_received = db.session.query(
                func.count(WikiLike.id)
            ).join(WikiArticle).filter(
                WikiArticle.author_id == user_id,
                WikiLike.created_at.between(start_date, end_date)
            ).scalar() or 0
            
            # Comentários feitos pelo usuário
            comments_made = WikiComment.query.filter(
                WikiComment.author_id == user_id,
                WikiComment.created_at.between(start_date, end_date)
            ).count()
            
            # Artigo mais popular do usuário
            most_popular = WikiArticle.query.filter(
                WikiArticle.author_id == user_id
            ).order_by(desc(WikiArticle.view_count)).first()
            
            return {
                'articles_created': articles_created,
                'total_views': total_views,
                'likes_received': likes_received,
                'comments_made': comments_made,
                'most_popular_article': {
                    'title': most_popular.title,
                    'views': most_popular.view_count,
                    'likes': most_popular.like_count
                } if most_popular else None,
                'engagement_score': self._calculate_wiki_engagement_score(user_id, start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de Wiki: {str(e)}")
            return {
                'articles_created': 0, 'total_views': 0, 'likes_received': 0, 
                'comments_made': 0, 'most_popular_article': None, 'engagement_score': 0
            }
    
    # === MÉTRICAS DE IA ===
    
    def _get_ai_usage_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Métricas de uso da IA"""
        try:
            from models.ai_usage import AIUsageLog
            
            # Total de requests de IA
            total_requests = AIUsageLog.query.filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at.between(start_date, end_date)
            ).count()
            
            # Requests por tipo
            requests_by_type = db.session.query(
                AIUsageLog.request_type,
                func.count(AIUsageLog.id).label('count')
            ).filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at.between(start_date, end_date)
            ).group_by(AIUsageLog.request_type).all()
            
            # Tokens consumidos
            total_tokens = db.session.query(
                func.sum(AIUsageLog.tokens_used)
            ).filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at.between(start_date, end_date)
            ).scalar() or 0
            
            # Tempo médio de resposta
            avg_response_time = db.session.query(
                func.avg(AIUsageLog.response_time_ms)
            ).filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at.between(start_date, end_date)
            ).scalar() or 0
            
            # Taxa de sucesso
            successful_requests = AIUsageLog.query.filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.status == 'success',
                AIUsageLog.created_at.between(start_date, end_date)
            ).count()
            
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'by_type': [{'type': req.request_type, 'count': req.count} for req in requests_by_type],
                'total_tokens': total_tokens,
                'avg_response_time_ms': round(avg_response_time, 2) if avg_response_time else 0,
                'success_rate': round(success_rate, 1),
                'efficiency_score': self._calculate_ai_efficiency_score(user_id, start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de IA: {str(e)}")
            return {
                'total_requests': 0, 'by_type': [], 'total_tokens': 0, 
                'avg_response_time_ms': 0, 'success_rate': 0, 'efficiency_score': 0
            }
    
    # === MÉTRICAS DE PRODUTIVIDADE ===
    
    def _get_productivity_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Métricas de produtividade"""
        try:
            # Atividade por dia da semana
            weekday_activity = self._get_weekday_activity_pattern(user_id, start_date, end_date)
            
            # Atividade por hora do dia
            hourly_activity = self._get_hourly_activity_pattern(user_id, start_date, end_date)
            
            # Streak de atividade (dias consecutivos)
            activity_streak = self._calculate_activity_streak(user_id)
            
            # Score de produtividade geral
            productivity_score = self._calculate_overall_productivity_score(user_id, start_date, end_date)
            
            # Metas e conquistas
            achievements = self._get_user_achievements(user_id, start_date, end_date)
            
            return {
                'weekday_pattern': weekday_activity,
                'hourly_pattern': hourly_activity,
                'activity_streak': activity_streak,
                'productivity_score': productivity_score,
                'achievements': achievements,
                'recommendations': self._generate_productivity_recommendations(user_id)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de produtividade: {str(e)}")
            return {
                'weekday_pattern': [], 'hourly_pattern': [], 'activity_streak': 0, 
                'productivity_score': 0, 'achievements': [], 'recommendations': []
            }
    
    # === MÉTRICAS DE NOTIFICAÇÕES ===
    
    def _get_notifications_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Métricas de notificações"""
        try:
            from models.notification import Notification
            
            # Total de notificações recebidas
            total_received = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.created_at.between(start_date, end_date)
            ).count()
            
            # Total lidas
            total_read = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.is_read == True,
                Notification.created_at.between(start_date, end_date)
            ).count()
            
            # Taxa de leitura
            read_rate = (total_read / total_received * 100) if total_received > 0 else 0
            
            # Notificações por tipo
            by_type = db.session.query(
                Notification.type,
                func.count(Notification.id).label('count')
            ).filter(
                Notification.user_id == user_id,
                Notification.created_at.between(start_date, end_date)
            ).group_by(Notification.type).all()
            
            # Tempo médio para leitura
            avg_read_time = db.session.query(
                func.avg(
                    extract('epoch', Notification.read_at) - extract('epoch', Notification.created_at)
                )
            ).filter(
                Notification.user_id == user_id,
                Notification.is_read == True,
                Notification.created_at.between(start_date, end_date)
            ).scalar() or 0
            
            return {
                'total_received': total_received,
                'total_read': total_read,
                'read_rate': round(read_rate, 1),
                'by_type': [{'type': notif.type.value, 'count': notif.count} for notif in by_type],
                'avg_read_time_minutes': round(avg_read_time / 60, 1) if avg_read_time else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de notificações: {str(e)}")
            return {
                'total_received': 0, 'total_read': 0, 'read_rate': 0, 
                'by_type': [], 'avg_read_time_minutes': 0
            }
    
    # === MÉTODOS AUXILIARES ===
    
    def _calculate_growth_rate(self, model, date_field, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula taxa de crescimento"""
        try:
            period_days = (end_date - start_date).days
            previous_start = start_date - timedelta(days=period_days)
            
            current_count = model.query.filter(
                getattr(model, 'usuario_id', getattr(model, 'user_id', None)) == user_id,
                getattr(model, date_field).between(start_date, end_date)
            ).count()
            
            previous_count = model.query.filter(
                getattr(model, 'usuario_id', getattr(model, 'user_id', None)) == user_id,
                getattr(model, date_field).between(previous_start, start_date)
            ).count()
            
            if previous_count == 0:
                return 100.0 if current_count > 0 else 0.0
            
            return ((current_count - previous_count) / previous_count) * 100
            
        except Exception as e:
            logger.error(f"Erro ao calcular taxa de crescimento: {str(e)}")
            return 0.0
    
    def _calculate_productivity_score(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula score de produtividade"""
        try:
            # Implementar lógica de cálculo baseada em várias métricas
            # Por exemplo: cards completados, tempo trabalhado, deadlines cumpridos, etc.
            
            from models.kanban import KanbanCard, KanbanTimeEntry
            
            # Cards completados no prazo
            completed_on_time = KanbanCard.query.filter(
                KanbanCard.created_by == user_id,
                KanbanCard.status == 'completed',
                KanbanCard.completed_at.between(start_date, end_date),
                KanbanCard.completed_at <= KanbanCard.due_date
            ).count()
            
            # Total de cards com deadline
            total_with_deadline = KanbanCard.query.filter(
                KanbanCard.created_by == user_id,
                KanbanCard.status == 'completed',
                KanbanCard.completed_at.between(start_date, end_date),
                KanbanCard.due_date.isnot(None)
            ).count()
            
            # Horas trabalhadas
            hours_worked = db.session.query(
                func.sum(KanbanTimeEntry.duration_minutes)
            ).filter(
                KanbanTimeEntry.user_id == user_id,
                KanbanTimeEntry.start_time.between(start_date, end_date)
            ).scalar() or 0
            
            # Cálculo do score (0-100)
            deadline_score = (completed_on_time / total_with_deadline * 40) if total_with_deadline > 0 else 0
            activity_score = min(hours_worked / 2400 * 40, 40)  # 40 horas = score máximo de 40
            consistency_score = 20  # Placeholder para score de consistência
            
            return min(deadline_score + activity_score + consistency_score, 100)
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de produtividade: {str(e)}")
            return 0.0
    
    def _calculate_wiki_engagement_score(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula score de engajamento na wiki"""
        try:
            from models.wiki import WikiArticle, WikiComment, WikiLike
            
            # Artigos criados
            articles = WikiArticle.query.filter(
                WikiArticle.author_id == user_id,
                WikiArticle.created_at.between(start_date, end_date)
            ).count()
            
            # Comentários feitos
            comments = WikiComment.query.filter(
                WikiComment.author_id == user_id,
                WikiComment.created_at.between(start_date, end_date)
            ).count()
            
            # Curtidas dadas
            likes = WikiLike.query.filter(
                WikiLike.user_id == user_id,
                WikiLike.created_at.between(start_date, end_date)
            ).count()
            
            # Score baseado em atividade (0-100)
            score = min(articles * 20 + comments * 5 + likes * 2, 100)
            
            return score
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de engajamento: {str(e)}")
            return 0.0
    
    def _calculate_ai_efficiency_score(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calcula score de eficiência no uso da IA"""
        try:
            from models.ai_usage import AIUsageLog
            
            # Total de requests
            total_requests = AIUsageLog.query.filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at.between(start_date, end_date)
            ).count()
            
            if total_requests == 0:
                return 0.0
            
            # Requests bem-sucedidos
            successful = AIUsageLog.query.filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.status == 'success',
                AIUsageLog.created_at.between(start_date, end_date)
            ).count()
            
            # Score baseado na taxa de sucesso
            success_rate = (successful / total_requests) * 100
            
            return success_rate
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de eficiência da IA: {str(e)}")
            return 0.0
    
    def _get_weekday_activity_pattern(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Padrão de atividade por dia da semana"""
        try:
            # Implementar consulta que agregue atividade por dia da semana
            # Usando diferentes tabelas (documentos, kanban, wiki, etc.)
            
            weekdays = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            pattern = []
            
            for i, day in enumerate(weekdays):
                # Placeholder - implementar consulta real
                activity_count = 10 + i * 2  # Dados fictícios
                pattern.append({
                    'day': day,
                    'day_number': i + 1,
                    'activity_count': activity_count
                })
            
            return pattern
            
        except Exception as e:
            logger.error(f"Erro ao obter padrão de atividade semanal: {str(e)}")
            return []
    
    def _get_hourly_activity_pattern(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Padrão de atividade por hora do dia"""
        try:
            pattern = []
            
            for hour in range(24):
                # Placeholder - implementar consulta real
                activity_count = max(0, 10 - abs(hour - 14))  # Pico às 14h
                pattern.append({
                    'hour': hour,
                    'activity_count': activity_count
                })
            
            return pattern
            
        except Exception as e:
            logger.error(f"Erro ao obter padrão de atividade horário: {str(e)}")
            return []
    
    def _calculate_activity_streak(self, user_id: int) -> int:
        """Calcula sequência de dias consecutivos com atividade"""
        try:
            # Placeholder - implementar lógica real
            return 7  # 7 dias consecutivos
            
        except Exception as e:
            logger.error(f"Erro ao calcular sequência de atividade: {str(e)}")
            return 0
    
    def _calculate_overall_productivity_score(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Score geral de produtividade"""
        try:
            # Combinar diferentes scores
            kanban_score = self._calculate_productivity_score(user_id, start_date, end_date)
            wiki_score = self._calculate_wiki_engagement_score(user_id, start_date, end_date)
            ai_score = self._calculate_ai_efficiency_score(user_id, start_date, end_date)
            
            # Média ponderada
            overall = (kanban_score * 0.5 + wiki_score * 0.3 + ai_score * 0.2)
            
            return round(overall, 1)
            
        except Exception as e:
            logger.error(f"Erro ao calcular score geral: {str(e)}")
            return 0.0
    
    def _get_user_achievements(self, user_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Conquistas do usuário no período"""
        try:
            achievements = []
            
            # Verificar diferentes conquistas
            # Exemplo: "Criou primeiro artigo", "Completou 10 tarefas", etc.
            
            from models.wiki import WikiArticle
            from models.kanban import KanbanCard
            
            # Primeira publicação na wiki
            first_article = WikiArticle.query.filter(
                WikiArticle.author_id == user_id,
                WikiArticle.created_at.between(start_date, end_date)
            ).first()
            
            if first_article:
                achievements.append({
                    'id': 'first_article',
                    'title': 'Primeiro Artigo',
                    'description': 'Publicou seu primeiro artigo na base de conhecimento',
                    'icon': '📝',
                    'earned_at': first_article.created_at.isoformat()
                })
            
            # Tasks completadas
            completed_tasks = KanbanCard.query.filter(
                KanbanCard.created_by == user_id,
                KanbanCard.status == 'completed',
                KanbanCard.completed_at.between(start_date, end_date)
            ).count()
            
            if completed_tasks >= 10:
                achievements.append({
                    'id': 'task_master',
                    'title': 'Mestre das Tarefas',
                    'description': f'Completou {completed_tasks} tarefas no período',
                    'icon': '✅',
                    'earned_at': end_date.isoformat()
                })
            
            return achievements
            
        except Exception as e:
            logger.error(f"Erro ao obter conquistas: {str(e)}")
            return []
    
    def _generate_productivity_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Gera recomendações para melhorar produtividade"""
        try:
            recommendations = [
                {
                    'id': 'time_tracking',
                    'title': 'Ative o controle de tempo',
                    'description': 'Use o timer integrado para acompanhar o tempo gasto em cada tarefa',
                    'priority': 'high',
                    'category': 'time_management'
                },
                {
                    'id': 'daily_goals',
                    'title': 'Defina metas diárias',
                    'description': 'Estabeleça objetivos claros para cada dia de trabalho',
                    'priority': 'medium',
                    'category': 'goal_setting'
                },
                {
                    'id': 'knowledge_sharing',
                    'title': 'Compartilhe conhecimento',
                    'description': 'Publique artigos na wiki para ajudar colegas e clientes',
                    'priority': 'low',
                    'category': 'collaboration'
                }
            ]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {str(e)}")
            return []

# Instância global do serviço
analytics_service = AnalyticsService() 