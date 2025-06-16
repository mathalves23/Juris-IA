#!/usr/bin/env python3
"""
Script para inicializar o sistema completo do JurisIA com dados de exemplo
Inclui: Usuários, Clientes, Processos, Quadros Kanban, Wiki e Notificações
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Adicionar o diretório pai ao Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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
        
        # 2. Criar plano e assinatura para o admin
        plano = Plan.query.filter_by(nome='Empresarial').first()
        if not plano:
            plano = Plan(
                nome='Empresarial',
                preco=399.90,
                limite_documentos=None,  # Ilimitado
                limite_templates=None,
                limite_ia_calls=None,
                features=['documentos_ilimitados', 'templates_ilimitados', 'ia_ilimitada', 'kanban', 'wiki', 'publicacoes']
            )
            db.session.add(plano)
            db.session.flush()
        
        subscription = Subscription.query.filter_by(usuario_id=admin.id).first()
        if not subscription:
            subscription = Subscription(
                usuario_id=admin.id,
                plano_id=plano.id,
                status='ativo',
                data_inicio=datetime.utcnow(),
                data_proximo_pagamento=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            print("✅ Assinatura criada para admin")
        
        # 3. Criar clientes de exemplo
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
            },
            {
                'nome': 'Maria Oliveira Costa',
                'documento': '987.654.321-00',
                'tipo_pessoa': 'PF',
                'email': 'maria.oliveira@email.com',
                'telefone': '(11) 97777-6666',
                'endereco': 'Rua dos Jardins, 456 - São Paulo/SP'
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
        
        # 4. Criar processos de exemplo
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
            },
            {
                'numero': '9876543-21.2024.5.02.0001',
                'tribunal': 'TRT2',
                'vara': '2ª Vara do Trabalho',
                'comarca': 'São Paulo',
                'area': 'Trabalhista',
                'valor_causa': 25000.00,
                'parte_contraria': 'Empresa ABC Ltda',
                'descricao': 'Reclamação trabalhista por verbas rescisórias'
            },
            {
                'numero': '5555666-77.2024.8.26.0200',
                'tribunal': 'TJSP',
                'vara': '3ª Vara de Família',
                'comarca': 'São Paulo',
                'area': 'Família',
                'valor_causa': 15000.00,
                'parte_contraria': 'Ex-cônjuge',
                'descricao': 'Ação de alimentos'
            }
        ]
        
        processos = []
        for i, processo_data in enumerate(processos_exemplos):
            processo_existente = Process.query.filter_by(numero=processo_data['numero']).first()
            if not processo_existente and i < len(clientes):
                processo = Process(
                    usuario_id=admin.id,
                    cliente_id=clientes[i].id,
                    **processo_data
                )
                db.session.add(processo)
                processos.append(processo)
        
        db.session.flush()
        print(f"✅ {len(processos)} processos criados")
        
        # 5. Criar tags para o sistema
        tags_exemplos = ['Urgente', 'Prazo Curto', 'Importante', 'Revisão', 'Aguardando Cliente']
        tags_criadas = []
        
        for tag_nome in tags_exemplos:
            tag_existente = Tag.query.filter_by(nome=tag_nome).first()
            if not tag_existente:
                tag = Tag(nome=tag_nome, cor=f"#{random.randint(0, 16777215):06x}")
                db.session.add(tag)
                tags_criadas.append(tag)
        
        db.session.flush()
        print(f"✅ {len(tags_criadas)} tags criadas")
        
        # 6. Criar quadros Kanban
        boards_exemplos = [
            {
                'nome': 'Processos Cíveis',
                'area': 'Cível',
                'cor': '#3B82F6'
            },
            {
                'nome': 'Processos Trabalhistas',
                'area': 'Trabalhista',
                'cor': '#10B981'
            },
            {
                'nome': 'Processos de Família',
                'area': 'Família',
                'cor': '#F59E0B'
            }
        ]
        
        boards = []
        for board_data in boards_exemplos:
            board_existente = KanbanBoard.query.filter_by(nome=board_data['nome']).first()
            if not board_existente:
                board = KanbanBoard(
                    criado_por=admin.id,
                    **board_data
                )
                db.session.add(board)
                db.session.flush()
                
                # Criar listas padrão para cada board
                listas_padrão = [
                    {'nome': 'Novos', 'ordem': 1, 'cor': '#F3F4F6'},
                    {'nome': 'Em Análise', 'ordem': 2, 'cor': '#DBEAFE'},
                    {'nome': 'Aguardando Documentos', 'ordem': 3, 'cor': '#FEF3C7'},
                    {'nome': 'Em Andamento', 'ordem': 4, 'cor': '#D1FAE5'},
                    {'nome': 'Concluído', 'ordem': 5, 'cor': '#D1FAE5'}
                ]
                
                for lista_data in listas_padrão:
                    lista = KanbanList(
                        quadro_id=board.id,
                        **lista_data
                    )
                    db.session.add(lista)
                
                boards.append(board)
        
        db.session.flush()
        print(f"✅ {len(boards)} quadros Kanban criados")
        
        # 7. Criar cartões de exemplo
        if boards:
            cartoes_exemplos = [
                {
                    'titulo': 'Analisar contestação',
                    'descricao': 'Revisar contestação apresentada pela parte adversa e preparar tréplica',
                    'prioridade': 'Alta',
                    'processo_id': processos[0].id if processos else None
                },
                {
                    'titulo': 'Protocolar petição inicial',
                    'descricao': 'Finalizar e protocolar a petição inicial do processo trabalhista',
                    'prioridade': 'Urgente',
                    'processo_id': processos[1].id if len(processos) > 1 else None
                },
                {
                    'titulo': 'Agendar audiência',
                    'descricao': 'Entrar em contato com o cartório para agendar audiência de conciliação',
                    'prioridade': 'Média',
                    'processo_id': processos[2].id if len(processos) > 2 else None
                }
            ]
            
            for i, cartao_data in enumerate(cartoes_exemplos):
                if i < len(boards) and boards[i].listas:
                    # Adicionar na primeira lista do board correspondente
                    lista = boards[i].listas[0]
                    cartao = KanbanCard(
                        lista_id=lista.id,
                        criado_por=admin.id,
                        ordem=i + 1,
                        data_limite=datetime.utcnow() + timedelta(days=random.randint(1, 30)),
                        **cartao_data
                    )
                    db.session.add(cartao)
                    
                    # Adicionar checklist de exemplo
                    checklist_items = [
                        'Revisar documentos',
                        'Analisar jurisprudência',
                        'Redigir minuta',
                        'Revisar com cliente'
                    ]
                    
                    for j, item_desc in enumerate(checklist_items):
                        db.session.flush()  # Para ter o ID do cartão
                        item = ChecklistItem(
                            cartao_id=cartao.id,
                            descricao=item_desc,
                            ordem=j + 1,
                            concluido=random.choice([True, False])
                        )
                        db.session.add(item)
        
        print("✅ Cartões e checklists criados")
        
        # 8. Criar itens da Wiki
        wiki_exemplos = [
            {
                'titulo': 'Prazos Processuais Cíveis',
                'categoria': 'Prazos',
                'texto': 'Resumo dos principais prazos do processo civil:\n\n- Contestação: 15 dias\n- Tréplica: 15 dias\n- Alegações finais: 15 dias\n- Recurso de apelação: 15 dias\n\nLembrar sempre de verificar os dias úteis e possíveis prorrogações.',
                'status': 'Publicado'
            },
            {
                'titulo': 'Modelo de Petição Inicial - Cobrança',
                'categoria': 'Modelos',
                'texto': 'Estrutura básica para petição inicial de cobrança:\n\n1. Qualificação das partes\n2. Dos fatos\n3. Do direito\n4. Dos pedidos\n5. Do valor da causa\n6. Das provas\n\nAtenção especial para a fundamentação legal e jurisprudencial.',
                'status': 'Publicado'
            },
            {
                'titulo': 'Jurisprudência - Danos Morais',
                'categoria': 'Jurisprudência',
                'texto': 'Principais entendimentos do STJ sobre danos morais:\n\n- Presunção de dano moral em casos específicos\n- Critérios para fixação do valor\n- Súmula 385 do STJ\n\nSempre verificar jurisprudência atualizada antes de utilizar.',
                'status': 'Publicado'
            }
        ]
        
        for wiki_data in wiki_exemplos:
            wiki_existente = Wiki.query.filter_by(titulo=wiki_data['titulo']).first()
            if not wiki_existente:
                wiki = Wiki(
                    autor_id=admin.id,
                    **wiki_data
                )
                db.session.add(wiki)
                db.session.flush()
                
                # Adicionar tags para os itens da wiki
                if 'Prazos' in wiki.titulo:
                    tag = WikiTag(wiki_id=wiki.id, tag='prazos')
                    db.session.add(tag)
                elif 'Modelo' in wiki.titulo:
                    tag = WikiTag(wiki_id=wiki.id, tag='modelos')
                    db.session.add(tag)
                elif 'Jurisprudência' in wiki.titulo:
                    tag = WikiTag(wiki_id=wiki.id, tag='jurisprudencia')
                    db.session.add(tag)
        
        print("✅ Itens da Wiki criados")
        
        # 9. Criar notificações de exemplo
        notificacoes_exemplos = [
            {
                'tipo': 'Prazo',
                'titulo': 'Prazo para contestação vencendo',
                'mensagem': 'O prazo para apresentar contestação no processo 1234567-89.2024.8.26.0100 vence em 3 dias.',
                'prioridade': 'Alta'
            },
            {
                'tipo': 'Tarefa',
                'titulo': 'Nova tarefa atribuída',
                'mensagem': 'Uma nova tarefa foi criada no quadro Processos Cíveis.',
                'prioridade': 'Normal'
            },
            {
                'tipo': 'Wiki',
                'titulo': 'Novo conteúdo na Wiki',
                'mensagem': 'Um novo item foi adicionado à categoria Jurisprudência.',
                'prioridade': 'Baixa'
            }
        ]
        
        for notif_data in notificacoes_exemplos:
            notificacao = Notification(
                usuario_id=admin.id,
                **notif_data
            )
            db.session.add(notificacao)
        
        print("✅ Notificações criadas")
        
        # Commit final
        db.session.commit()
        
        print("\n🎉 Sistema completo inicializado com sucesso!")
        print("\n📊 Resumo dos dados criados:")
        print(f"   👤 Usuários: 1 (admin@jurisia.com)")
        print(f"   🏢 Clientes: {len(clientes)}")
        print(f"   📁 Processos: {len(processos)}")
        print(f"   📋 Quadros Kanban: {len(boards)}")
        print(f"   📚 Itens Wiki: {len(wiki_exemplos)}")
        print(f"   🔔 Notificações: {len(notificacoes_exemplos)}")
        print(f"   🏷️ Tags: {len(tags_criadas)}")
        
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
    
    print("🚀 Inicializando sistema JurisIA com dados completos...")
    
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