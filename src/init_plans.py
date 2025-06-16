#!/usr/bin/env python3
"""
Script para inicializar os planos padrão da LegalAI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import create_app
from src.extensions import db
from src.models.subscription import Plan, PlanType, PlanFeatures, create_default_plans

def init_plans():
    """Inicializar planos padrão no banco de dados"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se já existem planos
            existing_plans = Plan.query.count()
            
            if existing_plans > 0:
                print(f"✅ Já existem {existing_plans} planos no banco de dados.")
                
                # Listar planos existentes
                plans = Plan.query.all()
                print("\n📋 Planos existentes:")
                for plan in plans:
                    print(f"  • {plan.name} - R$ {plan.price_monthly}/mês")
                
                return
            
            print("🚀 Criando planos padrão da LegalAI...")
            
            # Criar planos padrão
            plans = create_default_plans()
            
            print(f"✅ {len(plans)} planos criados com sucesso!")
            
            # Exibir resumo dos planos criados
            print("\n📋 Planos criados:")
            for plan in plans:
                print(f"\n🔹 {plan.name}")
                print(f"   💰 Preço: R$ {plan.price_monthly}/mês")
                print(f"   📄 Documentos: {plan.features.monthly_documents if plan.features.monthly_documents != -1 else 'Ilimitados'}")
                print(f"   🤖 IA: {plan.features.monthly_ai_requests if plan.features.monthly_ai_requests != -1 else 'Ilimitadas'} consultas")
                print(f"   💾 Armazenamento: {plan.features.storage_gb}GB")
                print(f"   👥 Usuários: {plan.features.users_limit}")
                
                # Funcionalidades especiais
                special_features = []
                if plan.features.jurisprudence_analysis:
                    special_features.append("Análise de Jurisprudência")
                if plan.features.deadline_prediction:
                    special_features.append("Predição de Prazos")
                if plan.features.contract_analysis:
                    special_features.append("Análise de Contratos")
                if plan.features.executive_dashboard:
                    special_features.append("Dashboard Executivo")
                if plan.features.business_intelligence:
                    special_features.append("Business Intelligence")
                if plan.features.priority_support:
                    special_features.append("Suporte Prioritário")
                if plan.features.api_access:
                    special_features.append("Acesso à API")
                if plan.features.white_label:
                    special_features.append("White Label")
                
                if special_features:
                    print(f"   ⭐ Recursos especiais: {', '.join(special_features)}")
                
                if plan.is_popular:
                    print("   🔥 PLANO POPULAR")
            
            print("\n🎉 Inicialização dos planos concluída com sucesso!")
            print("\n💡 Próximos passos:")
            print("   1. Inicie o servidor: python src/main.py")
            print("   2. Acesse /api/subscriptions/plans para ver os planos")
            print("   3. Teste a criação de assinaturas via API")
            
        except Exception as e:
            print(f"❌ Erro ao criar planos: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    init_plans() 