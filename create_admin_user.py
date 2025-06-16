#!/usr/bin/env python3
"""
Script para criar um usuário admin personalizado
Execute este script após a primeira inicialização da aplicação
"""

import sys
import os
from datetime import datetime
import secrets
import string

# Adicionar o diretório src ao Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User


def generate_strong_password(length=12):
    """Gera uma senha forte"""
    characters = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


def create_admin_user():
    """Cria um usuário admin personalizado"""
    print("🔧 CRIAÇÃO DE USUÁRIO ADMIN PERSONALIZADO")
    print("=" * 50)
    
    # Verificar se já existe um admin
    existing_admin = User.query.filter_by(email='admin@jurisia.com').first()
    if existing_admin:
        print("⚠️  Usuário admin padrão já existe.")
        overwrite = input("Deseja criar um novo admin personalizado? (s/n): ").lower()
        if overwrite != 's':
            print("❌ Operação cancelada.")
            return
    
    print("\n📝 Insira os dados do seu usuário admin:")
    
    # Coletar dados do usuário
    while True:
        name = input("👤 Nome completo: ").strip()
        if name:
            break
        print("❌ Nome é obrigatório!")
    
    while True:
        email = input("📧 Email: ").strip()
        if email and '@' in email:
            # Verificar se email já existe
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"❌ Email {email} já está em uso!")
                continue
            break
        print("❌ Email válido é obrigatório!")
    
    # Opção de senha
    print("\n🔑 Configuração de senha:")
    print("1. Gerar senha automática (recomendado)")
    print("2. Inserir senha manualmente")
    
    while True:
        choice = input("Escolha uma opção (1 ou 2): ").strip()
        if choice in ['1', '2']:
            break
        print("❌ Escolha 1 ou 2!")
    
    if choice == '1':
        password = generate_strong_password()
        print(f"🔐 Senha gerada: {password}")
        print("⚠️  IMPORTANTE: Anote esta senha em local seguro!")
    else:
        while True:
            password = input("🔐 Digite sua senha (mín. 8 caracteres): ").strip()
            if len(password) >= 8:
                break
            print("❌ Senha deve ter pelo menos 8 caracteres!")
    
    try:
        # Criar o usuário
        admin_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True,
            email_verified=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("\n✅ USUÁRIO ADMIN CRIADO COM SUCESSO!")
        print("=" * 50)
        print(f"👤 Nome: {name}")
        print(f"📧 Email: {email}")
        print(f"🔐 Senha: {password}")
        print(f"🔧 Admin: Sim")
        print(f"📅 Criado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 50)
        print("💡 Use estas credenciais para fazer login na aplicação")
        print("🌐 Frontend: http://localhost:3023")
        print("🔗 API: http://localhost:5005")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {str(e)}")
        db.session.rollback()


if __name__ == '__main__':
    # Importar a aplicação Flask
    from main import app
    
    with app.app_context():
        create_admin_user() 