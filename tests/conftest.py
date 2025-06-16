import pytest
import tempfile
import os
from src.main import create_app
from src.extensions import db
from src.models.user import User
from src.models.template import Template
from src.models.document import Document
from flask_jwt_extended import create_access_token
import json
from flask import Flask
from flask_testing import TestCase

# Configurar variáveis de ambiente para testes
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
os.environ['SECRET_KEY'] = 'test-secret'

@pytest.fixture
def app():
    """Fixture para criar app de teste"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Fixture para cliente de teste"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Fixture para runner CLI"""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers(client):
    """Fixture para headers de autenticação"""
    # Criar usuário de teste
    client.post('/api/auth/register', json={
        'nome': 'Teste User',
        'email': 'teste@jurisia.com',
        'senha': 'teste123'
    })
    
    # Fazer login
    response = client.post('/api/auth/login', json={
        'email': 'teste@jurisia.com',
        'senha': 'teste123'
    })
    
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

class BaseTestCase(TestCase):
    """Classe base para casos de teste"""
    
    def create_app(self):
        return create_app()
    
    def setUp(self):
        db.create_all()
        self.create_test_data()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
    
    def create_test_data(self):
        """Criar dados de teste padrão"""
        pass

@pytest.fixture
def sample_template():
    """Template de exemplo para testes."""
    return {
        'titulo': 'Contrato de Prestação de Serviços',
        'conteudo': '''
        CONTRATO DE PRESTAÇÃO DE SERVIÇOS

        Por este instrumento particular de contrato, as partes:

        CONTRATANTE: [NOME], [QUALIFICAÇÃO]
        CONTRATADO: [NOME], [QUALIFICAÇÃO]

        Têm entre si, justo e acordado o seguinte:

        CLÁUSULA 1ª - DO OBJETO
        O presente contrato tem por objeto a prestação de serviços de [DESCRIÇÃO].

        CLÁUSULA 2ª - DO VALOR
        O valor dos serviços será de R$ [VALOR].

        CLÁUSULA 3ª - DO PRAZO
        O prazo para execução dos serviços será de [PRAZO] dias.
        ''',
        'categoria': 'Contratos',
        'publico': True
    }


@pytest.fixture
def sample_document():
    """Documento de exemplo para testes."""
    return {
        'titulo': 'Petição Inicial - Ação de Cobrança',
        'conteudo': '''
        EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO

        [NOME DO AUTOR], por seus advogados que esta subscrevem, vem, respeitosamente,
        perante Vossa Excelência, propor a presente

        AÇÃO DE COBRANÇA

        em face de [NOME DO RÉU], pelos fatos e fundamentos jurídicos a seguir expostos:

        DOS FATOS

        O autor celebrou contrato de prestação de serviços com o réu...
        ''',
        'status': 'rascunho'
    }


class TestDataFactory:
    """Factory para criar dados de teste."""
    
    @staticmethod
    def create_user(nome='Test User', email='test@example.com', senha='test123'):
        """Criar usuário de teste."""
        import hashlib
        senha_hash = hashlib.pbkdf2_hmac('sha256', senha.encode(), b'salt', 100000).hex()
        
        user = User(
            nome=nome,
            email=email,
            senha_hash=senha_hash
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def create_template(user_id, titulo='Template Teste', categoria='Geral'):
        """Criar template de teste."""
        template = Template(
            titulo=titulo,
            conteudo='Conteúdo do template de teste',
            categoria=categoria,
            publico=False,
            usuario_id=user_id
        )
        db.session.add(template)
        db.session.commit()
        return template
    
    @staticmethod
    def create_document(user_id, titulo='Documento Teste', template_id=None):
        """Criar documento de teste."""
        document = Document(
            titulo=titulo,
            conteudo='Conteúdo do documento de teste',
            status='rascunho',
            usuario_id=user_id,
            template_id=template_id
        )
        db.session.add(document)
        db.session.commit()
        return document


@pytest.fixture
def test_factory():
    """Factory de dados de teste."""
    return TestDataFactory 