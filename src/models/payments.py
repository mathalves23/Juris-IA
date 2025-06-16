from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
import enum
from src.extensions import db

class SubscriptionStatus(enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"

class PaymentMethod(enum.Enum):
    CREDIT_CARD = "credit_card"
    PIX = "pix"
    BOLETO = "boleto"
    BANK_TRANSFER = "bank_transfer"

class PlanInterval(enum.Enum):
    MONTH = "month"
    YEAR = "year"

class Plan(db.Model):
    __tablename__ = 'plans'
    
    id = Column(String(50), primary_key=True)  # Ex: 'basic', 'professional'
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    interval = Column(Enum(PlanInterval), nullable=False)
    currency = Column(String(3), default='BRL')
    
    # Características do plano
    max_documents = Column(Integer)  # -1 para ilimitado
    max_users = Column(Integer, default=1)
    features = Column(JSON)  # Lista de features incluídas
    
    # Flags
    is_active = Column(Boolean, default=True)
    is_recommended = Column(Boolean, default=False)
    discount_percentage = Column(Integer, default=0)
    
    # Metadados
    stripe_price_id = Column(String(100))  # ID do preço no Stripe
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'interval': self.interval.value,
            'currency': self.currency,
            'max_documents': self.max_documents,
            'max_users': self.max_users,
            'features': self.features or [],
            'is_active': self.is_active,
            'is_recommended': self.is_recommended,
            'discount_percentage': self.discount_percentage,
            'stripe_price_id': self.stripe_price_id
        }

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Dados do cliente
    name = Column(String(200), nullable=False)
    email = Column(String(150), nullable=False)
    phone = Column(String(20))
    document = Column(String(20))  # CPF/CNPJ
    document_type = Column(String(10))  # 'cpf' ou 'cnpj'
    
    # Endereço
    address_street = Column(String(200))
    address_number = Column(String(20))
    address_complement = Column(String(100))
    address_district = Column(String(100))
    address_city = Column(String(100))
    address_state = Column(String(2))
    address_zipcode = Column(String(10))
    address_country = Column(String(2), default='BR')
    
    # IDs externos
    stripe_customer_id = Column(String(100))
    pagseguro_customer_id = Column(String(100))
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = relationship("User", back_populates="customer")
    subscriptions = relationship("Subscription", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'document': self.document,
            'document_type': self.document_type,
            'address': {
                'street': self.address_street,
                'number': self.address_number,
                'complement': self.address_complement,
                'district': self.address_district,
                'city': self.address_city,
                'state': self.address_state,
                'zipcode': self.address_zipcode,
                'country': self.address_country
            },
            'stripe_customer_id': self.stripe_customer_id,
            'pagseguro_customer_id': self.pagseguro_customer_id
        }

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    plan_id = Column(String(50), ForeignKey('plans.id'), nullable=False)
    
    # Status da assinatura
    status = Column(Enum(SubscriptionStatus), nullable=False)
    
    # Datas importantes
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    canceled_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    # Configurações
    cancel_at_period_end = Column(Boolean, default=False)
    collection_method = Column(String(20), default='charge_automatically')
    
    # IDs externos
    stripe_subscription_id = Column(String(100))
    pagseguro_subscription_id = Column(String(100))
    
    # Metadados
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    
    @property
    def is_active(self):
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
    
    @property
    def days_until_renewal(self):
        if self.current_period_end:
            return (self.current_period_end - datetime.utcnow()).days
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'plan_id': self.plan_id,
            'status': self.status.value,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'is_active': self.is_active,
            'days_until_renewal': self.days_until_renewal,
            'plan': self.plan.to_dict() if self.plan else None,
            'stripe_subscription_id': self.stripe_subscription_id,
            'metadata': self.metadata
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    
    # Dados do pagamento
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='BRL')
    status = Column(Enum(PaymentStatus), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Detalhes específicos do método
    payment_details = Column(JSON)  # Dados específicos como últimos 4 dígitos, etc.
    
    # Datas
    payment_date = Column(DateTime)
    due_date = Column(DateTime)
    paid_at = Column(DateTime)
    failed_at = Column(DateTime)
    refunded_at = Column(DateTime)
    
    # IDs externos e referências
    stripe_payment_intent_id = Column(String(100))
    stripe_charge_id = Column(String(100))
    pagseguro_transaction_id = Column(String(100))
    boleto_barcode = Column(String(100))
    boleto_url = Column(String(500))
    pix_qr_code = Column(Text)
    pix_qr_code_url = Column(String(500))
    
    # Informações adicionais
    description = Column(String(200))
    failure_reason = Column(String(200))
    receipt_url = Column(String(500))
    invoice_url = Column(String(500))
    
    # Metadados
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'subscription_id': self.subscription_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'payment_method': self.payment_method.value,
            'payment_details': self.payment_details,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'description': self.description,
            'failure_reason': self.failure_reason,
            'receipt_url': self.receipt_url,
            'invoice_url': self.invoice_url,
            'boleto_url': self.boleto_url,
            'pix_qr_code_url': self.pix_qr_code_url,
            'metadata': self.metadata
        }

