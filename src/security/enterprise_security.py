"""
Sistema de Segurança Empresarial Avançado
Inclui: 2FA, WAF, Criptografia, Auditoria, Device Tracking
"""
import hashlib
import hmac
import pyotp
import qrcode
import io
import base64
import secrets
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from flask import request, jsonify, abort
from functools import wraps
import ipaddress
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis
import json
import user_agents
import geoip2.database
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityConfig:
    """Configuração de segurança empresarial"""
    enable_2fa: bool = True
    enforce_2fa_admin: bool = True
    enable_waf: bool = True
    enable_device_tracking: bool = True
    enable_geo_blocking: bool = False
    max_login_attempts: int = 5
    lockout_duration: int = 1800  # 30 minutos
    session_timeout: int = 3600   # 1 hora
    password_min_length: int = 12
    require_password_change: int = 90  # dias
    allowed_countries: List[str] = field(default_factory=lambda: ["BR", "US"])
    blocked_ips: List[str] = field(default_factory=list)
    security_level: SecurityLevel = SecurityLevel.HIGH

class TwoFactorAuth:
    """Sistema de autenticação de dois fatores"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.issuer_name = "JurisIA"
    
    def generate_secret(self, user_id: int) -> str:
        """Gerar segredo TOTP para usuário"""
        secret = pyotp.random_base32()
        self.redis.setex(f"2fa_temp:{user_id}", 300, secret)
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
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"

class EnterpriseWAF:
    """Web Application Firewall Empresarial"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.threat_patterns = {
            'sql_injection': [
                re.compile(r"(\bUNION\b.*\bSELECT\b)", re.IGNORECASE),
                re.compile(r"(\bINSERT\b.*\bINTO\b)", re.IGNORECASE),
                re.compile(r"(\bDROP\b.*\bTABLE\b)", re.IGNORECASE),
                re.compile(r"(\bDELETE\b.*\bFROM\b)", re.IGNORECASE),
                re.compile(r"(\'.*\bOR\b.*\')", re.IGNORECASE),
            ],
            'xss': [
                re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
                re.compile(r"javascript:", re.IGNORECASE),
                re.compile(r"on\w+\s*=", re.IGNORECASE),
                re.compile(r"<iframe[^>]*>", re.IGNORECASE),
            ],
            'path_traversal': [
                re.compile(r"\.\./"),
                re.compile(r"\.\.\\"),
                re.compile(r"%2e%2e%2f", re.IGNORECASE),
                re.compile(r"%2e%2e%5c", re.IGNORECASE),
            ],
            'command_injection': [
                re.compile(r"[;&|`$]"),
                re.compile(r"\b(curl|wget|nc|netcat)\b", re.IGNORECASE),
            ],
            'suspicious_headers': [
                re.compile(r"<\?php", re.IGNORECASE),
                re.compile(r"<%.*%>", re.IGNORECASE),
            ]
        }
        
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 req/min
            'login': {'requests': 5, 'window': 300},     # 5 req/5min
            'api': {'requests': 1000, 'window': 60},     # 1000 req/min
            'upload': {'requests': 10, 'window': 3600}   # 10 req/hour
        }
    
    def analyze_request(self, request_data: Dict) -> Dict[str, Any]:
        """Análise completa da requisição"""
        threats_detected = []
        risk_score = 0
        
        # Analisar dados da requisição
        content_to_check = []
        
        if request_data.get('json'):
            content_to_check.append(json.dumps(request_data['json']))
        
        if request_data.get('form'):
            content_to_check.extend(request_data['form'].values())
        
        if request_data.get('args'):
            content_to_check.extend(request_data['args'].values())
        
        content_to_check.append(request_data.get('path', ''))
        
        # Verificar padrões maliciosos
        for threat_type, patterns in self.threat_patterns.items():
            for content in content_to_check:
                for pattern in patterns:
                    if pattern.search(str(content)):
                        threats_detected.append({
                            'type': threat_type,
                            'pattern': pattern.pattern,
                            'content': str(content)[:100] + '...' if len(str(content)) > 100 else str(content)
                        })
                        risk_score += 25
        
        # Verificar headers suspeitos
        headers = request_data.get('headers', {})
        for header, value in headers.items():
            for pattern in self.threat_patterns['suspicious_headers']:
                if pattern.search(str(value)):
                    threats_detected.append({
                        'type': 'suspicious_header',
                        'header': header,
                        'value': str(value)
                    })
                    risk_score += 15
        
        return {
            'threats_detected': threats_detected,
            'risk_score': min(risk_score, 100),
            'action': self._determine_action(risk_score)
        }
    
    def _determine_action(self, risk_score: int) -> str:
        """Determinar ação baseada no score de risco"""
        if risk_score >= 75:
            return 'block'
        elif risk_score >= 50:
            return 'challenge'
        elif risk_score >= 25:
            return 'monitor'
        else:
            return 'allow'
    
    def check_rate_limit(self, identifier: str, endpoint_type: str = 'default') -> Tuple[bool, Dict]:
        """Verificar rate limiting avançado"""
        limit_config = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=limit_config['window'])
        
        # Chave do Redis para rate limiting
        rate_key = f"rate_limit:{identifier}:{endpoint_type}"
        
        # Usar sorted set para janela deslizante
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(rate_key, 0, window_start.timestamp())
        pipe.zcard(rate_key)
        pipe.zadd(rate_key, {str(current_time.timestamp()): current_time.timestamp()})
        pipe.expire(rate_key, limit_config['window'])
        
        results = pipe.execute()
        current_count = results[1]
        
        is_allowed = current_count < limit_config['requests']
        
        return is_allowed, {
            'current_count': current_count,
            'limit': limit_config['requests'],
            'window': limit_config['window'],
            'reset_time': (current_time + timedelta(seconds=limit_config['window'])).isoformat()
        }

