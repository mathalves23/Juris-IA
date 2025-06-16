"""
Dashboard Executivo - Sistema de KPIs e Métricas Jurídicas
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)

class PeriodType(Enum):
    """Tipos de período para análise"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class KPICategory(Enum):
    """Categorias de KPIs"""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CLIENT = "client"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"

@dataclass
class KPIMetric:
    """Métrica KPI"""
    name: str
    value: float
    previous_value: float
    change_percentage: float
    category: KPICategory
    unit: str
    is_positive_change_good: bool = True
    target_value: Optional[float] = None
    description: str = ""

@dataclass
class DashboardWidget:
    """Widget do dashboard"""
    id: str
    title: str
    type: str  # chart, metric, table, gauge
    data: Any
    config: Dict[str, Any]
    position: Dict[str, int]  # row, col, width, height

class ExecutiveDashboard:
    """Dashboard executivo com KPIs jurídicos"""
    
    def __init__(self):
        # Dados simulados
        self.mock_data = self._generate_mock_data()
        
        # Configurações de KPIs
        self.kpi_definitions = {
            # KPIs Financeiros
            'receita_mensal': {
                'name': 'Receita Mensal',
                'category': KPICategory.FINANCIAL,
                'unit': 'R$',
                'target': 100000,
                'is_positive_good': True
            },
            'ticket_medio': {
                'name': 'Ticket Médio',
                'category': KPICategory.FINANCIAL,
                'unit': 'R$',
                'target': 5000,
                'is_positive_good': True
            },
            'margem_lucro': {
                'name': 'Margem de Lucro',
                'category': KPICategory.FINANCIAL,
                'unit': '%',
                'target': 25,
                'is_positive_good': True
            },
            
            # KPIs Operacionais
            'casos_ativos': {
                'name': 'Casos Ativos',
                'category': KPICategory.OPERATIONAL,
                'unit': 'unidades',
                'target': 150,
                'is_positive_good': True
            },
            'casos_concluidos': {
                'name': 'Casos Concluídos',
                'category': KPICategory.OPERATIONAL,
                'unit': 'unidades',
                'target': 30,
                'is_positive_good': True
            },
            'tempo_medio_resolucao': {
                'name': 'Tempo Médio de Resolução',
                'category': KPICategory.EFFICIENCY,
                'unit': 'dias',
                'target': 45,
                'is_positive_good': False
            },
            
            # KPIs de Cliente
            'satisfacao_cliente': {
                'name': 'Satisfação do Cliente',
                'category': KPICategory.CLIENT,
                'unit': 'score',
                'target': 4.5,
                'is_positive_good': True
            },
            'taxa_retencao': {
                'name': 'Taxa de Retenção',
                'category': KPICategory.CLIENT,
                'unit': '%',
                'target': 90,
                'is_positive_good': True
            },
            'novos_clientes': {
                'name': 'Novos Clientes',
                'category': KPICategory.CLIENT,
                'unit': 'unidades',
                'target': 10,
                'is_positive_good': True
            },
            
            # KPIs de Qualidade
            'taxa_sucesso': {
                'name': 'Taxa de Sucesso',
                'category': KPICategory.QUALITY,
                'unit': '%',
                'target': 85,
                'is_positive_good': True
            },
            'documentos_gerados': {
                'name': 'Documentos Gerados',
                'category': KPICategory.OPERATIONAL,
                'unit': 'unidades',
                'target': 200,
                'is_positive_good': True
            }
        }
    
    def _generate_mock_data(self) -> Dict:
        """Gerar dados simulados"""
        return {
            'receita_mensal': 125000,
            'receita_anterior': 118000,
            'casos_ativos': 147,
            'casos_anteriores': 142,
            'satisfacao': 4.2,
            'satisfacao_anterior': 4.0,
            'novos_clientes': 15,
            'novos_clientes_anterior': 12
        }
    
    def calculate_kpis(self) -> List[KPIMetric]:
        """Calcular KPIs principais"""
        data = self.mock_data
        kpis = []
        
        # Receita
        change_receita = ((data['receita_mensal'] - data['receita_anterior']) / data['receita_anterior'] * 100)
        kpis.append(KPIMetric(
            name="Receita Mensal",
            value=data['receita_mensal'],
            previous_value=data['receita_anterior'],
            change_percentage=change_receita,
            category=KPICategory.FINANCIAL,
            unit="R$"
        ))
        
        # Casos Ativos
        change_casos = ((data['casos_ativos'] - data['casos_anteriores']) / data['casos_anteriores'] * 100)
        kpis.append(KPIMetric(
            name="Casos Ativos",
            value=data['casos_ativos'],
            previous_value=data['casos_anteriores'],
            change_percentage=change_casos,
            category=KPICategory.OPERATIONAL,
            unit="unidades"
        ))
        
        # Satisfação
        change_satisfacao = ((data['satisfacao'] - data['satisfacao_anterior']) / data['satisfacao_anterior'] * 100)
        kpis.append(KPIMetric(
            name="Satisfação Cliente",
            value=data['satisfacao'],
            previous_value=data['satisfacao_anterior'],
            change_percentage=change_satisfacao,
            category=KPICategory.CLIENT,
            unit="score"
        ))
        
        return kpis
    
    def generate_charts(self) -> Dict:
        """Gerar dados para gráficos"""
        return {
            'revenue_chart': {
                'type': 'line',
                'data': {
                    'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
                    'values': [95000, 108000, 115000, 122000, 118000, 125000]
                }
            },
            'cases_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': ['Em Andamento', 'Concluídos', 'Aguardando'],
                    'values': [87, 34, 26]
                }
            }
        }

def get_executive_dashboard() -> Dict:
    """Obter dados do dashboard executivo"""
    try:
        dashboard = ExecutiveDashboard()
        kpis = dashboard.calculate_kpis()
        charts = dashboard.generate_charts()
        
        return {
            'success': True,
            'kpis': [
                {
                    'name': kpi.name,
                    'value': kpi.value,
                    'change': kpi.change_percentage,
                    'category': kpi.category.value,
                    'unit': kpi.unit
                }
                for kpi in kpis
            ],
            'charts': charts,
            'generated_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_kpi_summary() -> Dict:
    """Obter resumo dos KPIs principais"""
    
    try:
        dashboard = ExecutiveDashboard()
        kpis = dashboard.calculate_kpis()
        
        summary = {
            'financial': [],
            'operational': [],
            'client': [],
            'quality': []
        }
        
        for kpi in kpis:
            category_key = kpi.category.value
            if category_key in summary:
                summary[category_key].append({
                    'name': kpi.name,
                    'value': kpi.value,
                    'change': kpi.change_percentage,
                    'unit': kpi.unit,
                    'status': 'positive' if kpi.change_percentage > 0 else 'negative'
                })
        
        return {
            'success': True,
            'kpi_summary': summary,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo KPI: {e}")
        return {
            'success': False,
            'error': str(e)
        } 