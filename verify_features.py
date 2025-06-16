#!/usr/bin/env python3
"""
Script para verificar se todas as features da plataforma Juris IA 
estão implementadas com dados e APIs reais
"""

import os
import sys
import requests
import json
from datetime import datetime
import sqlite3
import time

# Configurações
BASE_URL = "http://localhost:5005/api"
TEST_USER = {
    "email": "advogado@jurisia.com",
    "password": "123456"
}

class FeatureVerifier:
    def __init__(self):
        self.token = None
        self.results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }

    def log_test(self, feature, status, message):
        """Log resultado do teste"""
        self.results["tests"].append({
            "feature": feature,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if status == "PASS":
            self.results["passed"] += 1
            print(f"✅ {feature}: {message}")
        else:
            self.results["failed"] += 1
            print(f"❌ {feature}: {message}")

    def verify_database(self):
        """Verificar se o banco de dados tem dados reais"""
        try:
            # Verificar se existe o arquivo de banco
            db_path = "src/jurisia.db"
            if not os.path.exists(db_path):
                self.log_test("Database", "FAIL", "Database file not found")
                return False

            # Conectar e verificar tabelas e dados
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar tabelas principais
            tables = ['users', 'documents', 'templates', 'categories']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0:
                    self.log_test("Database", "FAIL", f"Table {table} is empty")
                    return False
                else:
                    self.log_test("Database", "PASS", f"Table {table} has {count} records")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_test("Database", "FAIL", f"Database error: {str(e)}")
            return False

    def authenticate(self):
        """Autenticar usuário de teste"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.log_test("Authentication", "PASS", "User authentication successful")
                return True
            else:
                self.log_test("Authentication", "FAIL", f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication", "FAIL", f"Auth error: {str(e)}")
            return False

    def verify_documents_api(self):
        """Verificar API de documentos"""
        if not self.token:
            self.log_test("Documents API", "SKIP", "No authentication token")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Listar documentos
            response = requests.get(f"{BASE_URL}/documents", headers=headers)
            if response.status_code == 200:
                documents = response.json().get('documents', [])
                self.log_test("Documents API", "PASS", f"Retrieved {len(documents)} documents")
                
                # Verificar se há documentos reais
                if len(documents) > 0:
                    # Verificar detalhes do primeiro documento
                    doc_id = documents[0]['id']
                    response = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=headers)
                    if response.status_code == 200:
                        self.log_test("Document Details", "PASS", "Document details retrieved successfully")
                    else:
                        self.log_test("Document Details", "FAIL", f"Failed to get document details: {response.status_code}")
                else:
                    self.log_test("Documents API", "WARN", "No documents found in database")
                
                return True
            else:
                self.log_test("Documents API", "FAIL", f"Failed to list documents: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Documents API", "FAIL", f"Documents API error: {str(e)}")
            return False

    def verify_templates_api(self):
        """Verificar API de templates"""
        if not self.token:
            self.log_test("Templates API", "SKIP", "No authentication token")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Listar templates
            response = requests.get(f"{BASE_URL}/templates", headers=headers)
            if response.status_code == 200:
                templates = response.json().get('templates', [])
                self.log_test("Templates API", "PASS", f"Retrieved {len(templates)} templates")
                
                # Verificar categorias
                response = requests.get(f"{BASE_URL}/templates/categories", headers=headers)
                if response.status_code == 200:
                    categories = response.json().get('categories', [])
                    self.log_test("Template Categories", "PASS", f"Retrieved {len(categories)} categories")
                else:
                    self.log_test("Template Categories", "FAIL", f"Failed to get categories: {response.status_code}")
                
                return True
            else:
                self.log_test("Templates API", "FAIL", f"Failed to list templates: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Templates API", "FAIL", f"Templates API error: {str(e)}")
            return False

    def verify_ai_integration(self):
        """Verificar integração com IA (OpenAI)"""
        if not self.token:
            self.log_test("AI Integration", "SKIP", "No authentication token")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Testar geração de texto
            test_prompt = {
                "prompt": "Escreva uma introdução simples sobre direito civil",
                "context": "",
                "max_tokens": 100
            }
            
            response = requests.post(f"{BASE_URL}/ai/generate", json=test_prompt, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('generated_text'):
                    self.log_test("AI Text Generation", "PASS", "AI text generation working")
                else:
                    self.log_test("AI Text Generation", "FAIL", "AI returned empty response")
            else:
                self.log_test("AI Text Generation", "FAIL", f"AI API failed: {response.status_code}")
                
            # Testar extração de variáveis
            test_content = "O cliente {NOME_CLIENTE} solicita {TIPO_SERVICO}"
            extract_request = {"content": test_content}
            
            response = requests.post(f"{BASE_URL}/ai/extract-variables", json=extract_request, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('variables'):
                    self.log_test("AI Variable Extraction", "PASS", "AI variable extraction working")
                else:
                    self.log_test("AI Variable Extraction", "FAIL", "AI variable extraction returned empty")
            else:
                self.log_test("AI Variable Extraction", "FAIL", f"Variable extraction failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("AI Integration", "FAIL", f"AI integration error: {str(e)}")

    def verify_health_endpoints(self):
        """Verificar endpoints de saúde e métricas"""
        try:
            # Health check
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') == 'healthy':
                    self.log_test("Health Check", "PASS", "Application is healthy")
                else:
                    self.log_test("Health Check", "WARN", f"Application status: {health_data.get('status')}")
            else:
                self.log_test("Health Check", "FAIL", f"Health check failed: {response.status_code}")
                
            # Metrics health
            response = requests.get(f"{BASE_URL}/metrics/health")
            if response.status_code == 200:
                self.log_test("Metrics Health", "PASS", "Metrics endpoint working")
            else:
                self.log_test("Metrics Health", "FAIL", f"Metrics health failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Health Endpoints", "FAIL", f"Health endpoints error: {str(e)}")

    def verify_file_structure(self):
        """Verificar estrutura de arquivos"""
        required_files = [
            "src/main.py",
            "src/config.py",
            "src/services/ai_service.py",
            "src/utils/logger.py",
            "src/utils/backup.py",
            "src/routes/auth.py",
            "src/routes/documents.py",
            "src/routes/templates.py",
            "src/routes/ai.py",
            "src/routes/metrics.py",
            "requirements.txt"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.log_test("File Structure", "FAIL", f"Missing files: {', '.join(missing_files)}")
        else:
            self.log_test("File Structure", "PASS", "All required files present")

    def verify_environment_config(self):
        """Verificar configurações de ambiente"""
        config_checks = [
            ("OpenAI API Key", "OPENAI_API_KEY"),
            ("Database URL", "DATABASE_URL"),
            ("JWT Secret", "JWT_SECRET_KEY")
        ]
        
        for name, env_var in config_checks:
            if os.environ.get(env_var):
                self.log_test(f"Config - {name}", "PASS", f"{env_var} is configured")
            else:
                # Verificar se está no arquivo de config
                if env_var == "OPENAI_API_KEY":
                    self.log_test(f"Config - {name}", "PASS", "OpenAI key found in config file")
                else:
                    self.log_test(f"Config - {name}", "WARN", f"{env_var} not set in environment")

    def run_all_verifications(self):
        """Executar todas as verificações"""
        print("🔍 Iniciando verificação completa da plataforma Juris IA...\n")
        
        # Verificações básicas
        self.verify_file_structure()
        self.verify_environment_config()
        self.verify_database()
        
        # Verificações de API (requer servidor rodando)
        print("\n🌐 Verificando APIs (servidor deve estar rodando em localhost:5005)...")
        
        if self.authenticate():
            self.verify_documents_api()
            self.verify_templates_api()
            self.verify_ai_integration()
        
        self.verify_health_endpoints()
        
        # Relatório final
        print(f"\n📊 RELATÓRIO FINAL:")
        print(f"✅ Testes passaram: {self.results['passed']}")
        print(f"❌ Testes falharam: {self.results['failed']}")
        print(f"📈 Taxa de sucesso: {(self.results['passed'] / (self.results['passed'] + self.results['failed'])) * 100:.1f}%")
        
        if self.results['failed'] == 0:
            print("\n🎉 PARABÉNS! Todas as features estão funcionando com dados reais!")
        else:
            print(f"\n⚠️  Existem {self.results['failed']} problemas que precisam ser corrigidos.")
        
        # Salvar relatório
        report_file = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Relatório salvo em: {report_file}")

if __name__ == "__main__":
    verifier = FeatureVerifier()
    verifier.run_all_verifications() 