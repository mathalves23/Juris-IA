from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from ..extensions import db

class PlanType(Enum):
    BASICO_MENSAL = "basico_mensal"
    INTERMEDIARIO_MENSAL = "intermediario_mensal"
    PROFISSIONAL_MENSAL = "profissional_mensal"
    EMPRESARIAL_MENSAL = "empresarial_mensal"
    BASICO_ANUAL = "basico_anual"
    INTERMEDIARIO_ANUAL = "intermediario_anual"
    PROFISSIONAL_ANUAL = "profissional_anual"
    EMPRESARIAL_ANUAL = "empresarial_anual"

class PlanStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    TRIAL = "trial"
    EXPIRED = "expired"

@dataclass
class PlanFeatures:
    # Limites de uso
    monthly_documents: int
    monthly_templates: int
    monthly_ai_requests: int
    storage_gb: int
    users_limit: int
    
    # Funcionalidades básicas
    document_creation: bool = True
    template_library: bool = True
    basic_ai: bool = True
    
    # Funcionalidades avançadas
    jurisprudence_analysis: bool = False
    deadline_prediction: bool = False
    advanced_ai: bool = False
    contract_analysis: bool = False
    
    # Funcionalidades empresariais
    executive_dashboard: bool = False
    predictive_reports: bool = False
    business_intelligence: bool = False
    performance_metrics: bool = False
    microservices_access: bool = False
    
    # Suporte e integração
    priority_support: bool = False
    api_access: bool = False
    white_label: bool = False
    custom_integrations: bool = False

class Plan(db.Model):
    __tablename__ = 'plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    plan_type = db.Column(db.Enum(PlanType), nullable=False)
    description = db.Column(db.Text)
    price_monthly = db.Column(db.Float, nullable=False)
    price_annual = db.Column(db.Float)
    is_popular = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Limites e funcionalidades (JSON)
    features_json = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    subscriptions = db.relationship('Subscription', backref='plan', lazy=True)
    
    @property
    def features(self) -> PlanFeatures:
        """Converte JSON para objeto PlanFeatures"""
        return PlanFeatures(**self.features_json)
    
    @features.setter
    def features(self, features: PlanFeatures):
        """Converte PlanFeatures para JSON"""
        self.features_json = {
            'monthly_documents': features.monthly_documents,
            'monthly_templates': features.monthly_templates,
            'monthly_ai_requests': features.monthly_ai_requests,
            'storage_gb': features.storage_gb,
            'users_limit': features.users_limit,
            'document_creation': features.document_creation,
            'template_library': features.template_library,
            'basic_ai': features.basic_ai,
            'jurisprudence_analysis': features.jurisprudence_analysis,
            'deadline_prediction': features.deadline_prediction,
            'advanced_ai': features.advanced_ai,
            'contract_analysis': features.contract_analysis,
            'executive_dashboard': features.executive_dashboard,
            'predictive_reports': features.predictive_reports,
            'business_intelligence': features.business_intelligence,
            'performance_metrics': features.performance_metrics,
            'microservices_access': features.microservices_access,
            'priority_support': features.priority_support,
            'api_access': features.api_access,
            'white_label': features.white_label,
            'custom_integrations': features.custom_integrations
        }
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'plan_type': self.plan_type.value,
            'description': self.description,
            'price_monthly': self.price_monthly,
            'price_annual': self.price_annual,
            'is_popular': self.is_popular,
            'is_active': self.is_active,
            'features': self.features_json,
            'created_at': self.created_at.isoformat()
        }

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    
    status = db.Column(db.Enum(PlanStatus), default=PlanStatus.ACTIVE)
    is_annual = db.Column(db.Boolean, default=False)
    
    # Datas importantes
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    trial_end_date = db.Column(db.DateTime)
    
    # Pagamento
    amount_paid = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    stripe_subscription_id = db.Column(db.String(255))
    
    # Uso mensal (resetado todo mês)
    monthly_documents_used = db.Column(db.Integer, default=0)
    monthly_templates_used = db.Column(db.Integer, default=0)
    monthly_ai_requests_used = db.Column(db.Integer, default=0)
    last_usage_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, user_id, plan_id, is_annual=False, trial_days=7):
        self.user_id = user_id
        self.plan_id = plan_id
        self.is_annual = is_annual
        self.start_date = datetime.utcnow()
        
        # Definir período trial
        if trial_days > 0:
            self.status = PlanStatus.TRIAL
            self.trial_end_date = self.start_date + timedelta(days=trial_days)
        else:
            self.status = PlanStatus.ACTIVE
        
        # Definir data de término
        if is_annual:
            self.end_date = self.start_date + timedelta(days=365)
        else:
            self.end_date = self.start_date + timedelta(days=30)
    
    @property
    def is_active(self) -> bool:
        """Verifica se a assinatura está ativa"""
        now = datetime.utcnow()
        return (
            self.status in [PlanStatus.ACTIVE, PlanStatus.TRIAL] and
            self.end_date > now
        )
    
    @property
    def is_trial(self) -> bool:
        """Verifica se está em período trial"""
        if not self.trial_end_date:
            return False
        return (
            self.status == PlanStatus.TRIAL and
            datetime.utcnow() < self.trial_end_date
        )
    
    @property
    def days_remaining(self) -> int:
        """Dias restantes da assinatura"""
        if not self.end_date:
            return 0
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    def reset_monthly_usage(self):
        """Reseta contadores mensais"""
        now = datetime.utcnow()
        last_reset = self.last_usage_reset or self.start_date
        
        # Verifica se já passou um mês desde o último reset
        if (now - last_reset).days >= 30:
            self.monthly_documents_used = 0
            self.monthly_templates_used = 0
            self.monthly_ai_requests_used = 0
            self.last_usage_reset = now
            db.session.commit()
    
    def can_use_feature(self, feature_name: str) -> bool:
        """Verifica se pode usar uma funcionalidade específica"""
        if not self.is_active:
            return False
        
        features = self.plan.features
        return getattr(features, feature_name, False)
    
    def check_usage_limit(self, usage_type: str) -> Dict:
        """Verifica limites de uso mensal"""
        self.reset_monthly_usage()
        features = self.plan.features
        
        usage_map = {
            'documents': (self.monthly_documents_used, features.monthly_documents),
            'templates': (self.monthly_templates_used, features.monthly_templates),
            'ai_requests': (self.monthly_ai_requests_used, features.monthly_ai_requests)
        }
        
        if usage_type not in usage_map:
            return {'allowed': False, 'reason': 'Invalid usage type'}
        
        used, limit = usage_map[usage_type]
        
        if limit == -1:  # Ilimitado
            return {'allowed': True, 'used': used, 'limit': -1}
        
        if used >= limit:
            return {
                'allowed': False,
                'used': used,
                'limit': limit,
                'reason': f'Monthly limit of {limit} {usage_type} exceeded'
            }
        
        return {'allowed': True, 'used': used, 'limit': limit}
    
    def increment_usage(self, usage_type: str):
        """Incrementa contador de uso"""
        if usage_type == 'documents':
            self.monthly_documents_used += 1
        elif usage_type == 'templates':
            self.monthly_templates_used += 1
        elif usage_type == 'ai_requests':
            self.monthly_ai_requests_used += 1
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan.to_dict() if self.plan else None,
            'status': self.status.value,
            'is_annual': self.is_annual,
            'is_active': self.is_active,
            'is_trial': self.is_trial,
            'days_remaining': self.days_remaining,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'trial_end_date': self.trial_end_date.isoformat() if self.trial_end_date else None,
            'monthly_usage': {
                'documents': {
                    'used': self.monthly_documents_used,
                    'limit': self.plan.features.monthly_documents if self.plan else 0
                },
                'templates': {
                    'used': self.monthly_templates_used,
                    'limit': self.plan.features.monthly_templates if self.plan else 0
                },
                'ai_requests': {
                    'used': self.monthly_ai_requests_used,
                    'limit': self.plan.features.monthly_ai_requests if self.plan else 0
                }
            }
        }

