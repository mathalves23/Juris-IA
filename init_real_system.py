#!/usr/bin/env python3
"""
Script para inicializar o sistema JurisIA com dados reais
Cria banco de dados, usuário administrador e dados de exemplo
"""

import os
import sys
from datetime import datetime, timedelta

# Adicionar o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mudar para o diretório do projeto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Importar Flask app e extensões
from src.main import create_app
from src.extensions import db
from src.models.user import User
from src.models.document import Document
from src.models.template import Template
from src.models.subscription import Subscription
from flask_bcrypt import Bcrypt

def init_database():
    """Inicializa o banco de dados"""
    print("🗄️ Inicializando banco de dados...")
    
    app = create_app()
    bcrypt = Bcrypt(app)
    
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        print("✅ Tabelas criadas com sucesso")
        
        # Verificar se já existe usuário admin
        admin_user = User.query.filter_by(email='admin@jurisia.com').first()
        
        if not admin_user:
            # Criar usuário administrador
            admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_user = User(
                nome='Administrador JurisIA',
                email='admin@jurisia.com',
                senha=admin_password,
                telefone='(11) 99999-9999',
                oab='123456/SP',
                is_admin=True,
                email_verified=True
            )
            db.session.add(admin_user)
            print("✅ Usuário administrador criado (admin@jurisia.com / admin123)")
        else:
            print("ℹ️ Usuário administrador já existe")
        
        # Criar usuário de teste
        test_user = User.query.filter_by(email='advogado@jurisia.com').first()
        
        if not test_user:
            test_password = bcrypt.generate_password_hash('123456').decode('utf-8')
            test_user = User(
                nome='Dr. João Silva',
                email='advogado@jurisia.com',
                senha=test_password,
                telefone='(11) 98765-4321',
                oab='654321/SP',
                email_verified=True
            )
            db.session.add(test_user)
            print("✅ Usuário de teste criado (advogado@jurisia.com / 123456)")
        else:
            print("ℹ️ Usuário de teste já existe")
        
        # Commit usuários primeiro
        db.session.commit()
        
        # Criar documentos de exemplo
        create_sample_documents(test_user.id)
        
        # Criar templates de exemplo
        create_sample_templates(test_user.id)
        
        # Criar assinatura para o usuário de teste
        create_sample_subscription(test_user.id)
        
        # Commit final
        db.session.commit()
        print("🎉 Sistema inicializado com sucesso!")
        
        # Mostrar informações de login
        print("\n📋 INFORMAÇÕES DE LOGIN:")
        print("=" * 50)
        print("🔐 Administrador:")
        print("   Email: admin@jurisia.com")
        print("   Senha: admin123")
        print("\n👤 Usuário de Teste:")
        print("   Email: advogado@jurisia.com")
        print("   Senha: 123456")
        print("=" * 50)

