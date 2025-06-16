import pytest
import json
from tests.conftest import BaseTestCase
from src.models.user import User
from src.extensions import db

class TestAuth(BaseTestCase):
    """Testes para sistema de autenticação"""
    
    def test_register_success(self):
        """Teste de registro bem-sucedido"""
        response = self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Usuário criado com sucesso')
        
        # Verificar se usuário foi criado no banco
        user = User.query.filter_by(email='joao@teste.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.nome, 'João Silva')
    
    def test_register_duplicate_email(self):
        """Teste de registro com email duplicado"""
        # Primeiro registro
        self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        # Segundo registro com mesmo email
        response = self.client.post('/api/auth/register', 
            json={
                'nome': 'Maria Silva',
                'email': 'joao@teste.com',
                'senha': 'outrasenha'
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_register_invalid_data(self):
        """Teste de registro com dados inválidos"""
        # Email inválido
        response = self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'email_invalido',
                'senha': 'senha123'
            }
        )
        self.assertEqual(response.status_code, 400)
        
        # Senha muito curta
        response = self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': '123'
            }
        )
        self.assertEqual(response.status_code, 400)
        
        # Nome vazio
        response = self.client.post('/api/auth/register', 
            json={
                'nome': '',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        self.assertEqual(response.status_code, 400)
    
    def test_login_success(self):
        """Teste de login bem-sucedido"""
        # Criar usuário
        self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        # Fazer login
        response = self.client.post('/api/auth/login', 
            json={
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'joao@teste.com')
    
    def test_login_invalid_credentials(self):
        """Teste de login com credenciais inválidas"""
        # Criar usuário
        self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        # Login com senha errada
        response = self.client.post('/api/auth/login', 
            json={
                'email': 'joao@teste.com',
                'senha': 'senhaerrada'
            }
        )
        
        self.assertEqual(response.status_code, 401)
        
        # Login com email inexistente
        response = self.client.post('/api/auth/login', 
            json={
                'email': 'inexistente@teste.com',
                'senha': 'senha123'
            }
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_user_profile(self):
        """Teste de obtenção do perfil do usuário"""
        # Criar usuário e fazer login
        self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        login_response = self.client.post('/api/auth/login', 
            json={
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        token = json.loads(login_response.data)['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Obter perfil
        response = self.client.get('/api/auth/me', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'], 'joao@teste.com')
        self.assertEqual(data['nome'], 'João Silva')
    
    def test_update_profile(self):
        """Teste de atualização do perfil"""
        # Criar usuário e fazer login
        self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        login_response = self.client.post('/api/auth/login', 
            json={
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        token = json.loads(login_response.data)['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Atualizar perfil
        response = self.client.put('/api/auth/me', 
            json={'nome': 'João Santos'},
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar se foi atualizado
        profile_response = self.client.get('/api/auth/me', headers=headers)
        data = json.loads(profile_response.data)
        self.assertEqual(data['nome'], 'João Santos')
    
    def test_refresh_token(self):
        """Teste de renovação de token"""
        # Criar usuário e fazer login
        self.client.post('/api/auth/register', 
            json={
                'nome': 'João Silva',
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        login_response = self.client.post('/api/auth/login', 
            json={
                'email': 'joao@teste.com',
                'senha': 'senha123'
            }
        )
        
        refresh_token = json.loads(login_response.data)['refresh_token']
        headers = {'Authorization': f'Bearer {refresh_token}'}
        
        # Renovar token
        response = self.client.post('/api/auth/refresh', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
    
    def test_unauthorized_access(self):
        """Teste de acesso não autorizado"""
        # Tentar acessar rota protegida sem token
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, 401)
        
        # Tentar acessar com token inválido
        headers = {'Authorization': 'Bearer token_invalido'}
        response = self.client.get('/api/auth/me', headers=headers)
        self.assertEqual(response.status_code, 422)

if __name__ == '__main__':
    pytest.main([__file__]) 