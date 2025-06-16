import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash

from src.extensions import db
from src.config import Config
from src.models.user import User
from src.models.user_security import (
    LoginAttempt, PasswordResetToken, EmailVerificationToken, 
    TokenBlacklist, UserSession
)
from src.services.email_service import email_service

class AuthService:
    """Serviço avançado de autenticação com recursos de segurança"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _get_client_info(self) -> Tuple[str, str]:
        """Obtém informações do cliente (IP e User-Agent)"""
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        return ip_address or 'unknown', user_agent
    
    def register_user(self, email: str, password: str, name: str, 
                     send_verification: bool = True) -> Dict[str, any]:
        """Registra novo usuário com verificação de email"""
        try:
            # Verificar se usuário já existe
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return {
                    'success': False,
                    'error': 'EMAIL_ALREADY_EXISTS',
                    'message': 'Email já está em uso'
                }
            
            # Criar usuário
            new_user = User(
                email=email,
                name=name,
                password_hash=generate_password_hash(password),
                is_email_verified=False,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_user)
            db.session.flush()  # Para obter o ID
            
            # Enviar email de verificação se solicitado
            verification_token = None
            if send_verification and email_service.is_configured():
                try:
                    token_obj = EmailVerificationToken.create_for_user(new_user.id, email)
                    verification_token = token_obj.token
                    
                    # Enviar email
                    email_sent = email_service.send_email_verification(
                        email, name, verification_token
                    )
                    
                    if not email_sent:
                        self.logger.warning(f"Falha ao enviar email de verificação para {email}")
                        
                except Exception as e:
                    self.logger.error(f"Erro ao criar token de verificação: {str(e)}")
            
            db.session.commit()
            
            self.logger.info(f"Usuário registrado com sucesso: {email}")
            
            return {
                'success': True,
                'user_id': new_user.id,
                'verification_token': verification_token,
                'email_sent': email_service.is_configured()
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao registrar usuário {email}: {str(e)}")
            return {
                'success': False,
                'error': 'REGISTRATION_FAILED',
                'message': 'Erro interno do servidor'
            }
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, any]:
        """Autentica usuário com controle de tentativas"""
        ip_address, user_agent = self._get_client_info()
        
        try:
            # Verificar se a conta está bloqueada
            if LoginAttempt.is_account_locked(email):
                LoginAttempt.record_attempt(
                    email, ip_address, user_agent, False, 'account_locked'
                )
                
                return {
                    'success': False,
                    'error': 'ACCOUNT_LOCKED',
                    'message': f'Conta temporariamente bloqueada. Tente novamente em {Config.LOCKOUT_DURATION // 60} minutos.'
                }
            
            # Buscar usuário
            user = User.query.filter_by(email=email).first()
            
            if not user:
                LoginAttempt.record_attempt(
                    email, ip_address, user_agent, False, 'user_not_found'
                )
                
                return {
                    'success': False,
                    'error': 'INVALID_CREDENTIALS',
                    'message': 'Email ou senha incorretos'
                }
            
            # Verificar senha
            if not check_password_hash(user.password_hash, password):
                LoginAttempt.record_attempt(
                    email, ip_address, user_agent, False, 'invalid_password'
                )
                
                return {
                    'success': False,
                    'error': 'INVALID_CREDENTIALS',
                    'message': 'Email ou senha incorretos'
                }
            
            # Verificar se o email foi verificado
            if not user.is_email_verified:
                LoginAttempt.record_attempt(
                    email, ip_address, user_agent, False, 'email_not_verified'
                )
                
                return {
                    'success': False,
                    'error': 'EMAIL_NOT_VERIFIED',
                    'message': 'Email não verificado. Verifique sua caixa de entrada.'
                }
            
            # Login bem-sucedido
            LoginAttempt.record_attempt(
                email, ip_address, user_agent, True
            )
            
            # Atualizar último login
            user.last_login = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            
            # Criar tokens JWT
            access_token = create_access_token(
                identity=str(user.id),
                expires_delta=timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
            )
            
            refresh_token = create_refresh_token(
                identity=str(user.id),
                expires_delta=timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES)
            )
            
            # Criar sessão de usuário
            session_token = Config.generate_secure_token()
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(user_session)
            
            db.session.commit()
            
            self.logger.info(f"Login bem-sucedido para {email}")
            
            return {
                'success': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'is_email_verified': user.is_email_verified,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                },
                'session_token': session_token
            }
            
        except Exception as e:
            self.logger.error(f"Erro na autenticação de {email}: {str(e)}")
            return {
                'success': False,
                'error': 'AUTHENTICATION_FAILED',
                'message': 'Erro interno do servidor'
            }
    
    def request_password_reset(self, email: str) -> Dict[str, any]:
        """Solicita reset de senha"""
        ip_address, user_agent = self._get_client_info()
        
        try:
            user = User.query.filter_by(email=email).first()
            
            # Sempre retornar sucesso para não vazar informações sobre usuários existentes
            if not user:
                return {
                    'success': True,
                    'message': 'Se o email existir, você receberá instruções para reset'
                }
            
            # Verificar se já há muitas solicitações recentes
            recent_tokens = PasswordResetToken.query.filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.created_at > datetime.utcnow() - timedelta(minutes=15),
                PasswordResetToken.used_at.is_(None)
            ).count()
            
            if recent_tokens >= 3:
                self.logger.warning(f"Muitas solicitações de reset para {email}")
                return {
                    'success': True,
                    'message': 'Se o email existir, você receberá instruções para reset'
                }
            
            # Criar token de reset
            reset_token = PasswordResetToken.create_for_user(
                user.id, ip_address, user_agent
            )
            
            # Enviar email se configurado
            if email_service.is_configured():
                email_sent = email_service.send_password_reset(
                    email, user.name, reset_token.token, ip_address, user_agent
                )
                
                if not email_sent:
                    self.logger.error(f"Falha ao enviar email de reset para {email}")
            
            self.logger.info(f"Token de reset criado para {email}")
            
            return {
                'success': True,
                'message': 'Se o email existir, você receberá instruções para reset'
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao solicitar reset para {email}: {str(e)}")
            return {
                'success': True,
                'message': 'Se o email existir, você receberá instruções para reset'
            }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, any]:
        """Redefine a senha usando token"""
        try:
            # Buscar token
            reset_token = PasswordResetToken.query.filter_by(token=token).first()
            
            if not reset_token or not reset_token.is_valid:
                return {
                    'success': False,
                    'error': 'INVALID_TOKEN',
                    'message': 'Token inválido ou expirado'
                }
            
            # Buscar usuário
            user = User.query.get(reset_token.user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'USER_NOT_FOUND',
                    'message': 'Usuário não encontrado'
                }
            
            # Atualizar senha
            user.password_hash = generate_password_hash(new_password)
            user.password_changed_at = datetime.utcnow()
            
            # Marcar token como usado
            reset_token.mark_as_used()
            
            # Invalidar todas as sessões ativas do usuário
            UserSession.query.filter_by(user_id=user.id, is_active=True).update({
                'is_active': False,
                'logout_at': datetime.utcnow()
            })
            
            db.session.commit()
            
            self.logger.info(f"Senha redefinida com sucesso para usuário {user.email}")
            
            return {
                'success': True,
                'message': 'Senha redefinida com sucesso'
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao redefinir senha: {str(e)}")
            return {
                'success': False,
                'error': 'RESET_FAILED',
                'message': 'Erro interno do servidor'
            }
    
    def verify_email(self, token: str) -> Dict[str, any]:
        """Verifica email usando token"""
        try:
            # Buscar token
            verification_token = EmailVerificationToken.query.filter_by(token=token).first()
            
            if not verification_token or not verification_token.is_valid:
                return {
                    'success': False,
                    'error': 'INVALID_TOKEN',
                    'message': 'Token inválido ou expirado'
                }
            
            # Buscar usuário
            user = User.query.get(verification_token.user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'USER_NOT_FOUND',
                    'message': 'Usuário não encontrado'
                }
            
            # Verificar email
            user.is_email_verified = True
            user.email_verified_at = datetime.utcnow()
            
            # Marcar token como verificado
            verification_token.mark_as_verified()
            
            db.session.commit()
            
            self.logger.info(f"Email verificado com sucesso para {user.email}")
            
            return {
                'success': True,
                'message': 'Email verificado com sucesso',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'is_email_verified': True
                }
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao verificar email: {str(e)}")
            return {
                'success': False,
                'error': 'VERIFICATION_FAILED',
                'message': 'Erro interno do servidor'
            }
    
    def blacklist_token(self, jti: str, token_type: str, user_id: int, expires_at: datetime):
        """Adiciona token à blacklist"""
        try:
            blacklisted_token = TokenBlacklist(
                jti=jti,
                token_type=token_type,
                user_id=user_id,
                expires_at=expires_at
            )
            
            db.session.add(blacklisted_token)
            db.session.commit()
            
            self.logger.info(f"Token {jti} adicionado à blacklist")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro ao adicionar token à blacklist: {str(e)}")
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Verifica se token está na blacklist"""
        return TokenBlacklist.query.filter_by(jti=jti).first() is not None
    
    def logout_user(self, user_id: int, session_token: Optional[str] = None):
        """Faz logout do usuário"""
        try:
            # Terminar sessão específica se fornecida
            if session_token:
                session = UserSession.query.filter_by(
                    user_id=user_id,
                    session_token=session_token,
                    is_active=True
                ).first()
                
                if session:
                    session.terminate()
            
            # Adicionar token atual à blacklist se existir
            current_token = get_jwt()
            if current_token:
                self.blacklist_token(
                    current_token['jti'],
                    current_token['type'],
                    user_id,
                    datetime.fromtimestamp(current_token['exp'])
                )
            
            self.logger.info(f"Logout realizado para usuário {user_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao fazer logout: {str(e)}")

# Instância global do serviço
auth_service = AuthService() 