def create_sample_documents(user_id):
    """Cria documentos de exemplo"""
    print("📄 Criando documentos de exemplo...")
    
    # Verificar se já existem documentos
    if Document.query.filter_by(usuario_id=user_id).count() > 0:
        print("ℹ️ Documentos já existem")
        return
    
    documents = [
        {
            'titulo': 'Contrato de Prestação de Serviços',
            'conteudo': '''<h2>CONTRATO DE PRESTAÇÃO DE SERVIÇOS</h2>
            
<p><strong>CONTRATANTE:</strong> {{nome_contratante}}, {{qualificacao_contratante}}</p>
<p><strong>CONTRATADO:</strong> {{nome_contratado}}, {{qualificacao_contratado}}</p>

<h3>1. DO OBJETO</h3>
<p>O presente contrato tem por objeto a prestação de serviços de {{tipo_servico}}, conforme especificações detalhadas no Anexo I.</p>

<h3>2. DO VALOR E FORMA DE PAGAMENTO</h3>
<p>O valor total dos serviços é de R$ {{valor_total}}, a ser pago da seguinte forma: {{forma_pagamento}}.</p>

<h3>3. DO PRAZO</h3>
<p>O prazo para execução dos serviços é de {{prazo_execucao}}, iniciando-se em {{data_inicio}}.</p>

<h3>4. DAS OBRIGAÇÕES</h3>
<p>São obrigações do CONTRATADO:</p>
<ul>
<li>Executar os serviços com qualidade e pontualidade;</li>
<li>Manter sigilo sobre informações confidenciais;</li>
<li>Cumprir os prazos estabelecidos.</li>
</ul>

<p>São obrigações do CONTRATANTE:</p>
<ul>
<li>Efetuar os pagamentos nas datas estabelecidas;</li>
<li>Fornecer informações necessárias para execução dos serviços;</li>
<li>Disponibilizar recursos conforme acordado.</li>
</ul>

<h3>5. FORO</h3>
<p>Fica eleito o foro de {{cidade_foro}} para dirimir quaisquer questões oriundas do presente contrato.</p>

<p>{{cidade}}, {{data_assinatura}}</p>

<p>_________________________<br>
{{nome_contratante}}<br>
CONTRATANTE</p>

<p>_________________________<br>
{{nome_contratado}}<br>
CONTRATADO</p>''',
            'status': 'Rascunho'
        },
        {
            'titulo': 'Petição Inicial - Ação de Cobrança',
            'conteudo': '''<h2>PETIÇÃO INICIAL</h2>
            
<p>Excelentíssimo Senhor Doutor Juiz de Direito da {{vara}} Vara Cível da Comarca de {{comarca}}.</p>

<p><strong>{{nome_autor}}</strong>, {{qualificacao_autor}}, vem, respeitosamente, perante Vossa Excelência, por meio de seu advogado signatário, propor a presente</p>

<h3 style="text-align: center;"><strong>AÇÃO DE COBRANÇA</strong></h3>

<p>em face de <strong>{{nome_reu}}</strong>, {{qualificacao_reu}}, pelos fatos e fundamentos jurídicos a seguir expostos:</p>

<h3>I - DOS FATOS</h3>
<p>1. O Requerente celebrou com o Requerido {{tipo_contrato}} em {{data_contrato}}, conforme documento anexo.</p>

<p>2. O valor total do débito é de R$ {{valor_divida}}, vencido em {{data_vencimento}}.</p>

<p>3. O Requerido foi devidamente notificado para pagamento, porém quedou-se inerte.</p>

<h3>II - DO DIREITO</h3>
<p>4. O art. 389 do Código Civil estabelece que não cumprida a obrigação, responde o devedor por perdas e danos.</p>

<p>5. A mora do devedor está caracterizada pelo vencimento da obrigação, conforme art. 397 do CC.</p>

<h3>III - DOS PEDIDOS</h3>
<p>Ante o exposto, requer:</p>
<ol>
<li>A citação do requerido para pagar a dívida ou contestar a ação;</li>
<li>A condenação ao pagamento de R$ {{valor_divida}}, com correção e juros;</li>
<li>A condenação nas custas e honorários advocatícios.</li>
</ol>

<p>Dá-se à causa o valor de R$ {{valor_causa}}.</p>

<p>Termos em que pede deferimento.</p>

<p>{{cidade}}, {{data_peticao}}.</p>

<p>_________________________<br>
{{nome_advogado}}<br>
OAB/{{estado}} {{numero_oab}}</p>''',
            'status': 'Em Revisão'
        },
        {
            'titulo': 'Parecer Jurídico - Análise Contratual',
            'conteudo': '''<h2>PARECER JURÍDICO</h2>

<p><strong>Consulente:</strong> {{nome_consulente}}</p>
<p><strong>Objeto:</strong> Análise de {{objeto_parecer}}</p>
<p><strong>Data:</strong> {{data_parecer}}</p>

<h3>1. RELATÓRIO</h3>
<p>Trata-se de consulta formulada por {{nome_consulente}} acerca de {{questao_juridica}}.</p>

<p>A consulta versa sobre {{detalhamento_questao}}, conforme documentação anexa.</p>

<h3>2. FUNDAMENTAÇÃO LEGAL</h3>
<p>A questão encontra respaldo na legislação brasileira, especificamente:</p>
<ul>
<li>{{lei_aplicavel_1}}</li>
<li>{{lei_aplicavel_2}}</li>
<li>{{jurisprudencia_aplicavel}}</li>
</ul>

<h3>3. ANÁLISE JURÍDICA</h3>
<p>Da análise dos documentos e da legislação aplicável, verifica-se que {{analise_principal}}.</p>

<p>Os riscos identificados são: {{riscos_identificados}}.</p>

<p>As oportunidades identificadas são: {{oportunidades}}.</p>

<h3>4. CONCLUSÃO</h3>
<p>Com base no exposto, opina-se que {{conclusao_parecer}}.</p>

<p>Recomenda-se {{recomendacoes}}.</p>

<p>É o parecer, s.m.j.</p>

<p>{{cidade}}, {{data_parecer}}.</p>

<p>_________________________<br>
{{nome_advogado}}<br>
OAB/{{estado}} {{numero_oab}}</p>''',
            'status': 'Finalizado'
        }
    ]
    
    for doc_data in documents:
        document = Document(
            titulo=doc_data['titulo'],
            conteudo=doc_data['conteudo'],
            status=doc_data['status'],
            usuario_id=user_id,
            data_criacao=datetime.utcnow(),
            data_atualizacao=datetime.utcnow()
        )
        db.session.add(document)
    
    print("✅ Documentos de exemplo criados")