# Função para criar planos padrão
def create_default_plans():
    """Cria os planos padrão da aplicação"""
    
    # Plano Básico Mensal
    basic_features = PlanFeatures(
        monthly_documents=50,
        monthly_templates=10,
        monthly_ai_requests=100,
        storage_gb=5,
        users_limit=1,
        document_creation=True,
        template_library=True,
        basic_ai=True
    )
    
    basic_plan = Plan(
        name="Básico Mensal",
        plan_type=PlanType.BASICO_MENSAL,
        description="Perfeito para advogados autônomos e pequenos escritórios.",
        price_monthly=49.90,
        features=basic_features
    )
    
    # Plano Intermediário Mensal (Popular)
    intermediate_features = PlanFeatures(
        monthly_documents=200,
        monthly_templates=50,
        monthly_ai_requests=500,
        storage_gb=20,
        users_limit=3,
        document_creation=True,
        template_library=True,
        basic_ai=True,
        jurisprudence_analysis=True,
        deadline_prediction=True,
        advanced_ai=True
    )
    
    intermediate_plan = Plan(
        name="Intermediário Mensal",
        plan_type=PlanType.INTERMEDIARIO_MENSAL,
        description="Perfeito para escritórios em crescimento.",
        price_monthly=99.90,
        is_popular=True,
        features=intermediate_features
    )
    
    # Plano Profissional Mensal
    professional_features = PlanFeatures(
        monthly_documents=1000,
        monthly_templates=200,
        monthly_ai_requests=2000,
        storage_gb=100,
        users_limit=10,
        document_creation=True,
        template_library=True,
        basic_ai=True,
        jurisprudence_analysis=True,
        deadline_prediction=True,
        advanced_ai=True,
        contract_analysis=True,
        executive_dashboard=True,
        predictive_reports=True,
        priority_support=True,
        api_access=True
    )
    
    professional_plan = Plan(
        name="Profissional Mensal",
        plan_type=PlanType.PROFISSIONAL_MENSAL,
        description="Para escritórios estabelecidos que precisam de recursos avançados.",
        price_monthly=199.90,
        features=professional_features
    )
    
    # Plano Empresarial Mensal
    enterprise_features = PlanFeatures(
        monthly_documents=-1,  # Ilimitado
        monthly_templates=-1,  # Ilimitado
        monthly_ai_requests=-1,  # Ilimitado
        storage_gb=500,
        users_limit=50,
        document_creation=True,
        template_library=True,
        basic_ai=True,
        jurisprudence_analysis=True,
        deadline_prediction=True,
        advanced_ai=True,
        contract_analysis=True,
        executive_dashboard=True,
        predictive_reports=True,
        business_intelligence=True,
        performance_metrics=True,
        microservices_access=True,
        priority_support=True,
        api_access=True,
        white_label=True,
        custom_integrations=True
    )
    
    enterprise_plan = Plan(
        name="Empresarial Mensal",
        plan_type=PlanType.EMPRESARIAL_MENSAL,
        description="Solução completa para grandes escritórios e departamentos jurídicos.",
        price_monthly=399.90,
        features=enterprise_features
    )
    
    # Adicionar ao banco
    db.session.add_all([basic_plan, intermediate_plan, professional_plan, enterprise_plan])
    db.session.commit()
    
    return [basic_plan, intermediate_plan, professional_plan, enterprise_plan]
