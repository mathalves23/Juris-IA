from datetime import datetime
from src.extensions import db
import json

class Config(db.Model):
    """
    Modelo para armazenar configurações/flags da aplicação por ambiente
    """
    __tablename__ = 'configs'
    
    id = db.Column(db.Integer, primary_key=True)
    environment = db.Column(db.String(20), nullable=False, index=True)  # 'test' ou 'prod'
    key = db.Column(db.String(100), nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # 'string', 'boolean', 'integer', 'json'
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único para environment + key
    __table_args__ = (db.UniqueConstraint('environment', 'key', name='_environment_key_uc'),)
    
    def __init__(self, environment, key, value, value_type='string', description=None, user_id=None):
        self.environment = environment
        self.key = key
        self.value = value
        self.value_type = value_type
        self.description = description
        self.user_id = user_id
    
    def get_parsed_value(self):
        """
        Retorna o valor convertido para o tipo apropriado
        """
        if self.value is None:
            return None
            
        try:
            if self.value_type == 'boolean':
                return self.value.lower() in ['true', '1', 'yes', 'on']
            elif self.value_type == 'integer':
                return int(self.value)
            elif self.value_type == 'json':
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.value
    
    def set_value(self, value, value_type=None):
        """
        Define o valor e tipo automaticamente
        """
        if value_type:
            self.value_type = value_type
        elif isinstance(value, bool):
            self.value_type = 'boolean'
            self.value = str(value).lower()
        elif isinstance(value, int):
            self.value_type = 'integer'
            self.value = str(value)
        elif isinstance(value, (dict, list)):
            self.value_type = 'json'
            self.value = json.dumps(value)
        else:
            self.value_type = 'string'
            self.value = str(value)
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """
        Retorna o objeto como dicionário
        """
        return {
            'id': self.id,
            'environment': self.environment,
            'key': self.key,
            'value': self.get_parsed_value(),
            'value_type': self.value_type,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_config(environment, key, default=None):
        """
        Obtém uma configuração específica
        """
        config = Config.query.filter_by(environment=environment, key=key).first()
        if config:
            return config.get_parsed_value()
        return default
    
    @staticmethod
    def set_config(environment, key, value, user_id, description=None):
        """
        Define uma configuração
        """
        config = Config.query.filter_by(environment=environment, key=key).first()
        if config:
            config.set_value(value)
            config.user_id = user_id
            if description:
                config.description = description
        else:
            config = Config(
                environment=environment,
                key=key,
                value=str(value),
                user_id=user_id,
                description=description
            )
            config.set_value(value)
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @staticmethod
    def get_environment_configs(environment):
        """
        Obtém todas as configurações de um ambiente
        """
        configs = Config.query.filter_by(environment=environment).all()
        return {config.key: config.get_parsed_value() for config in configs}
    
    @staticmethod
    def get_flags(environment):
        """
        Obtém todas as configurações/flags de um ambiente específico
        Alias para get_environment_configs
        """
        return Config.get_environment_configs(environment)
    
    @staticmethod
    def set_flags_from_string(environment, flags_string, user_id):
        """
        Define múltiplas configurações a partir de uma string
        Formato: "key1=value1,key2=value2,key3=value3"
        """
        if not flags_string:
            return {}
        
        flags_dict = {}
        for flag_pair in flags_string.split(','):
            if '=' in flag_pair:
                key, value = flag_pair.strip().split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Determinar tipo automaticamente
                if value.lower() in ['true', 'false']:
                    typed_value = value.lower() == 'true'
                elif value.isdigit():
                    typed_value = int(value)
                else:
                    typed_value = value
                
                Config.set_config(environment, key, typed_value, user_id)
                flags_dict[key] = typed_value
        
        return flags_dict
    
    def __repr__(self):
        return f'<Config {self.environment}.{self.key}={self.value}>' 