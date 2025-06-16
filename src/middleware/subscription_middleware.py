"""
Middleware para controle de assinaturas e limites de uso
"""

from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from src.models.subscription import Subscription, PlanStatus
from src.models.user import User

def require_subscription(f):
    """Decorador que exige assinatura ativa"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            subscription = Subscription.query.filter(
                Subscription.user_id == user_id,
                Subscription.status.in_([PlanStatus.ACTIVE, PlanStatus.TRIAL])
            ).first()
            
            if not subscription or not subscription.is_active:
                return jsonify({
                    'error': 'Active subscription required',
                    'message': 'Esta funcionalidade requer uma assinatura ativa.',
                    'upgrade_required': True
                }), 403
            
            # Adicionar subscription ao request para uso posterior
            request.current_subscription = subscription
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Subscription verification failed'}), 500
    
    return decorated_function

def require_feature(feature_name):
    """Decorador que exige uma funcionalidade específica do plano"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                subscription = Subscription.query.filter(
                    Subscription.user_id == user_id,
                    Subscription.status.in_([PlanStatus.ACTIVE, PlanStatus.TRIAL])
                ).first()
                
                if not subscription or not subscription.is_active:
                    return jsonify({
                        'error': 'Active subscription required',
                        'message': 'Esta funcionalidade requer uma assinatura ativa.',
                        'upgrade_required': True
                    }), 403
                
                if not subscription.can_use_feature(feature_name):
                    return jsonify({
                        'error': 'Feature not available in your plan',
                        'feature': feature_name,
                        'current_plan': subscription.plan.name,
                        'message': f'A funcionalidade "{feature_name}" não está disponível no seu plano atual.',
                        'upgrade_required': True
                    }), 403
                
                request.current_subscription = subscription
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'error': 'Feature verification failed'}), 500
        
        return decorated_function
    return decorator

def check_usage_limit(usage_type):
    """Decorador que verifica limites de uso mensal"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                subscription = Subscription.query.filter(
                    Subscription.user_id == user_id,
                    Subscription.status.in_([PlanStatus.ACTIVE, PlanStatus.TRIAL])
                ).first()
                
                if not subscription or not subscription.is_active:
                    return jsonify({
                        'error': 'Active subscription required',
                        'message': 'Esta funcionalidade requer uma assinatura ativa.',
                        'upgrade_required': True
                    }), 403
                
                # Verificar limite de uso
                usage_check = subscription.check_usage_limit(usage_type)
                if not usage_check['allowed']:
                    return jsonify({
                        'error': 'Usage limit exceeded',
                        'usage_type': usage_type,
                        'used': usage_check['used'],
                        'limit': usage_check['limit'],
                        'message': f'Limite mensal de {usage_check["limit"]} {usage_type} excedido.',
                        'upgrade_required': True
                    }), 429
                
                # Executar função original
                result = f(*args, **kwargs)
                
                # Se a função foi executada com sucesso, incrementar uso
                if hasattr(result, 'status_code') and 200 <= result.status_code < 300:
                    subscription.increment_usage(usage_type)
                elif not hasattr(result, 'status_code'):
                    # Se não é uma Response, assumir sucesso
                    subscription.increment_usage(usage_type)
                
                request.current_subscription = subscription
                return result
                
            except Exception as e:
                return jsonify({'error': 'Usage limit verification failed'}), 500
        
        return decorated_function
    return decorator

def get_user_subscription():
    """Função helper para obter assinatura do usuário atual"""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        return Subscription.query.filter(
            Subscription.user_id == user_id,
            Subscription.status.in_([PlanStatus.ACTIVE, PlanStatus.TRIAL])
        ).first()
    except:
        return None