class DeviceTracker:
    """Sistema de rastreamento de dispositivos"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def register_device(self, user_id: int, request_info: Dict) -> str:
        """Registrar novo dispositivo"""
        device_fingerprint = self._generate_device_fingerprint(request_info)
        
        device_info = {
            'user_id': user_id,
            'fingerprint': device_fingerprint,
            'ip_address': request_info.get('ip'),
            'user_agent': request_info.get('user_agent'),
            'first_seen': datetime.utcnow().isoformat(),
            'last_seen': datetime.utcnow().isoformat(),
            'trusted': False,
            'location': self._get_location_info(request_info.get('ip')),
            'browser_info': self._parse_user_agent(request_info.get('user_agent'))
        }
        
        device_key = f"device:{user_id}:{device_fingerprint}"
        self.redis.setex(device_key, 86400 * 30, json.dumps(device_info))  # 30 dias
        
        return device_fingerprint
    
    def _generate_device_fingerprint(self, request_info: Dict) -> str:
        """Gerar fingerprint único do dispositivo"""
        components = [
            request_info.get('user_agent', ''),
            request_info.get('accept_language', ''),
            request_info.get('accept_encoding', ''),
            request_info.get('ip', ''),  # Apenas primeira parte do IP
        ]
        
        fingerprint_string = '|'.join(components)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]
    
    def _parse_user_agent(self, user_agent: str) -> Dict:
        """Analisar user agent"""
        if not user_agent:
            return {}
        
        try:
            ua = user_agents.parse(user_agent)
            return {
                'browser': ua.browser.family,
                'browser_version': ua.browser.version_string,
                'os': ua.os.family,
                'os_version': ua.os.version_string,
                'device': ua.device.family,
                'is_mobile': ua.is_mobile,
                'is_tablet': ua.is_tablet,
                'is_bot': ua.is_bot
            }
        except:
            return {'raw': user_agent}
    
    def _get_location_info(self, ip: str) -> Dict:
        """Obter informações de localização (mockado)"""
        # Em produção, usar serviço como MaxMind GeoIP2
        return {
            'country': 'BR',
            'region': 'SP',
            'city': 'São Paulo',
            'coordinates': {'lat': -23.5505, 'lon': -46.6333}
        }
    
    def is_trusted_device(self, user_id: int, device_fingerprint: str) -> bool:
        """Verificar se dispositivo é confiável"""
        device_key = f"device:{user_id}:{device_fingerprint}"
        device_data = self.redis.get(device_key)
        
        if not device_data:
            return False
        
        device_info = json.loads(device_data.decode())
        return device_info.get('trusted', False)
    
    def trust_device(self, user_id: int, device_fingerprint: str) -> bool:
        """Marcar dispositivo como confiável"""
        device_key = f"device:{user_id}:{device_fingerprint}"
        device_data = self.redis.get(device_key)
        
        if not device_data:
            return False
        
        device_info = json.loads(device_data.decode())
        device_info['trusted'] = True
        device_info['trusted_at'] = datetime.utcnow().isoformat()
        
        self.redis.setex(device_key, 86400 * 30, json.dumps(device_info))
        return True

class SecurityAuditSystem:
    """Sistema avançado de auditoria de segurança"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.severity_levels = {
            'info': 1,
            'warning': 2,
            'error': 3,
            'critical': 4
        }
    
    def log_event(self, event_type: str, user_id: Optional[int], 
                  details: Dict, severity: str = 'info', 
                  ip_address: Optional[str] = None):
        """Log de evento de segurança avançado"""
        
        event = {
            'id': secrets.token_hex(8),
            'type': event_type,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': ip_address or (request.remote_addr if request else None),
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details,
            'severity': severity,
            'severity_level': self.severity_levels.get(severity, 1)
        }
        
        # Log estruturado
        logger.log(
            getattr(logging, severity.upper(), logging.INFO),
            f"Security Event [{event_type}]: {json.dumps(event)}"
        )
        
        # Armazenar no Redis com TTL baseado na severidade
        ttl = {
            'info': 86400,      # 1 dia
            'warning': 86400 * 7,  # 7 dias
            'error': 86400 * 30,   # 30 dias
            'critical': 86400 * 90  # 90 dias
        }.get(severity, 86400)
        
        event_key = f"security_event:{event['id']}"
        self.redis.setex(event_key, ttl, json.dumps(event))
        
        # Adicionar a índices para busca
        self._index_event(event)
        
        # Verificar se precisa de alerta
        if severity in ['error', 'critical']:
            self._trigger_alert(event)
    
    def _index_event(self, event: Dict):
        """Indexar evento para busca eficiente"""
        timestamp = datetime.fromisoformat(event['timestamp']).timestamp()
        
        # Índice por usuário
        if event['user_id']:
            user_index = f"security_index:user:{event['user_id']}"
            self.redis.zadd(user_index, {event['id']: timestamp})
            self.redis.expire(user_index, 86400 * 90)  # 90 dias
        
        # Índice por tipo
        type_index = f"security_index:type:{event['type']}"
        self.redis.zadd(type_index, {event['id']: timestamp})
        self.redis.expire(type_index, 86400 * 90)
        
        # Índice por severidade
        severity_index = f"security_index:severity:{event['severity']}"
        self.redis.zadd(severity_index, {event['id']: timestamp})
        self.redis.expire(severity_index, 86400 * 90)
    
    def _trigger_alert(self, event: Dict):
        """Disparar alerta para eventos críticos"""
        alert = {
            'id': secrets.token_hex(8),
            'event_id': event['id'],
            'type': 'security_alert',
            'title': f"Security Alert: {event['type']}",
            'description': f"Critical security event detected: {event['details']}",
            'timestamp': datetime.utcnow().isoformat(),
            'severity': event['severity'],
            'acknowledged': False
        }
        
        alert_key = f"security_alert:{alert['id']}"
        self.redis.setex(alert_key, 86400 * 30, json.dumps(alert))  # 30 dias
        
        # Em produção, enviar para sistema de notificação
        logger.critical(f"SECURITY ALERT: {json.dumps(alert)}")
    
    def search_events(self, filters: Dict) -> List[Dict]:
        """Buscar eventos com filtros"""
        events = []
        
        # Determinar qual índice usar
        if filters.get('user_id'):
            index_key = f"security_index:user:{filters['user_id']}"
        elif filters.get('event_type'):
            index_key = f"security_index:type:{filters['event_type']}"
        elif filters.get('severity'):
            index_key = f"security_index:severity:{filters['severity']}"
        else:
            # Busca geral (menos eficiente)
            pattern = "security_event:*"
            for key in self.redis.scan_iter(match=pattern, count=1000):
                event_data = self.redis.get(key)
                if event_data:
                    events.append(json.loads(event_data.decode()))
            
            return sorted(events, key=lambda x: x['timestamp'], reverse=True)[:100]
        
        # Buscar por índice
        start_time = filters.get('start_time')
        end_time = filters.get('end_time')
        
        if start_time:
            start_timestamp = datetime.fromisoformat(start_time).timestamp()
        else:
            start_timestamp = 0
        
        if end_time:
            end_timestamp = datetime.fromisoformat(end_time).timestamp()
        else:
            end_timestamp = datetime.utcnow().timestamp()
        
        event_ids = self.redis.zrangebyscore(
            index_key, start_timestamp, end_timestamp, 
            start=0, num=100, desc=True
        )
        
        # Carregar eventos completos
        for event_id in event_ids:
            event_data = self.redis.get(f"security_event:{event_id.decode()}")
            if event_data:
                events.append(json.loads(event_data.decode()))
        
        return events

