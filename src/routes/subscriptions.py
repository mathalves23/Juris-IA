from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from decimal import Decimal

from src.models.subscription import Plan, Subscription, PlanType, PlanStatus, create_default_plans
from src.models.user import User
from src.extensions import db

bp = Blueprint('subscriptions', __name__, url_prefix='/api/subscriptions')

# Decorador para verificar acesso a funcionalidades
def require_feature(feature_name):
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            subscription = Subscription.query.filter_by(
                user_id=user_id,
                status__in=[PlanStatus.ACTIVE, PlanStatus.TRIAL]
            ).first()
            
            if not subscription or not subscription.can_use_feature(feature_name):
                return jsonify({
                    'error': 'Feature not available in your plan',
                    'feature': feature_name,
                    'upgrade_required': True
                }), 403
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Decorador para verificar limites de uso
def check_usage_limit(usage_type):
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            subscription = Subscription.query.filter_by(
                user_id=user_id,
                status__in=[PlanStatus.ACTIVE, PlanStatus.TRIAL]
            ).first()
            
            if not subscription:
                return jsonify({'error': 'No active subscription'}), 403
            
            usage_check = subscription.check_usage_limit(usage_type)
            if not usage_check['allowed']:
                return jsonify({
                    'error': 'Usage limit exceeded',
                    'usage_type': usage_type,
                    'limit_info': usage_check,
                    'upgrade_required': True
                }), 429
            
            # Incrementar uso após sucesso
            request.increment_usage = lambda: subscription.increment_usage(usage_type)
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@bp.route('/plans', methods=['GET'])
def get_plans():
    """Lista todos os planos disponíveis"""
    try:
        plans = Plan.query.filter_by(is_active=True).all()
        
        if not plans:
            # Criar planos padrão se não existirem
            plans = create_default_plans()
        
        return jsonify({
            'plans': [plan.to_dict() for plan in plans],
            'total': len(plans)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/plans/<int:plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Obter detalhes de um plano específico"""
    try:
        plan = Plan.query.get_or_404(plan_id)
        return jsonify(plan.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_subscription():
    """Obter assinatura atual do usuário"""
    try:
        user_id = get_jwt_identity()
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        
        if not subscription:
            return jsonify({
                'subscription': None,
                'has_subscription': False,
                'message': 'No subscription found'
            }), 200
        
        return jsonify({
            'subscription': subscription.to_dict(),
            'has_subscription': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/subscribe', methods=['POST'])
@jwt_required()
def create_subscription():
    """Criar nova assinatura"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validar dados
        plan_id = data.get('plan_id')
        is_annual = data.get('is_annual', False)
        payment_method = data.get('payment_method', 'credit_card')
        
        if not plan_id:
            return jsonify({'error': 'Plan ID is required'}), 400
        
        # Verificar se o plano existe
        plan = Plan.query.get(plan_id)
        if not plan or not plan.is_active:
            return jsonify({'error': 'Invalid or inactive plan'}), 400
        
        # Verificar se já tem assinatura ativa
        existing_subscription = Subscription.query.filter_by(
            user_id=user_id,
            status__in=[PlanStatus.ACTIVE, PlanStatus.TRIAL]
        ).first()
        
        if existing_subscription:
            return jsonify({
                'error': 'User already has an active subscription',
                'current_subscription': existing_subscription.to_dict()
            }), 400
        
        # Calcular valor
        amount = plan.price_annual if is_annual and plan.price_annual else plan.price_monthly
        
        # Criar assinatura com trial de 7 dias
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            is_annual=is_annual,
            trial_days=7
        )
        subscription.payment_method = payment_method
        subscription.amount_paid = amount
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription created successfully',
            'subscription': subscription.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/upgrade', methods=['POST'])
@jwt_required()
def upgrade_subscription():
    """Fazer upgrade da assinatura"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        new_plan_id = data.get('plan_id')
        
        if not new_plan_id:
            return jsonify({'error': 'New plan ID is required'}), 400
        
        # Buscar assinatura atual
        current_subscription = Subscription.query.filter_by(
            user_id=user_id,
            status__in=[PlanStatus.ACTIVE, PlanStatus.TRIAL]
        ).first()
        
        if not current_subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Verificar novo plano
        new_plan = Plan.query.get(new_plan_id)
        if not new_plan or not new_plan.is_active:
            return jsonify({'error': 'Invalid new plan'}), 400
        
        # Verificar se é realmente um upgrade (preço maior)
        current_price = current_subscription.plan.price_monthly
        new_price = new_plan.price_monthly
        
        if new_price <= current_price:
            return jsonify({'error': 'New plan must be an upgrade (higher price)'}), 400
        
        # Atualizar assinatura
        current_subscription.plan_id = new_plan_id
        current_subscription.updated_at = datetime.utcnow()
        
        # Calcular valor proporcional (simplificado)
        days_remaining = current_subscription.days_remaining
        daily_rate_old = float(current_price) / 30
        daily_rate_new = float(new_price) / 30
        prorated_amount = (daily_rate_new - daily_rate_old) * days_remaining
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription upgraded successfully',
            'subscription': current_subscription.to_dict(),
            'prorated_amount': round(prorated_amount, 2)
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancelar assinatura"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        reason = data.get('reason', 'User requested cancellation')
        
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            status__in=[PlanStatus.ACTIVE, PlanStatus.TRIAL]
        ).first()
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Cancelar no final do período atual (não imediatamente)
        subscription.status = PlanStatus.CANCELLED
        subscription.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription cancelled successfully',
            'subscription': subscription.to_dict(),
            'access_until': subscription.end_date.isoformat() if subscription.end_date else None
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/renew', methods=['POST'])
@jwt_required()
def renew_subscription():
    """Renovar assinatura"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        
        if not subscription:
            return jsonify({'error': 'No subscription found'}), 404
        
        # Renovar por mais um período
        if subscription.is_annual:
            subscription.end_date = datetime.utcnow() + timedelta(days=365)
        else:
            subscription.end_date = datetime.utcnow() + timedelta(days=30)
        
        subscription.status = PlanStatus.ACTIVE
        subscription.updated_at = datetime.utcnow()
        
        # Resetar contadores de uso
        subscription.monthly_documents_used = 0
        subscription.monthly_templates_used = 0
        subscription.monthly_ai_requests_used = 0
        subscription.last_usage_reset = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription renewed successfully',
            'subscription': subscription.to_dict()
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """Obter estatísticas de uso da assinatura"""
    try:
        user_id = get_jwt_identity()
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            status__in=[PlanStatus.ACTIVE, PlanStatus.TRIAL]
        ).first()
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Resetar contadores se necessário
        subscription.reset_monthly_usage()
        
        features = subscription.plan.features
        
        usage_stats = {
            'plan_info': {
                'name': subscription.plan.name,
                'is_trial': subscription.is_trial,
                'days_remaining': subscription.days_remaining
            },
            'documents': {
                'used': subscription.monthly_documents_used,
                'limit': features.monthly_documents,
                'percentage': (subscription.monthly_documents_used / features.monthly_documents * 100) if features.monthly_documents > 0 else 0
            },
            'templates': {
                'used': subscription.monthly_templates_used,
                'limit': features.monthly_templates,
                'percentage': (subscription.monthly_templates_used / features.monthly_templates * 100) if features.monthly_templates > 0 else 0
            },
            'ai_requests': {
                'used': subscription.monthly_ai_requests_used,
                'limit': features.monthly_ai_requests,
                'percentage': (subscription.monthly_ai_requests_used / features.monthly_ai_requests * 100) if features.monthly_ai_requests > 0 else 0
            },
            'storage': {
                'limit_gb': features.storage_gb,
                'users_limit': features.users_limit
            }
        }
        
        return jsonify(usage_stats), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/features', methods=['GET'])
