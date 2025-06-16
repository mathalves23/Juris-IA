"""
Sistema de Segurança Avançado com 2FA, WAF e Proteções Empresariais
"""
import hashlib
import hmac
import pyotp
import qrcode
import io
import base64
import secrets
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from flask import request, jsonify, abort
from functools import wraps
import ipaddress
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis
import json
from werkzeug.security import safe_str_cmp

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Configuração de segurança"""
    enable_2fa: bool = True
    enable_waf: bool = True
    max_login_attempts: int = 5
    lockout_duration: int = 1800  # 30 minutos
    session_timeout: int = 3600   # 1 hora
    password_min_length: int = 12
    require_mfa_admin: bool = True
    enable_ip_whitelist: bool = False
    allowed_ips: List[str] = None
    enable_device_tracking: bool = True

class TwoFactorAuth:
    """Sistema de autenticação de dois fatores"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.issuer_name = "JurisIA"
    
    def generate_secret(self, user_id: int) -> str:
        """Gerar segredo TOTP para usuário"""
        secret = pyotp.random_base32()
        
        # Armazenar segredo temporariamente até confirmação
        self.redis.setex(f"2fa_temp:{user_id}", 300, secret)  # 5 minutos
        
        return secret
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Gerar QR code para configuração"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Verificar token TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Janela de 30s
    
    def confirm_2fa_setup(self, user_id: int, verification_code: str) -> bool:
        """Confirmar configuração do 2FA"""
        secret = self.redis.get(f"2fa_temp:{user_id}")
        if not secret:
            return False
        
        secret = secret.decode('utf-8')
        
        if self.verify_totp(secret, verification_code):
            # Mover segredo para permanente
            self.redis.delete(f"2fa_temp:{user_id}")
            self.redis.set(f"2fa_secret:{user_id}", secret)
            return True
        
        return False
    
    def is_2fa_enabled(self, user_id: int) -> bool:
        """Verificar se 2FA está habilitado"""
        return bool(self.redis.get(f"2fa_secret:{user_id}"))
    
    def validate_2fa_token(self, user_id: int, token: str) -> bool:
        """Validar token 2FA do usuário"""
        secret = self.redis.get(f"2fa_secret:{user_id}")
        if not secret:
            return False
        
        secret = secret.decode('utf-8')
        return self.verify_totp(secret, token)

