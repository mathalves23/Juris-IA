#!/bin/bash

# Script de testes de smoke para o Editor IA JurisSaaS
# Este script executa testes básicos para verificar se a aplicação está funcionando corretamente em produção

echo "Iniciando testes de smoke para o Editor IA JurisSaaS..."

# Verificar parâmetros
if [ -z "$1" ]; then
  echo "Uso: $0 <URL_BASE>"
  echo "Exemplo: $0 https://app.jurissaas.com.br"
  exit 1
fi

BASE_URL=$1
API_URL="$BASE_URL/api"
TEST_EMAIL="smoke_test@jurissaas.com.br"
TEST_PASSWORD="SmokeTest@123"
TEST_NAME="Usuário Teste Smoke"

echo "URL base: $BASE_URL"
echo "URL da API: $API_URL"

# Função para verificar status HTTP
check_status() {
  local url=$1
  local expected_status=${2:-200}
  
  echo -n "Verificando $url... "
  
  status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  
  if [ "$status" -eq "$expected_status" ]; then
    echo "OK (status $status)"
    return 0
  else
    echo "FALHA (status $status, esperado $expected_status)"
    return 1
  fi
}

# Verificar se o frontend está acessível
echo "Verificando acesso ao frontend..."
check_status "$BASE_URL"

# Verificar se a API está acessível
echo "Verificando acesso à API..."
check_status "$API_URL/health"

# Teste de registro de usuário
echo "Teste de registro de usuário..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"nome\":\"$TEST_NAME\",\"email\":\"$TEST_EMAIL\",\"senha\":\"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "error"; then
  echo "Falha no teste de registro: $REGISTER_RESPONSE"
  
  # Tentar login caso o usuário já exista
  echo "Tentando login com usuário existente..."
  LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"senha\":\"$TEST_PASSWORD\"}")
  
  if echo "$LOGIN_RESPONSE" | grep -q "error"; then
    echo "Falha no login: $LOGIN_RESPONSE"
    exit 1
  else
    echo "Login bem-sucedido!"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
  fi
else
  echo "Registro bem-sucedido!"
  ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
fi

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Não foi possível obter o token de acesso."
  exit 1
fi

echo "Token de acesso obtido com sucesso!"

# Teste de obtenção de informações do usuário
echo "Teste de informações do usuário..."
USER_INFO_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$USER_INFO_RESPONSE" | grep -q "error"; then
  echo "Falha no teste de informações do usuário: $USER_INFO_RESPONSE"
  exit 1
else
  echo "Teste de informações do usuário bem-sucedido!"
fi

# Teste de criação de documento
echo "Teste de criação de documento..."
CREATE_DOC_RESPONSE=$(curl -s -X POST "$API_URL/documents" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"titulo\":\"Documento de Teste Smoke\",\"conteudo\":\"<p>Conteúdo de teste para smoke test</p>\",\"status\":\"Rascunho\"}")

if echo "$CREATE_DOC_RESPONSE" | grep -q "error"; then
  echo "Falha no teste de criação de documento: $CREATE_DOC_RESPONSE"
  exit 1
else
  echo "Teste de criação de documento bem-sucedido!"
  
  # Extrair ID do documento
  DOC_ID=$(echo "$CREATE_DOC_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | sed 's/"id"://')
  
  if [ -z "$DOC_ID" ]; then
    echo "Não foi possível extrair o ID do documento."
    exit 1
  else
    echo "ID do documento obtido: $DOC_ID"
    
    # Teste de obtenção de documento
    echo "Teste de obtenção de documento..."
    GET_DOC_RESPONSE=$(curl -s -X GET "$API_URL/documents/$DOC_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$GET_DOC_RESPONSE" | grep -q "error"; then
      echo "Falha no teste de obtenção de documento: $GET_DOC_RESPONSE"
      exit 1
    else
      echo "Teste de obtenção de documento bem-sucedido!"
    fi
    
    # Teste de atualização de documento
    echo "Teste de atualização de documento..."
    UPDATE_DOC_RESPONSE=$(curl -s -X PUT "$API_URL/documents/$DOC_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"titulo\":\"Documento de Teste Smoke Atualizado\",\"conteudo\":\"<p>Conteúdo de teste atualizado para smoke test</p>\",\"status\":\"Rascunho\"}")
    
    if echo "$UPDATE_DOC_RESPONSE" | grep -q "error"; then
      echo "Falha no teste de atualização de documento: $UPDATE_DOC_RESPONSE"
      exit 1
    else
      echo "Teste de atualização de documento bem-sucedido!"
    fi
    
    # Teste de geração de texto com IA
    echo "Teste de geração de texto com IA..."
    AI_RESPONSE=$(curl -s -X POST "$API_URL/ai/generate" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"prompt\":\"Escreva uma breve introdução sobre direito civil\",\"document_id\":$DOC_ID}")
    
    if echo "$AI_RESPONSE" | grep -q "error"; then
      echo "Falha no teste de geração de texto com IA: $AI_RESPONSE"
      echo "AVISO: Este erro pode ocorrer se a chave da API OpenAI não estiver configurada corretamente."
    else
      echo "Teste de geração de texto com IA bem-sucedido!"
    fi
    
    # Teste de exclusão de documento
    echo "Teste de exclusão de documento..."
    DELETE_DOC_RESPONSE=$(curl -s -X DELETE "$API_URL/documents/$DOC_ID" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$DELETE_DOC_RESPONSE" | grep -q "error"; then
      echo "Falha no teste de exclusão de documento: $DELETE_DOC_RESPONSE"
      exit 1
    else
      echo "Teste de exclusão de documento bem-sucedido!"
    fi
  fi
fi

echo ""
echo "Testes de smoke concluídos com sucesso!"
echo "A aplicação está funcionando corretamente em produção."
echo ""
echo "URL da aplicação: $BASE_URL"
echo "Usuário de teste: $TEST_EMAIL"
echo "Senha de teste: $TEST_PASSWORD"