@jwt_required()
def get_available_features():
    """Listar funcionalidades disponíveis no plano atual"""
    try:
        user_id = get_jwt_identity()
        subscription = Subscription.query.filter_by(
            user_id=user_id,
            status__in=[PlanStatus.ACTIVE, PlanStatus.TRIAL]
        ).first()
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        features = subscription.plan.features
        
        available_features = {
            'basic_features': {
                'document_creation': features.document_creation,
                'template_library': features.template_library,
                'basic_ai': features.basic_ai
            },
            'advanced_features': {
                'jurisprudence_analysis': features.jurisprudence_analysis,
                'deadline_prediction': features.deadline_prediction,
                'advanced_ai': features.advanced_ai,
                'contract_analysis': features.contract_analysis
            },
            'enterprise_features': {
                'executive_dashboard': features.executive_dashboard,
                'predictive_reports': features.predictive_reports,
                'business_intelligence': features.business_intelligence,
                'performance_metrics': features.performance_metrics,
                'microservices_access': features.microservices_access
            },
            'support_features': {
                'priority_support': features.priority_support,
                'api_access': features.api_access,
                'white_label': features.white_label,
                'custom_integrations': features.custom_integrations
            }
        }
        
        return jsonify({
            'plan_name': subscription.plan.name,
            'features': available_features
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoints para administração (futuro)
@bp.route('/admin/plans', methods=['POST'])
@jwt_required()
def create_plan():
    """Criar novo plano (admin only)"""
    # TODO: Implementar verificação de admin
    return jsonify({'message': 'Admin feature - not implemented yet'}), 501

@bp.route('/admin/subscriptions', methods=['GET'])
@jwt_required()
def list_all_subscriptions():
    """Listar todas as assinaturas (admin only)"""
    # TODO: Implementar verificação de admin
    return jsonify({'message': 'Admin feature - not implemented yet'}), 501

# Webhook para processamento de pagamentos (futuro)
@bp.route('/webhook/payment', methods=['POST'])
def payment_webhook():
    """Webhook para processamento de pagamentos"""
    # TODO: Implementar integração com Stripe/PagSeguro
    return jsonify({'message': 'Payment webhook - not implemented yet'}), 501 