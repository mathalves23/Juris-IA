#!/usr/bin/env python3
"""
Script para inicializar o sistema completo do JurisIA com dados de exemplo
Inclui: Usuários, Clientes, Processos, Quadros Kanban, Wiki e Notificações
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.getcwd())

from src.extensions import db
from src.models.user import User
from src.models.client import Client
from src.models.process import Process
from src.models.kanban import KanbanBoard, KanbanList, KanbanCard, ChecklistItem, Tag
from src.models.wiki import Wiki, WikiTag
from src.models.notification import Notification
from src.models.subscription import Subscription, Plan

def create_sample_data():
    """Criar dados de exemplo para demonstração"""
    
    print("🔧 Iniciando criação de dados de exemplo...")
    
    try:
        # 1. Criar usuário administrador se não existir
        admin = User.query.filter_by(email='admin@jurisia.com').first()
        if not admin:
            admin = User(
                nome='Administrador JurisIA',
                email='admin@jurisia.com',
                telefone='(11) 99999-9999',
                empresa='JurisIA Ltda',
                funcao='Administrador'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()
            print("✅ Usuário admin criado")
        else:
            print("✅ Usuário admin já existe")
        
        # 2. Criar clientes de exemplo
        clientes_exemplos = [
            {
                'nome': 'João Silva Santos',
                'documento': '123.456.789-10',
                'tipo_pessoa': 'PF',
                'email': 'joao.silva@email.com',
                'telefone': '(11) 98888-7777',
                'endereco': 'Rua das Flores, 123 - São Paulo/SP'
            },
            {
                'nome': 'Empresa ABC Ltda',
                'documento': '12.345.678/0001-90',
                'tipo_pessoa': 'PJ',
                'email': 'contato@empresaabc.com',
                'telefone': '(11) 3333-4444',
                'endereco': 'Av. Paulista, 1000 - São Paulo/SP'
            }
        ]
        
        clientes = []
        for cliente_data in clientes_exemplos:
            cliente_existente = Client.query.filter_by(documento=cliente_data['documento']).first()
            if not cliente_existente:
                cliente = Client(
                    usuario_id=admin.id,
                    **cliente_data
                )
                db.session.add(cliente)
                clientes.append(cliente)
        
        db.session.flush()
        print(f"✅ {len(clientes)} clientes criados")
        
        # 3. Criar processos de exemplo
        if clientes:
            processos_exemplos = [
                {
                    'numero': '1234567-89.2024.8.26.0100',
                    'tribunal': 'TJSP',
                    'vara': '1ª Vara Cível',
                    'comarca': 'São Paulo',
                    'area': 'Cível',
                    'valor_causa': 50000.00,
                    'parte_contraria': 'Banco XYZ S.A.',
                    'descricao': 'Ação de cobrança indevida com danos morais'
                }
            ]
            
            processos = []
            for processo_data in processos_exemplos:
                processo_existente = Process.query.filter_by(numero=processo_data['numero']).first()
                if not processo_existente:
                    processo = Process(
                        usuario_id=admin.id,
                        cliente_id=clientes[0].id,
                        **processo_data
                    )
                    db.session.add(processo)
                    processos.append(processo)
            
            db.session.flush()
            print(f"✅ {len(processos)} processos criados")
        
        # 4. Criar quadro Kanban
        board_existente = KanbanBoard.query.filter_by(nome='Processos Gerais').first()
        if not board_existente:
            board = KanbanBoard(
                nome='Processos Gerais',
                area='Geral',
                criado_por=admin.id,
                cor='#3B82F6'
            )
            db.session.add(board)
            db.session.flush()
            
            # Criar listas padrão
            listas_padrão = [
                {'nome': 'A Fazer', 'ordem': 1, 'cor': '#F3F4F6'},
                {'nome': 'Em Andamento', 'ordem': 2, 'cor': '#DBEAFE'},
                {'nome': 'Concluído', 'ordem': 3, 'cor': '#D1FAE5'}
            ]
            
            for lista_data in listas_padrão:
                lista = KanbanList(
                    quadro_id=board.id,
                    **lista_data
                )
                db.session.add(lista)
            
            db.session.flush()
            print("✅ Quadro Kanban criado")
            
            # Criar cartão de exemplo
            if board.listas:
                cartao = KanbanCard(
                    lista_id=board.listas[0].id,
                    titulo='Analisar contestação',
                    descricao='Revisar contestação apresentada pela parte adversa',
                    criado_por=admin.id,
                    ordem=1,
                    prioridade='Alta'
                )
                db.session.add(cartao)
                print("✅ Cartão de exemplo criado")
        
        # 5. Criar item da Wiki
        wiki_existente = Wiki.query.filter_by(titulo='Prazos Processuais').first()
        if not wiki_existente:
            wiki = Wiki(
                titulo='Prazos Processuais',
                categoria='Prazos',
                texto='Principais prazos do processo civil:\n\n- Contestação: 15 dias\n- Tréplica: 15 dias\n- Recurso: 15 dias',
                autor_id=admin.id,
                status='Publicado'
            )
            db.session.add(wiki)
            print("✅ Item da Wiki criado")
        
        # 6. Criar notificação
        notificacao = Notification(
            usuario_id=admin.id,
            tipo='Sistema',
            titulo='Sistema JurisIA Inicializado',
            mensagem='O sistema foi inicializado com dados de exemplo. Bem-vindo ao JurisIA!',
            prioridade='Normal'
        )
        db.session.add(notificacao)
        print("✅ Notificação criada")
        
        # Commit final
        db.session.commit()
        
        print("\n🎉 Sistema completo inicializado com sucesso!")
        print("\n🔑 Credenciais de acesso:")
        print(f"   📧 Email: admin@jurisia.com")
        print(f"   🔒 Senha: admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar dados de exemplo: {e}")
        db.session.rollback()
        return False

if __name__ == '__main__':
    from src.main import create_app
    
    print("🚀 Inicializando sistema JurisIA...")
    
    app = create_app()
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas/verificadas")
            
            # Criar dados de exemplo
            if create_sample_data():
                print("\n✅ Inicialização concluída com sucesso!")
                print("🌐 Você já pode acessar o sistema!")
            else:
                print("\n❌ Falha na inicialização")
                
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            sys.exit(1) 