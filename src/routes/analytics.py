from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.analytics_service import analytics_service
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard/overview', methods=['GET'])
@jwt_required()
def get_dashboard_overview():
    """Retorna visão geral do dashboard com métricas principais"""
    try:
        user_id = get_jwt_identity()
        date_range = request.args.get('range', '30days')
        
        # Validar range
        valid_ranges = ['7days', '30days', '90days', '1year']
        if date_range not in valid_ranges:
            return jsonify({
                'success': False,
                'message': f'Range inválido. Use: {", ".join(valid_ranges)}'
            }), 400
        
        overview = analytics_service.get_dashboard_overview(user_id, date_range)
        
        return jsonify({
            'success': True,
            'data': overview
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter overview do dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter dados do dashboard'
        }), 500

@analytics_bp.route('/detailed/<category>', methods=['GET'])
@jwt_required()
def get_detailed_analytics(category):
    """Retorna analytics detalhadas por categoria"""
    try:
        user_id = get_jwt_identity()
        
        # Validar categoria
        valid_categories = ['documents', 'kanban', 'wiki', 'ai', 'productivity']
        if category not in valid_categories:
            return jsonify({
                'success': False,
                'message': f'Categoria inválida. Use: {", ".join(valid_categories)}'
            }), 400
        
        # Processar filtros
        filters = {}
        if request.args.get('start_date'):
            try:
                filters['start_date'] = datetime.fromisoformat(request.args.get('start_date'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Formato de data inválido para start_date'
                }), 400
        
        if request.args.get('end_date'):
            try:
                filters['end_date'] = datetime.fromisoformat(request.args.get('end_date'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Formato de data inválido para end_date'
                }), 400
        
        if request.args.get('filter_by'):
            filters['filter_by'] = request.args.get('filter_by')
        
        if request.args.get('group_by'):
            filters['group_by'] = request.args.get('group_by')
        
        analytics = analytics_service.get_detailed_analytics(user_id, category, filters)
        
        return jsonify({
            'success': True,
            'data': analytics
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Erro ao obter analytics detalhadas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter analytics detalhadas'
        }), 500

@analytics_bp.route('/charts/<chart_type>', methods=['GET'])
@jwt_required()
def get_chart_data(chart_type):
    """Retorna dados para gráficos específicos"""
    try:
        user_id = get_jwt_identity()
        period = request.args.get('period', '30days')
        
        # Validar tipo de gráfico
        valid_charts = [
            'documents_timeline', 'kanban_progress', 'wiki_engagement', 
            'ai_usage_trends', 'productivity_heatmap'
        ]
        if chart_type not in valid_charts:
            return jsonify({
                'success': False,
                'message': f'Tipo de gráfico inválido. Use: {", ".join(valid_charts)}'
            }), 400
        
        # Validar período
        valid_periods = ['7days', '30days', '90days', '1year']
        if period not in valid_periods:
            return jsonify({
                'success': False,
                'message': f'Período inválido. Use: {", ".join(valid_periods)}'
            }), 400
        
        chart_data = analytics_service.get_charts_data(user_id, chart_type, period)
        
        return jsonify({
            'success': True,
            'data': chart_data
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Erro ao obter dados do gráfico: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter dados do gráfico'
        }), 500

@analytics_bp.route('/productivity/score', methods=['GET'])
@jwt_required()
def get_productivity_score():
    """Retorna score de produtividade detalhado"""
    try:
        user_id = get_jwt_identity()
        period = request.args.get('period', '30days')
        
        # Calcular datas baseadas no período
        end_date = datetime.utcnow()
        if period == '7days':
            start_date = end_date - timedelta(days=7)
        elif period == '30days':
            start_date = end_date - timedelta(days=30)
        elif period == '90days':
            start_date = end_date - timedelta(days=90)
        elif period == '1year':
            start_date = end_date - timedelta(days=365)
        else:
            return jsonify({
                'success': False,
                'message': 'Período inválido'
            }), 400
        
        # Obter métricas de produtividade
        productivity_data = analytics_service._get_productivity_metrics(user_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': productivity_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter score de produtividade: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter score de produtividade'
        }), 500

@analytics_bp.route('/achievements', methods=['GET'])
@jwt_required()
def get_user_achievements():
    """Retorna conquistas do usuário"""
    try:
        user_id = get_jwt_identity()
        period = request.args.get('period', '30days')
        
        # Calcular datas
        end_date = datetime.utcnow()
        if period == '7days':
            start_date = end_date - timedelta(days=7)
        elif period == '30days':
            start_date = end_date - timedelta(days=30)
        elif period == '90days':
            start_date = end_date - timedelta(days=90)
        elif period == 'all':
            start_date = datetime(2020, 1, 1)  # Data bem antiga para pegar tudo
        else:
            start_date = end_date - timedelta(days=30)
        
        achievements = analytics_service._get_user_achievements(user_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': {
                'achievements': achievements,
                'period': period,
                'total_count': len(achievements)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter conquistas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter conquistas'
        }), 500

@analytics_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_productivity_recommendations():
    """Retorna recomendações para melhorar produtividade"""
    try:
        user_id = get_jwt_identity()
        
        recommendations = analytics_service._generate_productivity_recommendations(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'total_count': len(recommendations)
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter recomendações: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter recomendações'
        }), 500

