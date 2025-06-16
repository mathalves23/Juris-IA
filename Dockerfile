FROM python:3.10-slim

# Configurar timezone
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash jurisia

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs backups uploads && \
    chown -R jurisia:jurisia /app

# Mudar para usuário não-root
USER jurisia

# Expor porta
EXPOSE 5005

# Configurar variáveis de ambiente
ENV FLASK_APP=src/main.py
ENV PYTHONPATH=/app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5005/api/health || exit 1

# Comando padrão
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "src.main:create_app()"] 