class PaymentWebhook(db.Model):
    __tablename__ = 'payment_webhooks'
    
    id = Column(Integer, primary_key=True)
    
    # Identificação
    webhook_id = Column(String(100))  # ID do webhook no provedor
    provider = Column(String(50), nullable=False)  # stripe, pagseguro, etc.
    event_type = Column(String(100), nullable=False)
    
    # Dados do evento
    data = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Relacionamentos
    payment_id = Column(Integer, ForeignKey('payments.id'))
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'webhook_id': self.webhook_id,
            'provider': self.provider,
            'event_type': self.event_type,
            'processed': self.processed,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'error_message': self.error_message,
            'payment_id': self.payment_id,
            'subscription_id': self.subscription_id,
            'created_at': self.created_at.isoformat()
        }

class Discount(db.Model):
    __tablename__ = 'discounts'
    
    id = Column(Integer, primary_key=True)
    
    # Identificação
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Tipo de desconto
    discount_type = Column(String(20), nullable=False)  # 'percentage', 'fixed'
    amount = Column(Float, nullable=False)  # Porcentagem ou valor fixo
    
    # Limitações
    max_uses = Column(Integer)  # Limite de usos
    max_uses_per_customer = Column(Integer, default=1)
    minimum_amount = Column(Float)  # Valor mínimo para aplicar
    
    # Aplicabilidade
    applicable_plans = Column(JSON)  # Lista de plan_ids ou null para todos
    first_payment_only = Column(Boolean, default=False)
    
    # Validade
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    uses_count = Column(Integer, default=0)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_valid(self):
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now and
            (self.valid_until is None or self.valid_until >= now) and
            (self.max_uses is None or self.uses_count < self.max_uses)
        )
    
    def calculate_discount(self, amount):
        """Calcula o valor do desconto para um determinado valor"""
        if not self.is_valid:
            return 0
        
        if self.minimum_amount and amount < self.minimum_amount:
            return 0
        
        if self.discount_type == 'percentage':
            return amount * (self.amount / 100)
        elif self.discount_type == 'fixed':
            return min(self.amount, amount)
        
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'amount': self.amount,
            'max_uses': self.max_uses,
            'max_uses_per_customer': self.max_uses_per_customer,
            'minimum_amount': self.minimum_amount,
            'applicable_plans': self.applicable_plans,
            'first_payment_only': self.first_payment_only,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_active': self.is_active,
            'is_valid': self.is_valid,
            'uses_count': self.uses_count
        }

# Função para criar planos padrão
def create_default_plans():
    """Cria os planos padrão da aplicação"""
    plans = [
        {
            'id': 'basic',
            'name': 'Básico',
            'description': 'Plano ideal para advogados iniciantes',
            'price': 99.90,
            'interval': PlanInterval.MONTH,
            'max_documents': 50,
            'max_users': 1,
            'features': [
                'Até 50 documentos/mês',
                'Editor IA básico',
                'Templates padrão',
                'Suporte por email'
            ]
        },
        {
            'id': 'professional',
            'name': 'Profissional',
            'description': 'Plano completo para profissionais',
            'price': 199.90,
            'interval': PlanInterval.MONTH,
            'max_documents': -1,  # Ilimitado
            'max_users': 1,
            'is_recommended': True,
            'features': [
                'Documentos ilimitados',
                'IA Assistant avançado',
                'Templates premium',
                'Análise de contratos',
                'Dashboard analytics',
                'Suporte prioritário'
            ]
        },
        {
            'id': 'enterprise',
            'name': 'Empresarial',
            'description': 'Solução completa para escritórios',
            'price': 399.90,
            'interval': PlanInterval.MONTH,
            'max_documents': -1,
            'max_users': 10,
            'features': [
                'Tudo do Profissional',
                'Multi-usuários (até 10)',
                'API personalizada',
                'Integração customizada',
                'Suporte 24/7',
                'Treinamento incluído'
            ]
        },
        {
            'id': 'professional_yearly',
            'name': 'Profissional Anual',
            'description': 'Plano profissional com desconto anual',
            'price': 1999.90,
            'interval': PlanInterval.YEAR,
            'max_documents': -1,
            'max_users': 1,
            'discount_percentage': 20,
            'features': [
                'Tudo do Profissional',
                '20% de desconto',
                'Suporte premium'
            ]
        }
    ]
    
    for plan_data in plans:
        existing_plan = Plan.query.filter_by(id=plan_data['id']).first()
        if not existing_plan:
            plan = Plan(**plan_data)
            db.session.add(plan)
    
    try:
        db.session.commit()
        print("Planos padrão criados com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar planos padrão: {e}")

if __name__ == "__main__":
    # Para testar a criação dos modelos
    from src.extensions import create_app
    
    app = create_app()
    with app.app_context():
        db.create_all()
        create_default_plans()