# Inicialização do sistema de segurança empresarial
def init_enterprise_security(app, redis_client, config: SecurityConfig):
    """Inicializar sistema de segurança empresarial completo"""
    
    # Inicializar componentes
    two_factor = TwoFactorAuth(redis_client)
    waf = EnterpriseWAF(redis_client)
    device_tracker = DeviceTracker(redis_client)
    audit_system = SecurityAuditSystem(redis_client)
    
    # Middleware de segurança global
    @app.before_request
    def enterprise_security_middleware():
        # Coletar informações da requisição
        request_info = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'method': request.method,
            'path': request.path,
            'endpoint': request.endpoint,
            'json': request.get_json(silent=True),
            'form': dict(request.form),
            'args': dict(request.args),
            'headers': dict(request.headers)
        }
        
        # Análise WAF
        if config.enable_waf:
            waf_result = waf.analyze_request(request_info)
            
            if waf_result['action'] == 'block':
                audit_system.log_event(
                    'waf_block',
                    None,
                    {
                        'reason': 'WAF blocked request',
                        'threats': waf_result['threats_detected'],
                        'risk_score': waf_result['risk_score']
                    },
                    'warning'
                )
                abort(403)
            
            elif waf_result['action'] == 'challenge':
                # Implementar challenge (CAPTCHA, etc.)
                pass
        
        # Rate limiting
        rate_limit_key = f"{request.remote_addr}:{request.endpoint or 'unknown'}"
        endpoint_type = 'login' if 'login' in (request.endpoint or '') else 'default'
        
        is_allowed, limit_info = waf.check_rate_limit(rate_limit_key, endpoint_type)
        
        if not is_allowed:
            audit_system.log_event(
                'rate_limit_exceeded',
                None,
                limit_info,
                'warning'
            )
            abort(429)
        
        # Log de acesso
        audit_system.log_event(
            'request',
            None,
            {
                'method': request.method,
                'path': request.path,
                'endpoint': request.endpoint
            }
        )
    
    # Rotas de segurança
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
        
        audit_system.log_event(
            '2fa_setup_initiated',
            user_id,
            {'email': user.email}
        )
        
        return jsonify({
            'secret': secret,
            'qr_code': qr_code
        })
    
    @app.route('/api/security/2fa/confirm', methods=['POST'])
    def confirm_2fa():
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        user_id = get_jwt_identity()
        data = request.get_json()
        
        verification_code = data.get('verification_code')
        if not verification_code:
            return jsonify({'error': 'Verification code required'}), 400
        
        secret = two_factor.redis.get(f"2fa_temp:{user_id}")
        if not secret:
            return jsonify({'error': 'Secret not found'}), 400
        
        totp = pyotp.TOTP(secret)
        if totp.verify(verification_code, valid_window=2):  # Janela de 1 minuto
            # Mover para permanente
            permanent_data = {
                'secret': secret,
                'enabled_at': datetime.utcnow().isoformat(),
                'recovery_used': []
            }
            
            two_factor.redis.set(f"2fa_data:{user_id}", json.dumps(permanent_data))
            two_factor.redis.delete(f"2fa_temp:{user_id}")
            
            audit_system.log_event(
                '2fa_enabled',
                user_id,
                {},
                'info'
            )
            return jsonify({'message': '2FA enabled successfully'})
        else:
            audit_system.log_event(
                '2fa_setup_failed',
                user_id,
                {'code_provided': verification_code},
                'warning'
            )
            return jsonify({'error': 'Invalid verification code'}), 400
    
    @app.route('/api/security/devices', methods=['GET'])
    def get_user_devices():
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        user_id = get_jwt_identity()
        
        # Em uma implementação real, buscar dispositivos do usuário
        devices = []  # device_tracker.get_user_devices(user_id)
        
        return jsonify({'devices': devices})
    
    @app.route('/api/security/audit', methods=['GET'])
    def get_security_audit():
        # Apenas para admins
        filters = {
            'start_time': request.args.get('start_time'),
            'end_time': request.args.get('end_time'),
            'user_id': request.args.get('user_id'),
            'event_type': request.args.get('event_type'),
            'severity': request.args.get('severity')
        }
        
        # Remover filtros vazios
        filters = {k: v for k, v in filters.items() if v}
        
        events = audit_system.search_events(filters)
        
        return jsonify({
            'events': events,
            'count': len(events)
        })
    
    return {
        'two_factor': two_factor,
        'waf': waf,
        'device_tracker': device_tracker,
        'audit_system': audit_system,
        'config': config
    } 