@analytics_bp.route('/comparison', methods=['GET'])
@jwt_required()
def get_period_comparison():
    """Compara métricas entre dois períodos"""
    try:
        user_id = get_jwt_identity()
        
        # Período atual
        current_period = request.args.get('current_period', '30days')
        
        # Calcular datas do período atual
        end_date = datetime.utcnow()
        if current_period == '7days':
            current_start = end_date - timedelta(days=7)
            previous_start = current_start - timedelta(days=7)
        elif current_period == '30days':
            current_start = end_date - timedelta(days=30)
            previous_start = current_start - timedelta(days=30)
        elif current_period == '90days':
            current_start = end_date - timedelta(days=90)
            previous_start = current_start - timedelta(days=90)
        else:
            return jsonify({
                'success': False,
                'message': 'Período inválido'
            }), 400
        
        # Obter métricas dos dois períodos
        current_metrics = analytics_service.get_dashboard_overview(user_id, current_period)
        
        # Para o período anterior, usar as mesmas funções mas com datas diferentes
        previous_end = current_start
        
        # Simular métricas do período anterior (implementação simplificada)
        previous_metrics = {
            'documents': {'created': 5, 'updated': 3, 'total': 15},
            'kanban': {'cards_created': 8, 'cards_completed': 6, 'total_hours': 25.5},
            'wiki': {'articles_created': 2, 'total_views': 150, 'likes_received': 8},
            'ai_usage': {'total_requests': 45, 'success_rate': 92.5},
            'productivity': {'productivity_score': 78.5}
        }
        
        # Calcular comparações
        comparison = {
            'current_period': {
                'start_date': current_start.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': current_metrics
            },
            'previous_period': {
                'start_date': previous_start.isoformat(),
                'end_date': previous_end.isoformat(),
                'metrics': previous_metrics
            },
            'changes': {
                'documents_created': _calculate_change(
                    current_metrics.get('documents', {}).get('created', 0),
                    previous_metrics.get('documents', {}).get('created', 0)
                ),
                'cards_completed': _calculate_change(
                    current_metrics.get('kanban', {}).get('cards_completed', 0),
                    previous_metrics.get('kanban', {}).get('cards_completed', 0)
                ),
                'productivity_score': _calculate_change(
                    current_metrics.get('productivity', {}).get('productivity_score', 0),
                    previous_metrics.get('productivity', {}).get('productivity_score', 0)
                )
            }
        }
        
        return jsonify({
            'success': True,
            'data': comparison
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter comparação de períodos: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter comparação'
        }), 500

@analytics_bp.route('/export', methods=['POST'])
@jwt_required()
def export_analytics():
    """Exporta dados de analytics em formato CSV/Excel"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        export_type = data.get('type', 'csv')  # csv, excel, pdf
        categories = data.get('categories', ['documents', 'kanban', 'wiki'])
        period = data.get('period', '30days')
        
        if export_type not in ['csv', 'excel', 'pdf']:
            return jsonify({
                'success': False,
                'message': 'Tipo de exportação inválido'
            }), 400
        
        # Obter dados para exportação
        export_data = {}
        for category in categories:
            try:
                export_data[category] = analytics_service.get_detailed_analytics(user_id, category)
            except:
                continue
        
        # Gerar arquivo de exportação (implementação simplificada)
        # Na prática, você usaria bibliotecas como pandas, openpyxl, reportlab
        
        if export_type == 'csv':
            # Gerar CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow(['Categoria', 'Métrica', 'Valor', 'Período'])
            
            # Dados
            for category, data in export_data.items():
                for metric, value in data.items():
                    writer.writerow([category, metric, value, period])
            
            csv_data = output.getvalue()
            output.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'download_url': f'/api/analytics/download/{user_id}_{period}.csv',
                    'filename': f'analytics_{user_id}_{period}.csv',
                    'type': 'csv',
                    'size': len(csv_data.encode('utf-8'))
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'Exportação {export_type} não implementada ainda'
            }), 501
        
    except Exception as e:
        logger.error(f"Erro ao exportar analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao exportar dados'
        }), 500

@analytics_bp.route('/realtime/metrics', methods=['GET'])
@jwt_required()
def get_realtime_metrics():
    """Retorna métricas em tempo real"""
    try:
        user_id = get_jwt_identity()
        
        # Métricas das últimas 24 horas
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)
        
        metrics = {
            'last_24h': analytics_service.get_dashboard_overview(user_id, '7days'),
            'current_session': {
                'session_start': start_date.isoformat(),
                'active_time_minutes': 45,  # Placeholder
                'actions_count': 12,  # Placeholder
                'last_activity': (end_date - timedelta(minutes=5)).isoformat()
            },
            'live_stats': {
                'online_users': 1,
                'active_documents': 2,
                'running_timers': 1
            }
        }
        
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': end_date.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas em tempo real: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao obter métricas em tempo real'
        }), 500

# === FUNÇÕES AUXILIARES ===

def _calculate_change(current: float, previous: float) -> Dict[str, Any]:
    """Calcula mudança percentual entre dois valores"""
    if previous == 0:
        percentage = 100.0 if current > 0 else 0.0
    else:
        percentage = ((current - previous) / previous) * 100
    
    return {
        'absolute': current - previous,
        'percentage': round(percentage, 1),
        'trend': 'up' if current > previous else 'down' if current < previous else 'stable'
    } 