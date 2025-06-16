import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import app
from extensions import db
from models.user import User
from models.subscription import Subscription
from werkzeug.security import generate_password_hash

with app.app_context():
    # Criar todas as tabelas
    db.create_all()
    print('Tabelas criadas!')
    
    # Verificar se o usuário admin já existe
    admin = User.query.filter_by(email='admin@jurisia.com').first()
    if not admin:
        # Criar usuário admin
        admin = User(
            nome='Administrador',
            email='admin@jurisia.com',
            senha_hash=generate_password_hash('admin123'),
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Usuário admin criado!')
    else:
        print('Usuário admin já existe!') 