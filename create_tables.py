#!/usr/bin/env python3
"""Script simples para criar tabelas PostgreSQL"""

import os
import sys
sys.path.append('./src')

# Configurar Flask antes de importar modelos
os.environ['FLASK_ENV'] = 'development'

from src.main import app
from src.extensions import db
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_tables():
    """Cria as tabelas e dados iniciais"""
    with app.app_context():
        try:
            print("🔧 Criando tabelas PostgreSQL...")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas!")
            
            # Verificar se precisa criar usuário admin
            from src.models.user import User
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
                
                # Criar um plano básico
                from src.models.subscription import Subscription
                plano = Subscription(
                    nome='Básico',
                    descricao='Plano básico',
                    preco=29.90,
                    duracao_dias=30,
                    max_documentos=50,
                    max_templates=10,
                    ativo=True
                )
                db.session.add(plano)
                
                db.session.commit()
                print("✅ Usuário admin criado: admin@jurisia.com / admin123")
                print("✅ Plano básico criado")
            else:
                print("ℹ️  Usuário admin já existe")
                
            print("🎉 Banco PostgreSQL configurado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("✨ Sucesso!")
    else:
        print("💥 Falhou!")
        sys.exit(1) 