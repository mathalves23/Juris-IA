#!/usr/bin/env python3
"""
Script para inicializar o banco de dados do JurisIA MVP
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import create_app
from src.extensions import db

def init_database():
    """Inicializa o banco de dados criando todas as tabelas"""
    
    app = create_app()
    
    with app.app_context():
        # Importar todos os modelos para garantir que sejam registrados
        from src.models.user import User
        from src.models.template import Template
        from src.models.document import Document
        from src.models.subscription import Subscription
        
        print("Criando banco de dados...")
        
        # Remover todas as tabelas existentes
        db.drop_all()
        print("Tabelas antigas removidas.")
        
        # Criar todas as tabelas
        db.create_all()
        print("Novas tabelas criadas.")
        
        # Criar usuário demo para o MVP
        demo_user = User(
            nome='Advogado Demo',
            email='advogado@jurisia.com',
            senha='123456',
            papel='usuario'
        )
        
        db.session.add(demo_user)
        db.session.commit()
        
        # Criar assinatura demo
        demo_subscription = Subscription(
            usuario_id=demo_user.id,
            plano='editor_ia',
            status='ativo',
            limite_documentos=50,
            documentos_utilizados=0
        )
        
        db.session.add(demo_subscription)
        db.session.commit()
        
        # Criar templates iniciais
        templates_iniciais = [
            {
                'titulo': 'Petição Inicial Cível',
                'categoria': 'Cível',
                'conteudo': '''EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA {VARA_COMPETENTE}

{NOME_AUTOR}, {QUALIFICACAO_AUTOR}, vem, respeitosamente, por meio de seu advogado que esta subscreve, com fundamento nos artigos {ARTIGOS_FUNDAMENTO}, propor

AÇÃO {TIPO_ACAO}

em face de {NOME_REU}, {QUALIFICACAO_REU}, pelos fatos e fundamentos jurídicos a seguir expostos:

I - DOS FATOS

{RELATO_FATOS}

II - DO DIREITO

{FUNDAMENTACAO_JURIDICA}

III - DOS PEDIDOS

Ante o exposto, requer-se:

a) {PEDIDO_PRINCIPAL};
b) A condenação do requerido ao pagamento das custas processuais e honorários advocatícios;
c) {OUTROS_PEDIDOS}.

Dá-se à causa o valor de R$ {VALOR_CAUSA}.

Termos em que,
Pede deferimento.

{CIDADE}, {DATA}.

{NOME_ADVOGADO}
OAB/{UF} {NUMERO_OAB}''',
                'publico': True
            },
            {
                'titulo': 'Contestação',
                'categoria': 'Cível',
                'conteudo': '''EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA {VARA_COMPETENTE}

{NOME_REU}, já qualificado nos autos da ação {TIPO_ACAO} que lhe move {NOME_AUTOR}, vem, respeitosamente, por intermédio de seu advogado signatário, tempestivamente, apresentar

CONTESTAÇÃO

pelos fatos e fundamentos jurídicos que passa a expor:

I - DAS PRELIMINARES

{PRELIMINARES}

II - DO MÉRITO

{DEFESA_MERITO}

III - DO DIREITO

{FUNDAMENTACAO_JURIDICA}

IV - DOS PEDIDOS

Ante o exposto, requer-se:

a) O acolhimento das preliminares arguidas;
b) No mérito, a total improcedência da ação;
c) A condenação do autor ao pagamento das custas processuais e honorários advocatícios.

Protesta por todos os meios de prova em direito admitidos.

Termos em que,
Pede deferimento.

{CIDADE}, {DATA}.

{NOME_ADVOGADO}
OAB/{UF} {NUMERO_OAB}''',
                'publico': True
            },
            {
                'titulo': 'Recurso de Apelação',
                'categoria': 'Recursal',
                'conteudo': '''EXCELENTÍSSIMO(A) SENHOR(A) DESEMBARGADOR(A) RELATOR(A)

{NOME_APELANTE}, nos autos da ação {TIPO_ACAO} em curso perante a {VARA_ORIGEM}, vem, respeitosamente, por seu advogado signatário, tempestivamente, interpor

RECURSO DE APELAÇÃO

em face da r. sentença de fls. {FOLHAS_SENTENCA}, pelos fundamentos que passa a expor:

I - DO CABIMENTO

O presente recurso é cabível, tempestivo e adequado, nos termos do art. 1009 do CPC.

II - DOS FUNDAMENTOS

{FUNDAMENTOS_RECURSO}

III - DO DIREITO

{FUNDAMENTACAO_JURIDICA}

IV - DOS PEDIDOS

Ante o exposto, requer-se:

a) O conhecimento e provimento do presente recurso;
b) {PEDIDO_PRINCIPAL};
c) {OUTROS_PEDIDOS}.

Termos em que,
Pede deferimento.

{CIDADE}, {DATA}.

{NOME_ADVOGADO}
OAB/{UF} {NUMERO_OAB}''',
                'publico': True
            },
            {
                'titulo': 'Habeas Corpus',
                'categoria': 'Criminal',
                'conteudo': '''EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) DESEMBARGADOR(A) PRESIDENTE DO EGRÉGIO TRIBUNAL DE JUSTIÇA

{NOME_IMPETRANTE}, {QUALIFICACAO_IMPETRANTE}, por seu advogado signatário, vem, respeitosamente, impetrar

HABEAS CORPUS

em favor de {NOME_PACIENTE}, {QUALIFICACAO_PACIENTE}, contra ato do(a) {AUTORIDADE_COATORA}, pelos fatos e fundamentos jurídicos que passa a expor:

I - DA COMPETÊNCIA

Este Egrégio Tribunal é competente para processar e julgar o presente writ, nos termos do art. {ARTIGO_COMPETENCIA}.

II - DOS FATOS

{RELATO_FATOS}

III - DO DIREITO VIOLADO OU AMEAÇADO

{FUNDAMENTACAO_JURIDICA}

IV - DA ILEGALIDADE OU ABUSO DE PODER

{DEMONSTRACAO_ILEGALIDADE}

V - DOS PEDIDOS

Ante o exposto, requer-se:

a) A concessão da ordem para {PEDIDO_PRINCIPAL};
b) {OUTROS_PEDIDOS}.

Termos em que,
Pede deferimento.

{CIDADE}, {DATA}.

{NOME_ADVOGADO}
OAB/{UF} {NUMERO_OAB}''',
                'publico': True
            },
            {
                'titulo': 'Mandado de Segurança',
                'categoria': 'Constitucional',
                'conteudo': '''EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO

{NOME_IMPETRANTE}, {QUALIFICACAO_IMPETRANTE}, vem, respeitosamente, por intermédio de seu advogado signatário, impetrar

MANDADO DE SEGURANÇA

contra ato do(a) {AUTORIDADE_COATORA}, {QUALIFICACAO_AUTORIDADE}, pelos fatos e fundamentos que passa a expor:

I - DA COMPETÊNCIA

Este MM. Juízo é competente para processar e julgar o presente writ, nos termos do art. {ARTIGO_COMPETENCIA}.

II - DOS FATOS

{RELATO_FATOS}

III - DO DIREITO LÍQUIDO E CERTO

{DEMONSTRACAO_DIREITO_LIQUIDO_CERTO}

IV - DA ILEGALIDADE OU ABUSO DE PODER

{FUNDAMENTACAO_ILEGALIDADE}

V - DOS PEDIDOS

Ante o exposto, requer-se:

a) A concessão da segurança para {PEDIDO_PRINCIPAL};
b) {OUTROS_PEDIDOS}.

Termos em que,
Pede deferimento.

{CIDADE}, {DATA}.

{NOME_ADVOGADO}
OAB/{UF} {NUMERO_OAB}''',
                'publico': True
            }
        ]
        
        # Inserir templates no banco
        for template_data in templates_iniciais:
            template = Template(
                titulo=template_data['titulo'],
                categoria=template_data['categoria'],
                conteudo=template_data['conteudo'],
                usuario_id=demo_user.id,
                publico=template_data['publico']
            )
            db.session.add(template)
        
        db.session.commit()
        
        print("Usuário demo criado:")
        print("  Email: advogado@jurisia.com")
        print("  Senha: 123456")
        print("  Plano: editor_ia")
        print("  Limite de documentos: 50")
        print(f"  Templates criados: {len(templates_iniciais)}")
        
        print("\nBanco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_database() 