from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

from src.services.auth_service import auth_service
from src.models.user import User
from src.config import Config

# Configurar rate limiting
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

bp = Blueprint('auth_secure', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)

@bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")  # Máximo 5 registros por minuto
def register():
    """Registro de usuário com verificação de email"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': 'MISSING_FIELD',
                    'message': f'Campo obrigatório: {field}'
                }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        
        # Validações básicas
        if len(password) < 8:
            return jsonify({
                'success': False,
                'error': 'WEAK_PASSWORD',
                'message': 'Senha deve ter pelo menos 8 caracteres'
            }), 400
        
        if '@' not in email or len(email) < 5:
            return jsonify({
                'success': False,
                'error': 'INVALID_EMAIL',
                'message': 'Email inválido'
            }), 400
        
        # Registrar usuário
        result = auth_service.register_user(email, password, name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Usuário registrado com sucesso',
                'email_sent': result.get('email_sent', False),
                'user_id': result['user_id']
            }), 201
        else:
            status_code = 409 if result['error'] == 'EMAIL_ALREADY_EXISTS' else 500
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Erro no registro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")  # Máximo 10 tentativas de login por minuto
def login():
    """Login de usuário com controle de tentativas"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'MISSING_CREDENTIALS',
                'message': 'Email e senha são obrigatórios'
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Autenticar usuário
        result = auth_service.authenticate_user(email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso',
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'user': result['user']
            }), 200
        else:
            # Diferentes códigos de status para diferentes erros
            status_codes = {
                'ACCOUNT_LOCKED': 423,  # Locked
                'EMAIL_NOT_VERIFIED': 403,  # Forbidden
                'INVALID_CREDENTIALS': 401,  # Unauthorized
                'AUTHENTICATION_FAILED': 500  # Server Error
            }
            
            status_code = status_codes.get(result['error'], 400)
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per minute")  # Máximo 3 solicitações por minuto
def forgot_password():
    """Solicita reset de senha"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'success': False,
                'error': 'MISSING_EMAIL',
                'message': 'Email é obrigatório'
            }), 400
        
        email = data['email'].lower().strip()
        
        # Solicitar reset
        result = auth_service.request_password_reset(email)
        
        # Sempre retornar sucesso para não vazar informações
        return jsonify({
            'success': True,
            'message': 'Se o email existir, você receberá instruções para redefinir a senha'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro em forgot-password: {str(e)}")
        return jsonify({
            'success': True,
            'message': 'Se o email existir, você receberá instruções para redefinir a senha'
        }), 200

@bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per minute")  # Máximo 5 tentativas por minuto
def reset_password():
    """Redefine senha usando token"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('token') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'MISSING_DATA',
                'message': 'Token e nova senha são obrigatórios'
            }), 400
        
        token = data['token']
        new_password = data['new_password']
        
        # Validar nova senha
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'error': 'WEAK_PASSWORD',
                'message': 'Nova senha deve ter pelo menos 8 caracteres'
            }), 400
        
        # Redefinir senha
        result = auth_service.reset_password(token, new_password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 400 if result['error'] == 'INVALID_TOKEN' else 500
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Erro em reset-password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/verify-email', methods=['POST'])
@limiter.limit("10 per minute")  # Máximo 10 verificações por minuto
def verify_email():
    """Verifica email usando token"""
    try:
        data = request.get_json()
        
        if not data.get('token'):
            return jsonify({
                'success': False,
                'error': 'MISSING_TOKEN',
                'message': 'Token é obrigatório'
            }), 400
        
        token = data['token']
        
        # Verificar email
        result = auth_service.verify_email(token)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 400 if result['error'] == 'INVALID_TOKEN' else 500
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Erro em verify-email: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/resend-verification', methods=['POST'])
@limiter.limit("3 per hour")  # Máximo 3 reenvios por hora
def resend_verification():
    """Reenvia email de verificação"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({
                'success': False,
                'error': 'MISSING_EMAIL',
                'message': 'Email é obrigatório'
            }), 400
        
        email = data['email'].lower().strip()
        
        # Buscar usuário
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Não revelar se o email existe
            return jsonify({
                'success': True,
                'message': 'Se o email existir e não estiver verificado, um novo link será enviado'
            }), 200
        
        if user.is_email_verified:
            return jsonify({
                'success': False,
                'error': 'ALREADY_VERIFIED',
                'message': 'Email já está verificado'
            }), 400
        
        # Criar novo token e enviar email
        from src.models.user_security import EmailVerificationToken
        from src.services.email_service import email_service
        
        if email_service.is_configured():
            token_obj = EmailVerificationToken.create_for_user(user.id, email)
            email_sent = email_service.send_email_verification(
                email, user.name, token_obj.token
            )
            
            if email_sent:
                return jsonify({
                    'success': True,
                    'message': 'Email de verificação reenviado'
                }), 200
        
        return jsonify({
            'success': False,
            'error': 'EMAIL_SEND_FAILED',
            'message': 'Erro ao enviar email'
        }), 500
        
    except Exception as e:
        logger.error(f"Erro em resend-verification: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Renova token de acesso"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verificar se usuário ainda existe e está ativo
        user = User.query.get(current_user_id)
        if not user or not user.is_email_verified:
            return jsonify({
                'success': False,
                'error': 'INVALID_USER',
                'message': 'Usuário inválido ou inativo'
            }), 401
        
        # Criar novo token de acesso
        from flask_jwt_extended import create_access_token
        from datetime import timedelta
        
        new_access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
        )
        
        return jsonify({
            'success': True,
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Erro em refresh: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout do usuário"""
    try:
        current_user_id = get_jwt_identity()
        
        # Fazer logout
        auth_service.logout_user(current_user_id)
        
        return jsonify({
            'success': True,
            'message': 'Logout realizado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro em logout: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtém informações do usuário atual"""
    try:
        current_user_id = get_jwt_identity()
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'Usuário não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'is_email_verified': user.is_email_verified,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'login_count': user.login_count or 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro em get_current_user: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

@bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")  # Máximo 5 mudanças por hora
def change_password():
    """Altera senha do usuário logado"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar dados
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': 'MISSING_DATA',
                'message': 'Senha atual e nova senha são obrigatórias'
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Validar nova senha
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'error': 'WEAK_PASSWORD',
                'message': 'Nova senha deve ter pelo menos 8 caracteres'
            }), 400
        
        # Buscar usuário
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'Usuário não encontrado'
            }), 404
        
        # Verificar senha atual
        from werkzeug.security import check_password_hash, generate_password_hash
        
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({
                'success': False,
                'error': 'INVALID_PASSWORD',
                'message': 'Senha atual incorreta'
            }), 400
        
        # Atualizar senha
        user.password_hash = generate_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        
        # Invalidar todas as sessões ativas
        from src.models.user_security import UserSession
        UserSession.query.filter_by(user_id=user.id, is_active=True).update({
            'is_active': False,
            'logout_at': datetime.utcnow()
        })
        
        from src.extensions import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso. Faça login novamente.'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro em change-password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Erro interno do servidor'
        }), 500

# Middleware para verificar tokens na blacklist
@bp.before_request
def check_token_blacklist():
    """Verifica se o token está na blacklist antes de processar requisições protegidas"""
    if request.endpoint and 'auth_secure' in request.endpoint:
        # Verificar apenas em rotas que precisam de autenticação
        protected_routes = ['refresh', 'logout', 'get_current_user', 'change_password']
        
        if any(route in request.endpoint for route in protected_routes):
            try:
                current_token = get_jwt()
                if current_token and auth_service.is_token_blacklisted(current_token['jti']):
                    return jsonify({
                        'success': False,
                        'error': 'TOKEN_BLACKLISTED',
                        'message': 'Token inválido'
                    }), 401
            except:
                # Se não conseguir verificar o token, continuar normalmente
                pass 