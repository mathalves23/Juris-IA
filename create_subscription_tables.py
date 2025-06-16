#!/usr/bin/env python3
"""
Script para criar tabelas de subscription no banco existente
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_subscription_tables():
    """Criar tabelas de subscription e planos"""
    
    # Conectar ao banco
    db_path = os.path.join(os.path.dirname(__file__), 'src', 'legalai.db')
    print(f"Conectando ao banco: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Banco não encontrado: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Criar tabela de planos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                plan_type VARCHAR(50) NOT NULL,
                description TEXT,
                price_monthly REAL NOT NULL,
                price_annual REAL,
                is_popular BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                features_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Criar tabela de assinaturas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                is_annual BOOLEAN DEFAULT 0,
                start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_date DATETIME,
                trial_end_date DATETIME,
                amount_paid REAL,
                payment_method VARCHAR(50),
                stripe_subscription_id VARCHAR(255),
                monthly_documents_used INTEGER DEFAULT 0,
                monthly_templates_used INTEGER DEFAULT 0,
                monthly_ai_requests_used INTEGER DEFAULT 0,
                last_usage_reset DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (plan_id) REFERENCES plans (id)
            )
        ''')
        
        print("✅ Tabelas de subscription criadas com sucesso!")
        
        # Verificar se já existem planos
        cursor.execute("SELECT COUNT(*) FROM plans")
        plan_count = cursor.fetchone()[0]
        
        if plan_count == 0:
            print("📋 Criando planos padrão...")
            
            # Planos com features em JSON
            plans_data = [
                {
                    'name': 'Básico Mensal',
                    'plan_type': 'basico_mensal',
                    'description': 'Plano ideal para advogados iniciantes',
                    'price_monthly': 49.90,
                    'price_annual': 49.90 * 10,  # 2 meses gratuitos
                    'is_popular': False,
                    'features': {
                        'monthly_documents': 50,
                        'monthly_templates': 10,
                        'monthly_ai_requests': 100,
                        'storage_gb': 5,
                        'users_limit': 1,
                        'document_creation': True,
                        'template_library': True,
                        'basic_ai': True,
                        'jurisprudence_analysis': False,
                        'deadline_prediction': False,
                        'advanced_ai': False,
                        'contract_analysis': False,
                        'executive_dashboard': False,
                        'predictive_reports': False,
                        'business_intelligence': False,
                        'performance_metrics': False,
                        'microservices_access': False,
                        'priority_support': False,
                        'api_access': False,
                        'white_label': False,
                        'custom_integrations': False
                    }
                },
                {
                    'name': 'Intermediário Mensal',
                    'plan_type': 'intermediario_mensal',
                    'description': 'Perfeito para escritórios em crescimento',
                    'price_monthly': 99.90,
                    'price_annual': 99.90 * 10,
                    'is_popular': True,
                    'features': {
                        'monthly_documents': 200,
                        'monthly_templates': 50,
                        'monthly_ai_requests': 500,
                        'storage_gb': 20,
                        'users_limit': 3,
                        'document_creation': True,
                        'template_library': True,
                        'basic_ai': True,
                        'jurisprudence_analysis': True,
                        'deadline_prediction': True,
                        'advanced_ai': True,
                        'contract_analysis': False,
                        'executive_dashboard': False,
                        'predictive_reports': False,
                        'business_intelligence': False,
                        'performance_metrics': False,
                        'microservices_access': False,
                        'priority_support': False,
                        'api_access': False,
                        'white_label': False,
                        'custom_integrations': False
                    }
                },
                {
                    'name': 'Profissional Mensal',
                    'plan_type': 'profissional_mensal',
                    'description': 'Para escritórios estabelecidos que precisam de recursos avançados',
                    'price_monthly': 199.90,
                    'price_annual': 199.90 * 10,
                    'is_popular': False,
                    'features': {
                        'monthly_documents': 1000,
                        'monthly_templates': 200,
                        'monthly_ai_requests': 2000,
                        'storage_gb': 100,
                        'users_limit': 10,
                        'document_creation': True,
                        'template_library': True,
                        'basic_ai': True,
                        'jurisprudence_analysis': True,
                        'deadline_prediction': True,
                        'advanced_ai': True,
                        'contract_analysis': True,
                        'executive_dashboard': True,
                        'predictive_reports': True,
                        'business_intelligence': False,
                        'performance_metrics': False,
                        'microservices_access': False,
                        'priority_support': True,
                        'api_access': True,
                        'white_label': False,
                        'custom_integrations': False
                    }
                },
                {
                    'name': 'Empresarial Mensal',
                    'plan_type': 'empresarial_mensal',
                    'description': 'Solução completa para grandes escritórios e empresas',
                    'price_monthly': 399.90,
                    'price_annual': 399.90 * 10,
                    'is_popular': False,
                    'features': {
                        'monthly_documents': -1,  # Ilimitado
                        'monthly_templates': -1,
                        'monthly_ai_requests': -1,
                        'storage_gb': 500,
                        'users_limit': 50,
                        'document_creation': True,
                        'template_library': True,
                        'basic_ai': True,
                        'jurisprudence_analysis': True,
                        'deadline_prediction': True,
                        'advanced_ai': True,
                        'contract_analysis': True,
                        'executive_dashboard': True,
                        'predictive_reports': True,
                        'business_intelligence': True,
                        'performance_metrics': True,
                        'microservices_access': True,
                        'priority_support': True,
                        'api_access': True,
                        'white_label': True,
                        'custom_integrations': True
                    }
                }
            ]
            
            for plan_data in plans_data:
                features_json = str(plan_data['features']).replace("'", '"').replace('True', 'true').replace('False', 'false')
                cursor.execute('''
                    INSERT INTO plans (name, plan_type, description, price_monthly, price_annual, is_popular, features_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    plan_data['name'],
                    plan_data['plan_type'],
                    plan_data['description'],
                    plan_data['price_monthly'],
                    plan_data['price_annual'],
                    plan_data['is_popular'],
                    features_json
                ))
                print(f"   📄 {plan_data['name']} - R$ {plan_data['price_monthly']}/mês")
        else:
            print(f"ℹ️ {plan_count} planos já existem no banco")
        
        # Criar assinatura trial para usuário admin
        cursor.execute("SELECT id FROM users WHERE email LIKE '%admin%' OR email LIKE '%advogado%' LIMIT 1")
        admin_user = cursor.fetchone()
        
        if admin_user:
            user_id = admin_user[0]
            
            # Verificar se já tem assinatura
            cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE user_id = ?", (user_id,))
            sub_count = cursor.fetchone()[0]
            
            if sub_count == 0:
                # Criar assinatura trial no plano Intermediário (mais popular)
                cursor.execute("SELECT id FROM plans WHERE is_popular = 1 LIMIT 1")
                popular_plan = cursor.fetchone()
                
                if popular_plan:
                    plan_id = popular_plan[0]
                    start_date = datetime.now()
                    trial_end = start_date + timedelta(days=7)
                    end_date = start_date + timedelta(days=30)
                    
                    cursor.execute('''
                        INSERT INTO subscriptions (user_id, plan_id, status, start_date, end_date, trial_end_date)
                        VALUES (?, ?, 'trial', ?, ?, ?)
                    ''', (user_id, plan_id, start_date, end_date, trial_end))
                    
                    print(f"🎁 Assinatura trial criada para usuário ID {user_id}")
            else:
                print("ℹ️ Usuário já possui assinatura")
        
        conn.commit()
        print("✅ Configuração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Criando tabelas de subscription...")
    success = create_subscription_tables()
    
    if success:
        print("\n🎉 Pronto! Execute agora:")
        print("   python src/main.py")
        print("   Em seguida teste: python test_legalai_system.py")
    else:
        print("\n❌ Falha na criação das tabelas") 