def create_sample_templates(user_id):
    """Cria templates de exemplo"""
    print("📋 Criando templates de exemplo...")
    
    # Verificar se já existem templates
    if Template.query.filter_by(usuario_id=user_id).count() > 0:
        print("ℹ️ Templates já existem")
        return
    
    templates = [
        {
            'nome': 'Contrato de Locação Residencial',
            'categoria': 'Contratos',
            'conteudo': '''<h2>CONTRATO DE LOCAÇÃO RESIDENCIAL</h2>

<p><strong>LOCADOR:</strong> {{nome_locador}}, {{qualificacao_locador}}</p>
<p><strong>LOCATÁRIO:</strong> {{nome_locatario}}, {{qualificacao_locatario}}</p>

<h3>CLÁUSULA 1ª - DO OBJETO</h3>
<p>O LOCADOR dá em locação ao LOCATÁRIO o imóvel situado na {{endereco_imovel}}.</p>

<h3>CLÁUSULA 2ª - DO PRAZO</h3>
<p>A locação é por prazo determinado de {{prazo_locacao}}, com início em {{data_inicio}}.</p>

<h3>CLÁUSULA 3ª - DO ALUGUEL</h3>
<p>O valor mensal do aluguel é de R$ {{valor_aluguel}}, vencível todo dia {{dia_vencimento}}.</p>

<h3>CLÁUSULA 4ª - DO DEPÓSITO CAUÇÃO</h3>
<p>O LOCATÁRIO depositará a quantia de R$ {{valor_caucao}} como garantia.</p>''',
            'variaveis': {
                'nome_locador': '',
                'nome_locatario': '',
                'endereco_imovel': '',
                'prazo_locacao': '',
                'valor_aluguel': '',
                'dia_vencimento': '',
                'valor_caucao': ''
            }
        },
        {
            'nome': 'Procuração Ad Judicia',
            'categoria': 'Procurações',
            'conteudo': '''<h2>PROCURAÇÃO</h2>

<p><strong>OUTORGANTE:</strong> {{nome_outorgante}}, {{qualificacao_outorgante}}</p>

<p><strong>OUTORGADO:</strong> {{nome_outorgado}}, {{qualificacao_outorgado}}, inscrito na OAB/{{estado}} sob o nº {{numero_oab}}</p>

<p>Por este instrumento particular de procuração, o OUTORGANTE nomeia e constitui seu bastante procurador o OUTORGADO, para representá-lo perante {{orgaos_representacao}}, podendo:</p>

<ul>
<li>Propor ações e defendê-lo em juízo;</li>
<li>Transigir, acordar e desistir;</li>
<li>Substabelecer esta procuração;</li>
<li>Praticar todos os atos necessários ao bom desempenho do mandato.</li>
</ul>

<p>{{cidade}}, {{data_procuracao}}.</p>

<p>_________________________<br>
{{nome_outorgante}}<br>
OUTORGANTE</p>''',
            'variaveis': {
                'nome_outorgante': '',
                'qualificacao_outorgante': '',
                'nome_outorgado': '',
                'qualificacao_outorgado': '',
                'estado': '',
                'numero_oab': '',
                'orgaos_representacao': '',
                'cidade': '',
                'data_procuracao': ''
            }
        }
    ]
    
    for template_data in templates:
        template = Template(
            nome=template_data['nome'],
            categoria=template_data['categoria'],
            conteudo=template_data['conteudo'],
            variaveis=template_data.get('variaveis', {}),
            usuario_id=user_id,
            data_criacao=datetime.utcnow()
        )
        db.session.add(template)
    
    print("✅ Templates de exemplo criados")

def create_sample_subscription(user_id):
    """Cria assinatura de exemplo"""
    print("💳 Criando assinatura de exemplo...")
    
    # Verificar se já existe assinatura
    if Subscription.query.filter_by(user_id=user_id).first():
        print("ℹ️ Assinatura já existe")
        return
    
    subscription = Subscription(
        user_id=user_id,
        plan_type='premium',
        status='active',
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=365),  # 1 ano
        auto_renew=True
    )
    db.session.add(subscription)
    print("✅ Assinatura premium criada (1 ano)")

if __name__ == '__main__':
    try:
        print("🚀 Iniciando configuração do sistema JurisIA...")
        init_database()
        print("\n🎯 Sistema pronto para uso!")
        print("\n🌐 Para iniciar o backend:")
        print("   python main.py")
        print("\n🌐 Para iniciar o frontend:")
        print("   cd frontend && npm start")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema: {e}")
        sys.exit(1) 