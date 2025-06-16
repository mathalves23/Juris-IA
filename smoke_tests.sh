#!/bin/bash

# Script de testes de smoke para validação crítica do sistema JurisSaaS

echo "Iniciando testes de smoke para JurisSaaS..."
echo "----------------------------------------"

# Verificar se o backend está acessível
echo "Teste 1: Verificando se o backend está acessível..."
BACKEND_HEALTH=$(curl -s https://5000-ie32ebooudf1fs6t5ss30-c5d42775.manusvm.computer/api/health)
if [[ $BACKEND_HEALTH == *"ok"* ]]; then
  echo "✅ Backend está acessível e funcionando corretamente"
else
  echo "❌ Backend não está respondendo corretamente"
  echo "Resposta: $BACKEND_HEALTH"
fi
echo "----------------------------------------"

# Verificar se o frontend está acessível
echo "Teste 2: Verificando se o frontend está acessível..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://5173-ie32ebooudf1fs6t5ss30-c5d42775.manusvm.computer)
if [[ $FRONTEND_STATUS == "200" ]]; then
  echo "✅ Frontend está acessível (código HTTP 200)"
else
  echo "❌ Frontend não está respondendo corretamente (código HTTP $FRONTEND_STATUS)"
fi
echo "----------------------------------------"

# Testar registro de usuário
echo "Teste 3: Testando registro de usuário..."
REGISTER_RESPONSE=$(curl -s -X POST https://5000-ie32ebooudf1fs6t5ss30-c5d42775.manusvm.computer/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nome":"Usuário Teste","email":"teste@jurissaas.com","senha":"senha123"}')

if [[ $REGISTER_RESPONSE == *"sucesso"* ]] || [[ $REGISTER_RESPONSE == *"token"* ]]; then
  echo "✅ Registro de usuário funcionando corretamente"
else
  echo "❌ Falha no registro de usuário"
  echo "Resposta: $REGISTER_RESPONSE"
fi
echo "----------------------------------------"

# Testar login de usuário
echo "Teste 4: Testando login de usuário..."
LOGIN_RESPONSE=$(curl -s -X POST https://5000-ie32ebooudf1fs6t5ss30-c5d42775.manusvm.computer/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@jurissaas.com","senha":"senha123"}')

if [[ $LOGIN_RESPONSE == *"sucesso"* ]] || [[ $LOGIN_RESPONSE == *"token"* ]]; then
  echo "✅ Login de usuário funcionando corretamente"
  # Extrair token para testes subsequentes
  ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
  echo "Token obtido para testes subsequentes"
else
  echo "❌ Falha no login de usuário"
  echo "Resposta: $LOGIN_RESPONSE"
  ACCESS_TOKEN=""
fi
echo "----------------------------------------"

# Se temos um token, testar criação de template
if [[ ! -z "$ACCESS_TOKEN" ]]; then
  echo "Teste 5: Testando criação de template..."
  TEMPLATE_RESPONSE=$(curl -s -X POST https://5000-ie32ebooudf1fs6t5ss30-c5d42775.manusvm.computer/api/templates \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{"titulo":"Template de Teste","conteudo":"Este é um template de teste para validação do sistema.","categoria":"Geral","publico":true}')

  if [[ $TEMPLATE_RESPONSE == *"id"* ]]; then
    echo "✅ Criação de template funcionando corretamente"
    TEMPLATE_ID=$(echo $TEMPLATE_RESPONSE | grep -o '"id":[0-9]*' | sed 's/"id"://')
    echo "Template ID: $TEMPLATE_ID"
  else
    echo "❌ Falha na criação de template"
    echo "Resposta: $TEMPLATE_RESPONSE"
    TEMPLATE_ID=""
  fi
  echo "----------------------------------------"

  # Testar criação de documento
  echo "Teste 6: Testando criação de documento..."
  DOCUMENT_RESPONSE=$(curl -s -X POST https://5000-ie32ebooudf1fs6t5ss30-c5d42775.manusvm.computer/api/documents \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{"titulo":"Documento de Teste","conteudo":"Este é um documento de teste para validação do sistema.","status":"Rascunho"}')

  if [[ $DOCUMENT_RESPONSE == *"id"* ]]; then
    echo "✅ Criação de documento funcionando corretamente"
    DOCUMENT_ID=$(echo $DOCUMENT_RESPONSE | grep -o '"id":[0-9]*' | sed 's/"id"://')
    echo "Documento ID: $DOCUMENT_ID"
  else
    echo "❌ Falha na criação de documento"
    echo "Resposta: $DOCUMENT_RESPONSE"
    DOCUMENT_ID=""
  fi
  echo "----------------------------------------"

  # Testar geração de texto com IA
  echo "Teste 7: Testando geração de texto com IA..."
  AI_RESPONSE=$(curl -s -X POST https://5000-ie32ebooudf1fs6t5ss30-c5d42775.manusvm.computer/api/ai/generate \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{"prompt":"Gere uma introdução para uma petição inicial de divórcio consensual."}')

  if [[ $AI_RESPONSE == *"text"* ]]; then
    echo "✅ Geração de texto com IA funcionando corretamente"
  else
    echo "❌ Falha na geração de texto com IA"
    echo "Resposta: $AI_RESPONSE"
  fi
  echo "----------------------------------------"
else
  echo "⚠️ Pulando testes que requerem autenticação devido à falha no login"
fi

echo "Testes de smoke concluídos!"
echo "Resumo dos resultados acima."
