#!/usr/bin/env python3
"""Script simples para criar apenas as tabelas"""

import os
import sys
sys.path.append('./src')

# Configurar ambiente
os.environ['DATABASE_URL'] = 'postgresql://localhost/jurisia_db'
os.environ['FLASK_ENV'] = 'development'

from src.main import app
from src.extensions import db

def create_tables():
    """Criar apenas as tabelas"""
    with app.app_context():
        try:
            print("🔧 Conectando ao PostgreSQL...")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("✨ PostgreSQL pronto!")
    else:
        print("💥 Falhou!")
        sys.exit(1) 