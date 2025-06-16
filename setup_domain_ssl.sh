#!/bin/bash

# Script de configuração de domínio e SSL para o Editor IA JurisSaaS
# Este script automatiza a configuração de domínio e certificados SSL

echo "Iniciando configuração de domínio e SSL para o Editor IA JurisSaaS..."

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script deve ser executado como root (sudo)."
  exit 1
fi

# Solicitar informações do domínio
read -p "Digite o domínio principal para a aplicação (ex: app.jurissaas.com.br): " MAIN_DOMAIN

# Verificar se o domínio já está configurado no Nginx
if [ -f "/etc/nginx/sites-available/$MAIN_DOMAIN" ]; then
  echo "Configuração para o domínio $MAIN_DOMAIN já existe."
  read -p "Deseja sobrescrever? (s/n): " OVERWRITE
  if [ "$OVERWRITE" != "s" ]; then
    echo "Operação cancelada."
    exit 0
  fi
fi

# Verificar se o diretório da aplicação existe
read -p "Digite o caminho para o diretório da aplicação [/var/www/jurissaas]: " APP_DIR
APP_DIR=${APP_DIR:-/var/www/jurissaas}

if [ ! -d "$APP_DIR" ]; then
  echo "Erro: Diretório da aplicação $APP_DIR não encontrado."
  echo "Execute primeiro o script setup_production.sh para configurar o ambiente."
  exit 1
fi

# Criar configuração do Nginx
echo "Criando configuração do Nginx para $MAIN_DOMAIN..."
cat > /etc/nginx/sites-available/$MAIN_DOMAIN << EOF
server {
    listen 80;
    server_name $MAIN_DOMAIN;

    # Redirecionar HTTP para HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $MAIN_DOMAIN;

    # Certificados SSL serão configurados pelo Certbot

    # Configurações SSL recomendadas
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # HSTS (opcional, remova se não for necessário)
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Frontend
    location / {
        root $APP_DIR/frontend/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Configurações adicionais de segurança
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
}
EOF

# Ativar configuração do Nginx
ln -sf /etc/nginx/sites-available/$MAIN_DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remover configuração padrão se existir

# Verificar configuração do Nginx
echo "Verificando configuração do Nginx..."
nginx -t

if [ $? -ne 0 ]; then
  echo "Erro na configuração do Nginx. Corrigindo..."
  rm -f /etc/nginx/sites-enabled/$MAIN_DOMAIN
  exit 1
fi

# Reiniciar Nginx
echo "Reiniciando Nginx..."
systemctl reload nginx

# Verificar se o Certbot está instalado
if ! command -v certbot &> /dev/null; then
  echo "Certbot não encontrado. Instalando..."
  apt update
  apt install -y certbot python3-certbot-nginx
fi

# Verificar DNS antes de obter certificado
echo "Verificando resolução DNS para $MAIN_DOMAIN..."
if ! host $MAIN_DOMAIN > /dev/null; then
  echo "AVISO: O domínio $MAIN_DOMAIN não parece estar apontando para este servidor."
  echo "Verifique se o registro DNS A está configurado corretamente antes de continuar."
  read -p "Deseja continuar mesmo assim? (s/n): " CONTINUE_DNS
  if [ "$CONTINUE_DNS" != "s" ]; then
    echo "Operação cancelada. Configure o DNS e execute este script novamente."
    exit 0
  fi
fi

# Obter certificado SSL com Certbot
echo "Obtendo certificado SSL com Certbot para $MAIN_DOMAIN..."
certbot --nginx -d $MAIN_DOMAIN

# Verificar se o certificado foi obtido com sucesso
if [ $? -ne 0 ]; then
  echo "Erro ao obter certificado SSL. Verifique os logs do Certbot."
  exit 1
fi

# Configurar renovação automática do certificado
echo "Configurando renovação automática do certificado..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | crontab -

echo "Configuração de domínio e SSL concluída com sucesso!"
echo ""
echo "Domínio configurado: $MAIN_DOMAIN"
echo "Diretório da aplicação: $APP_DIR"
echo ""
echo "Acesse https://$MAIN_DOMAIN para verificar se a aplicação está funcionando corretamente."
echo "Certifique-se de que o backend esteja em execução: systemctl status jurissaas-backend"
