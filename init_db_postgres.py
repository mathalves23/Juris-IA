#!/usr/bin/env python3
"""Script para inicializar o banco de dados PostgreSQL"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import app
from extensions import db
from models.user import User
from models.subscription import Subscription
from werkzeug.security import generate_password_hash

def init_database():
    """Inicializa o banco de dados com as tabelas e dados iniciais"""
    with app.app_context():
        try:
            # Dropar todas as tabelas se existirem (para limpar)
            print("🔄 Removendo tabelas existentes...")
            db.drop_all()
            
            # Criar todas as tabelas
            print("🔧 Criando tabelas...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se o usuário admin já existe
            admin = User.query.filter_by(email='admin@jurisia.com').first()
            if not admin:
                # Criar usuário admin
                admin = User(
                    nome='Administrador',
                    email='admin@jurisia.com',
                    senha_hash=generate_password_hash('admin123'),
                    ativo=True,
                    data_criacao=datetime.utcnow()
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuário admin criado!")
                print("   📧 Email: admin@jurisia.com")
                print("   🔑 Senha: admin123")
            else:
                print("ℹ️  Usuário admin já existe!")
                
            # Verificar se existe plano básico
            plano_basico = Subscription.query.filter_by(nome='Básico').first()
            if not plano_basico:
                plano_basico = Subscription(
                    nome='Básico',
                    descricao='Plano básico com funcionalidades essenciais',
                    preco=29.90,
                    duracao_dias=30,
                    max_documentos=50,
                    max_templates=10,
                    ativo=True
                )
                db.session.add(plano_basico)
                db.session.commit()
                print("✅ Plano Básico criado!")
                
            print("\n🎉 Banco de dados inicializado com sucesso!")
            print("🚀 Você pode agora fazer login com admin@jurisia.com / admin123")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {str(e)}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🗄️  Inicializando banco de dados PostgreSQL...")
    success = init_database()
    if success:
        print("✨ Inicialização concluída!")
    else:
        print("💥 Falha na inicialização!")
        sys.exit(1) 