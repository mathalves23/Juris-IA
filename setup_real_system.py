#!/usr/bin/env python3
"""
Script para configurar sistema JurisIA com dados reais
"""

import os
import sys
from datetime import datetime, timedelta

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.extensions import db
from src.models.user import User
from src.models.document import Document
from src.models.template import Template
from flask_bcrypt import Bcrypt

def main():
    print("🚀 Configurando sistema JurisIA...")
    
    app = create_app()
    bcrypt = Bcrypt(app)
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        print("✅ Banco de dados configurado")
        
        # Criar usuário de teste se não existir
        test_user = User.query.filter_by(email='advogado@jurisia.com').first()
        
        if not test_user:
            test_password_hash = User.hash_password('123456')
            test_user = User(
                nome='Dr. João Silva',
                email='advogado@jurisia.com',
                senha_hash=test_password_hash,
                papel='user',
                email_verificado=True
            )
            db.session.add(test_user)
            db.session.commit()
            print("✅ Usuário criado: advogado@jurisia.com / 123456")
        else:
            print("ℹ️ Usuário já existe")
        
        # Criar documentos de exemplo
        if Document.query.filter_by(user_id=test_user.id).count() == 0:
            doc1 = Document(
                titulo='Contrato de Prestação de Serviços',
                conteudo='<h2>CONTRATO DE PRESTAÇÃO DE SERVIÇOS</h2><p>Contrato de exemplo...</p>',
                status='Rascunho',
                user_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            doc2 = Document(
                titulo='Petição Inicial - Ação de Cobrança',
                conteudo='<h2>PETIÇÃO INICIAL</h2><p>Petição de exemplo...</p>',
                status='Em Revisão',
                user_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            doc3 = Document(
                titulo='Parecer Jurídico',
                conteudo='<h2>PARECER JURÍDICO</h2><p>Parecer de exemplo...</p>',
                status='Finalizado',
                user_id=test_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(doc1)
            db.session.add(doc2)
            db.session.add(doc3)
            db.session.commit()
            print("✅ Documentos de exemplo criados")
        
        print("\n🎯 Sistema configurado com sucesso!")
        print("=" * 50)
        print("📧 Email: advogado@jurisia.com")
        print("🔑 Senha: 123456")
        print("=" * 50)
        print("\nPara iniciar:")
        print("Backend: python main.py")
        print("Frontend: cd frontend && npm run build && npm start")

if __name__ == '__main__':
    main() 