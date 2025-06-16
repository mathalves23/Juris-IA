#!/bin/bash

# Script de teste de integração para o Editor IA JurisSaaS
# Este script executa testes básicos de integração entre backend e frontend

echo "Iniciando testes de integração para o Editor IA JurisSaaS..."

# Verificar se está no diretório correto
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
  echo "Erro: Execute este script no diretório raiz do projeto (onde estão as pastas backend e frontend)"
  exit 1
fi

# Definir variáveis para os testes
API_URL="http://localhost:5000/api"
TEST_EMAIL="teste@jurissaas.com.br"
TEST_PASSWORD="Teste@123"
TEST_NAME="Usuário Teste"

# Iniciar o backend em segundo plano
echo "Iniciando o backend para testes..."
cd backend
source venv/bin/activate
flask run > backend_test.log 2>&1 &
BACKEND_PID=$!

# Aguardar o backend iniciar
echo "Aguardando o backend inicializar..."
sleep 5

# Verificar se o backend está rodando
if ! curl -s "$API_URL/health" > /dev/null; then
  echo "Erro: Backend não está respondendo. Verifique o arquivo backend_test.log para mais detalhes."
  kill $BACKEND_PID
  exit 1
fi

echo "Backend iniciado com sucesso!"

# Executar testes de API
echo "Executando testes de integração da API..."

# Teste 1: Registro de usuário
echo "Teste 1: Registro de usuário"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"nome\":\"$TEST_NAME\",\"email\":\"$TEST_EMAIL\",\"senha\":\"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "error"; then
  echo "Falha no teste de registro: $REGISTER_RESPONSE"
else
  echo "Teste de registro bem-sucedido!"
  
  # Extrair token de acesso
  ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
  
  if [ -z "$ACCESS_TOKEN" ]; then
    echo "Não foi possível extrair o token de acesso."
  else
    echo "Token de acesso obtido com sucesso!"
    
    # Teste 2: Obter informações do usuário
    echo "Teste 2: Obter informações do usuário"
    USER_INFO_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$USER_INFO_RESPONSE" | grep -q "error"; then
      echo "Falha no teste de informações do usuário: $USER_INFO_RESPONSE"
    else
      echo "Teste de informações do usuário bem-sucedido!"
    fi
    
    # Teste 3: Criar um documento
    echo "Teste 3: Criar um documento"
    CREATE_DOC_RESPONSE=$(curl -s -X POST "$API_URL/documents" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"titulo\":\"Documento de Teste\",\"conteudo\":\"<p>Conteúdo de teste</p>\",\"status\":\"Rascunho\"}")
    
    if echo "$CREATE_DOC_RESPONSE" | grep -q "error"; then
      echo "Falha no teste de criação de documento: $CREATE_DOC_RESPONSE"
    else
      echo "Teste de criação de documento bem-sucedido!"
      
      # Extrair ID do documento
      DOC_ID=$(echo "$CREATE_DOC_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | sed 's/"id"://')
      
      if [ -z "$DOC_ID" ]; then
        echo "Não foi possível extrair o ID do documento."
      else
        echo "ID do documento obtido: $DOC_ID"
        
        # Teste 4: Obter documento
        echo "Teste 4: Obter documento"
        GET_DOC_RESPONSE=$(curl -s -X GET "$API_URL/documents/$DOC_ID" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        
        if echo "$GET_DOC_RESPONSE" | grep -q "error"; then
          echo "Falha no teste de obtenção de documento: $GET_DOC_RESPONSE"
        else
          echo "Teste de obtenção de documento bem-sucedido!"
        fi
        
        # Teste 5: Atualizar documento
        echo "Teste 5: Atualizar documento"
        UPDATE_DOC_RESPONSE=$(curl -s -X PUT "$API_URL/documents/$DOC_ID" \
          -H "Authorization: Bearer $ACCESS_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{\"titulo\":\"Documento de Teste Atualizado\",\"conteudo\":\"<p>Conteúdo de teste atualizado</p>\",\"status\":\"Rascunho\"}")
        
        if echo "$UPDATE_DOC_RESPONSE" | grep -q "error"; then
          echo "Falha no teste de atualização de documento: $UPDATE_DOC_RESPONSE"
        else
          echo "Teste de atualização de documento bem-sucedido!"
        fi
        
        # Teste 6: Gerar texto com IA
        echo "Teste 6: Gerar texto com IA"
        AI_RESPONSE=$(curl -s -X POST "$API_URL/ai/generate" \
          -H "Authorization: Bearer $ACCESS_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{\"prompt\":\"Escreva uma introdução sobre responsabilidade civil\",\"document_id\":$DOC_ID}")
        
        if echo "$AI_RESPONSE" | grep -q "error"; then
          echo "Falha no teste de geração de texto com IA: $AI_RESPONSE"
        else
          echo "Teste de geração de texto com IA bem-sucedido!"
        fi
        
        # Teste 7: Excluir documento
        echo "Teste 7: Excluir documento"
        DELETE_DOC_RESPONSE=$(curl -s -X DELETE "$API_URL/documents/$DOC_ID" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        
        if echo "$DELETE_DOC_RESPONSE" | grep -q "error"; then
          echo "Falha no teste de exclusão de documento: $DELETE_DOC_RESPONSE"
        else
          echo "Teste de exclusão de documento bem-sucedido!"
        fi
      fi
    fi
  fi
fi

# Encerrar o backend
echo "Encerrando o backend..."
kill $BACKEND_PID

echo "Testes de integração concluídos!"
echo "Verifique os resultados acima para identificar possíveis problemas."
