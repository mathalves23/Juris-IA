from src.extensions import db
from src.models.user import User
from src.models.subscription import Subscription, PlanStatus, Plan
from src.config import Config
import os

os.environ['DATABASE_URL'] = 'postgresql://localhost/jurisia_db'

# Configurar app context
from src.main import app
with app.app_context():
    user = User.query.filter_by(email='admin@jurisia.com').first()
    print(f'Usuário: {user.nome}')
    
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if subscription:
        print(f'Assinatura: {subscription.status}')
        print(f'Plano: {subscription.plan.name}')
    else:
        print('Nenhuma assinatura encontrada')
        
        # Criar assinatura básica
        plan = Plan.query.first()
        
        if plan:
            subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id
            )
            subscription.status = PlanStatus.ACTIVE
            db.session.add(subscription)
            db.session.commit()
            print(f'Assinatura criada: {subscription.status} - Plano: {plan.name}')
        else:
            print('Nenhum plano encontrado') 