#!/usr/bin/env python3

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_database():
    """Cria banco de dados SQLite manualmente"""
    
    # Caminho para o banco de dados
    db_path = os.path.join(os.path.dirname(__file__), 'jurisia.db')
    
    print(f"Criando banco de dados em: {db_path}")
    
    # Remover banco existente se houver
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Banco existente removido")
    
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabelas
    print("Criando tabelas...")
    
    # Tabela users
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            senha_hash VARCHAR(255) NOT NULL,
            telefone VARCHAR(20),
            empresa VARCHAR(200),
            cargo VARCHAR(100),
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela subscriptions
    cursor.execute('''
        CREATE TABLE subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plano VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'ativo',
            limite_documentos INTEGER DEFAULT 100,
            documentos_utilizados INTEGER DEFAULT 0,
            limite_templates INTEGER DEFAULT 50,
            templates_utilizados INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela templates
    cursor.execute('''
        CREATE TABLE templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            titulo VARCHAR(200) NOT NULL,
            categoria VARCHAR(100),
            conteudo TEXT,
            variaveis TEXT,
            tags VARCHAR(500),
            publico BOOLEAN DEFAULT FALSE,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela documents
    cursor.execute('''
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            template_id INTEGER,
            titulo VARCHAR(200) NOT NULL,
            conteudo TEXT,
            variaveis TEXT,
            status VARCHAR(50) DEFAULT 'rascunho',
            versao INTEGER DEFAULT 1,
            tags VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (template_id) REFERENCES templates (id)
        )
    ''')
    
    print("Tabelas criadas com sucesso!")
    
    # Inserir dados de exemplo
    print("Inserindo dados de exemplo...")
    
    # Usuário administrador - usando hash manual simples
    import hashlib
    senha_hash = hashlib.pbkdf2_hmac('sha256', 'admin123'.encode(), b'salt', 100000)
    senha_hash_str = senha_hash.hex()
    
    cursor.execute('''
        INSERT INTO users (nome, email, senha_hash, telefone, empresa, cargo)
        VALUES (?, ?, ?, ?, ?, ?)
            ''', ('Administrador', 'admin@jurisia.com', senha_hash_str, '(11) 99999-9999', 'JurisIA Ltda', 'Administrador'))
    
    user_id = cursor.lastrowid
    
    # Assinatura do usuário
    expires_at = datetime.now() + timedelta(days=365)
    cursor.execute('''
        INSERT INTO subscriptions (user_id, plano, status, limite_documentos, documentos_utilizados, 
                                 limite_templates, templates_utilizados, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, 'premium', 'ativo', 1000, 0, 100, 5, expires_at))
    
    # Template básico
    cursor.execute('''
        INSERT INTO templates (user_id, titulo, categoria, conteudo, variaveis, tags, publico)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, 'Petição Inicial Cível', 'Petições', 
          '<h2>PETIÇÃO INICIAL</h2><p>Exemplo de template jurídico.</p>', 
          '[]', 'petição inicial, cível', True))
    
    # Documento de exemplo
    cursor.execute('''
        INSERT INTO documents (user_id, template_id, titulo, conteudo, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, 1, 'Exemplo - Ação de Cobrança', 
          '<h2>PETIÇÃO INICIAL - AÇÃO DE COBRANÇA</h2><p>Documento de exemplo.</p>', 
          'rascunho'))
    
    # Commit e fechar
    conn.commit()
    conn.close()
    
    print(f"✅ Banco de dados criado com sucesso!")
    print(f"📁 Localização: {db_path}")
    print(f"👤 Usuário admin: admin@jurisia.com")
    print(f"🔑 Senha: admin123")

if __name__ == '__main__':
    create_database() 