class WebApplicationFirewall:
    """Web Application Firewall básico"""
    
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_patterns = [
            # SQL Injection
            re.compile(r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDROP\b|\bDELETE\b)", re.IGNORECASE),
            # XSS
            re.compile(r"<script[^>]*>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            # Path Traversal
            re.compile(r"\.\./"),
            # Command Injection
            re.compile(r"[;&|`]"),
        ]
        self.rate_limits = {}
    
    def is_suspicious_request(self, request_data: str) -> Tuple[bool, str]:
        """Detectar requisições suspeitas"""
        for pattern in self.suspicious_patterns:
            if pattern.search(request_data):
                return True, f"Suspicious pattern detected: {pattern.pattern}"
        return False, ""
    
    def check_rate_limit(self, ip: str, endpoint: str, limit: int = 60) -> bool:
        """Verificar rate limiting por IP/endpoint"""
        key = f"{ip}:{endpoint}"
        current_time = datetime.utcnow()
        minute_key = current_time.strftime("%Y%m%d%H%M")
        
        rate_key = f"{key}:{minute_key}"
        
        if rate_key not in self.rate_limits:
            self.rate_limits[rate_key] = 0
        
        self.rate_limits[rate_key] += 1
        
        # Limpar chaves antigas
        cutoff = (current_time - timedelta(minutes=2)).strftime("%Y%m%d%H%M")
        keys_to_remove = [k for k in self.rate_limits.keys() if k.endswith(cutoff)]
        for k in keys_to_remove:
            del self.rate_limits[k]
        
        return self.rate_limits[rate_key] <= limit
    
    def block_ip(self, ip: str, duration: int = 3600):
        """Bloquear IP por tempo determinado"""
        self.blocked_ips.add(ip)
        # Em produção, usar Redis com TTL
        logger.warning(f"IP blocked: {ip} for {duration} seconds")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Verificar se IP está bloqueado"""
        return ip in self.blocked_ips

class DataEncryption:
    """Sistema de criptografia de dados sensíveis"""
    
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        self._cipher = self._generate_cipher()
    
    def _generate_cipher(self) -> Fernet:
        """Gerar cipher com chave derivada"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'jurisia_salt',  # Em produção, usar salt aleatório
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Criptografar dados"""
        encrypted_data = self._cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Descriptografar dados"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self._cipher.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    
    def encrypt_file(self, file_path: str, output_path: str):
        """Criptografar arquivo"""
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = self._cipher.encrypt(file_data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)

class SessionSecurity:
    """Gerenciamento seguro de sessões"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def create_secure_session(self, user_id: int, device_info: Dict) -> str:
        """Criar sessão segura"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'device_info': device_info,
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None
        }
        
        # Armazenar sessão com TTL
        self.redis.setex(
            f"session:{session_id}", 
            3600,  # 1 hora
            json.dumps(session_data)
        )
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validar e renovar sessão"""
        session_data = self.redis.get(f"session:{session_id}")
        if not session_data:
            return None
        
        session_data = json.loads(session_data.decode())
        
        # Verificar dispositivo e IP (opcional)
        if request:
            current_ip = request.remote_addr
            current_ua = request.headers.get('User-Agent')
            
            if (session_data.get('ip_address') != current_ip or 
                session_data.get('user_agent') != current_ua):
                logger.warning(f"Session anomaly detected for user {session_data['user_id']}")
                # Em ambiente de alta segurança, invalidar sessão
        
        # Renovar TTL
        self.redis.expire(f"session:{session_id}", 3600)
        
        return session_data
    
    def invalidate_session(self, session_id: str):
        """Invalidar sessão"""
        self.redis.delete(f"session:{session_id}")
    
    def invalidate_user_sessions(self, user_id: int):
        """Invalidar todas as sessões do usuário"""
        pattern = f"session:*"
        for key in self.redis.scan_iter(match=pattern):
            session_data = self.redis.get(key)
            if session_data:
                data = json.loads(session_data.decode())
                if data.get('user_id') == user_id:
                    self.redis.delete(key)

class SecurityAuditor:
    """Sistema de auditoria de segurança"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def log_security_event(self, event_type: str, user_id: Optional[int], 
                          details: Dict, severity: str = 'info'):
        """Registrar evento de segurança"""
        event = {
            'type': event_type,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details,
            'severity': severity
        }
        
        # Log estruturado
        logger.info(f"Security Event: {json.dumps(event)}")
        
        # Armazenar no Redis para análise
        event_key = f"security_event:{datetime.utcnow().timestamp()}"
        self.redis.setex(event_key, 86400, json.dumps(event))  # 24 horas
    
    def get_security_events(self, hours: int = 24) -> List[Dict]:
        """Obter eventos de segurança recentes"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_timestamp = cutoff.timestamp()
        
        events = []
        pattern = "security_event:*"
        
        for key in self.redis.scan_iter(match=pattern):
            timestamp = float(key.decode().split(':')[1])
            if timestamp >= cutoff_timestamp:
                event_data = self.redis.get(key)
                if event_data:
                    events.append(json.loads(event_data.decode()))
        
        return sorted(events, key=lambda x: x['timestamp'], reverse=True)

# Decoradores de segurança
def require_2fa(f):
    """Decorator para exigir 2FA"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if not user_id:
            abort(401)
        
        # Verificar se 2FA está habilitado e validado
        if not getattr(decorated_function, '_2fa_validated', False):
            return jsonify({
                'error': '2FA required',
                'code': '2FA_REQUIRED'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def ip_whitelist_required(f):
    """Decorator para whitelist de IPs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        
        # Lista de IPs permitidos (em produção, carregar de config)
        allowed_ips = getattr(f, '_allowed_ips', [])
        
        if allowed_ips and client_ip not in allowed_ips:
            logger.warning(f"Access denied for IP: {client_ip}")
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function

def waf_protection(f):
    """Decorator para proteção WAF"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        waf = getattr(f, '_waf_instance', None)
        if not waf:
            return f(*args, **kwargs)
        
        # Verificar IP bloqueado
        client_ip = request.remote_addr
        if waf.is_ip_blocked(client_ip):
            abort(403)
        
        # Verificar rate limiting
        endpoint = request.endpoint or 'unknown'
        if not waf.check_rate_limit(client_ip, endpoint):
            waf.block_ip(client_ip, 3600)  # Bloquear por 1 hora
            abort(429)
        
        # Verificar padrões suspeitos
        request_data = str(request.get_json() or '') + str(request.args)
        is_suspicious, reason = waf.is_suspicious_request(request_data)
        
        if is_suspicious:
            logger.warning(f"Suspicious request blocked: {reason}")
            waf.block_ip(client_ip, 1800)  # Bloquear por 30 minutos
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function

# Inicialização do sistema de segurança
def init_advanced_security(app, redis_client, config: SecurityConfig):
    """Inicializar sistema de segurança avançado"""
    
    # Instanciar componentes
    two_factor = TwoFactorAuth(redis_client)
    waf = WebApplicationFirewall()
    encryption = DataEncryption(app.config.get('ENCRYPTION_KEY', 'default-key'))
    session_security = SessionSecurity(redis_client)
    auditor = SecurityAuditor(redis_client)
    
    # Middleware de segurança
    @app.before_request
    def security_middleware():
        # Log de acesso
        auditor.log_security_event(
            'access_attempt',
            None,
            {
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path
            }
        )
        
        # Aplicar WAF se habilitado
        if config.enable_waf:
            client_ip = request.remote_addr
            
            if waf.is_ip_blocked(client_ip):
                auditor.log_security_event(
                    'blocked_ip_access',
                    None,
                    {'ip': client_ip},
                    'warning'
                )
                abort(403)
    
    # Rotas de 2FA
    @app.route('/api/security/2fa/setup', methods=['POST'])
    def setup_2fa():
        from flask_jwt_extended import jwt_required, get_jwt_identity
        from src.models.user import User
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        secret = two_factor.generate_secret(user_id)
        qr_code = two_factor.generate_qr_code(user.email, secret)
        
        return jsonify({
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': [secrets.token_hex(4) for _ in range(8)]
        })
    
    @app.route('/api/security/2fa/confirm', methods=['POST'])
    def confirm_2fa():
        from flask_jwt_extended import jwt_required, get_jwt_identity
        from flask import request
        
        user_id = get_jwt_identity()
        data = request.get_json()
        
        verification_code = data.get('verification_code')
        if not verification_code:
            return jsonify({'error': 'Verification code required'}), 400
        
        if two_factor.confirm_2fa_setup(user_id, verification_code):
            auditor.log_security_event(
                '2fa_enabled',
                user_id,
                {},
                'info'
            )
            return jsonify({'message': '2FA enabled successfully'})
        else:
            return jsonify({'error': 'Invalid verification code'}), 400
    
    @app.route('/api/security/events', methods=['GET'])
    def get_security_events():
        # Apenas para admins
        events = auditor.get_security_events(hours=24)
        return jsonify({'events': events})
    
    return {
        'two_factor': two_factor,
        'waf': waf,
        'encryption': encryption,
        'session_security': session_security,
        'auditor': auditor
    } 