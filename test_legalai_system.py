#!/usr/bin/env python3
"""
Script de teste para o sistema de planos da LegalAI
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_api_connection():
    """Testar conexão com a API"""
    print("\n🔌 Testando conexão com a API...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ API está funcionando")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return False

def test_plans_endpoint():
    """Testar endpoint de planos"""
    print("\n📋 Testando endpoint de planos...")
    try:
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        if response.status_code == 200:
            data = response.json()
            plans = data.get('plans', [])
            print(f"✅ {len(plans)} planos encontrados")
            
            for plan in plans:
                print(f"  📄 {plan['name']} - R$ {plan['price_monthly']}/mês")
                if plan.get('is_popular'):
                    print("    🔥 POPULAR")
            
            return True
        else:
            print(f"❌ Erro ao buscar planos: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_user_login():
    """Testar login do usuário"""
    print("\n🔐 Testando login...")
    try:
        login_data = {
            "email": "advogado@legalai.com",
            "password": "123456"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            if token:
                print("✅ Login realizado com sucesso")
                return token
            else:
                print("❌ Token não encontrado na resposta")
                return None
        else:
            print(f"❌ Erro no login: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_subscription_endpoints(token):
    """Testar endpoints de assinatura"""
    print("\n📊 Testando endpoints de assinatura...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Testar assinatura atual
    try:
        response = requests.get(f"{BASE_URL}/api/subscriptions/current", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('has_subscription'):
                print("✅ Usuário já possui assinatura")
                subscription = data['subscription']
                print(f"  📄 Plano: {subscription['plan']['name']}")
                print(f"  🏃 Status: {subscription['status']}")
                print(f"  📅 Dias restantes: {subscription['days_remaining']}")
            else:
                print("ℹ️ Usuário não possui assinatura")
        else:
            print(f"❌ Erro ao verificar assinatura: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Testar estatísticas de uso
    try:
        response = requests.get(f"{BASE_URL}/api/subscriptions/usage", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Estatísticas de uso obtidas")
            print(f"  📄 Documentos: {data['documents']['used']}/{data['documents']['limit']}")
            print(f"  📝 Templates: {data['templates']['used']}/{data['templates']['limit']}")
            print(f"  🤖 IA: {data['ai_requests']['used']}/{data['ai_requests']['limit']}")
        else:
            print(f"❌ Erro ao obter uso: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_create_subscription(token):
    """Testar criação de assinatura"""
    print("\n🆕 Testando criação de assinatura...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Primeiro, obter lista de planos
    try:
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        if response.status_code == 200:
            plans = response.json()['plans']
            if plans:
                # Usar o primeiro plano para teste
                plan_id = plans[0]['id']
                
                subscription_data = {
                    "plan_id": plan_id,
                    "is_annual": False,
                    "payment_method": "credit_card"
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/subscriptions/subscribe", 
                    json=subscription_data,
                    headers=headers
                )
                
                if response.status_code == 201:
                    print("✅ Assinatura criada com sucesso")
                    data = response.json()
                    subscription = data['subscription']
                    print(f"  📄 Plano: {subscription['plan']['name']}")
                    print(f"  🏃 Status: {subscription['status']}")
                    print(f"  🎁 Trial: {subscription['is_trial']}")
                elif response.status_code == 400:
                    print("ℹ️ Usuário já possui assinatura ativa")
                else:
                    print(f"❌ Erro ao criar assinatura: {response.status_code}")
                    print(f"Response: {response.text}")
            else:
                print("❌ Nenhum plano encontrado")
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_ai_limits(token):
    """Testar limites de IA"""
    print("\n🤖 Testando limites de IA...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        ai_data = {
            "prompt": "Gere um contrato de prestação de serviços",
            "document_type": "contrato"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json=ai_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Solicitação de IA processada com sucesso")
        elif response.status_code == 429:
            print("⚠️ Limite de IA atingido (esperado)")
        elif response.status_code == 403:
            print("⚠️ Funcionalidade não disponível no plano atual")
        else:
            print(f"❌ Erro na IA: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_document_limits(token):
    """Testar limites de documentos"""
    print("\n📄 Testando limites de documentos...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        doc_data = {
            "titulo": f"Documento de Teste {datetime.now().strftime('%H:%M:%S')}",
            "conteudo": "Este é um documento de teste para verificar os limites.",
            "status": "Rascunho"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/documents/",
            json=doc_data,
            headers=headers
        )
        
        if response.status_code == 201:
            print("✅ Documento criado com sucesso")
        elif response.status_code == 429:
            print("⚠️ Limite de documentos atingido")
        elif response.status_code == 403:
            print("⚠️ Assinatura necessária")
        else:
            print(f"❌ Erro ao criar documento: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DO SISTEMA LEGALAI")
    print("=" * 50)
    
    # Teste 1: Conexão com API
    if not test_api_connection():
        print("\n❌ Teste falhou na conexão com a API")
        return
    
    # Teste 2: Endpoint de planos
    if not test_plans_endpoint():
        print("\n❌ Teste falhou no endpoint de planos")
        return
    
    # Teste 3: Login
    token = test_user_login()
    if not token:
        print("\n❌ Teste falhou no login")
        return
    
    # Teste 4: Endpoints de assinatura
    test_subscription_endpoints(token)
    
    # Teste 5: Criar assinatura (se necessário)
    test_create_subscription(token)
    
    # Teste 6: Limites de IA
    test_ai_limits(token)
    
    # Teste 7: Limites de documentos
    test_document_limits(token)
    
    print("\n" + "=" * 50)
    print("🎉 TESTES CONCLUÍDOS")
    print("\n💡 Próximos passos:")
    print("   1. Acesse http://localhost:3000/pricing para ver a página de planos")
    print("   2. Teste a criação de assinaturas no frontend")
    print("   3. Verifique os limites em ação")

if __name__ == "__main__":
    main() 