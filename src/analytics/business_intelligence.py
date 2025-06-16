"""
Business Intelligence - Análises Avançadas para Escritórios Jurídicos
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class BusinessIntelligence:
    """Sistema de Business Intelligence jurídico"""
    
    def __init__(self):
        self.data = self._generate_sample_data()
    
    def _generate_sample_data(self) -> Dict:
        """Gerar dados de exemplo"""
        return {
            'client_segments': {
                'Pessoa Física': {'count': 145, 'revenue': 380000, 'satisfaction': 4.2},
                'Pequena Empresa': {'count': 78, 'revenue': 520000, 'satisfaction': 4.0},
                'Média Empresa': {'count': 32, 'revenue': 680000, 'satisfaction': 4.3},
                'Grande Empresa': {'count': 12, 'revenue': 1200000, 'satisfaction': 4.5}
            },
            'practice_areas': {
                'Direito Civil': {'cases': 45, 'revenue': 285000, 'success_rate': 89, 'avg_duration': 156},
                'Direito Trabalhista': {'cases': 32, 'revenue': 198000, 'success_rate': 92, 'avg_duration': 134},
                'Direito Tributário': {'cases': 28, 'revenue': 420000, 'success_rate': 85, 'avg_duration': 178},
                'Direito Criminal': {'cases': 18, 'revenue': 135000, 'success_rate': 83, 'avg_duration': 201},
                'Direito Empresarial': {'cases': 24, 'revenue': 540000, 'success_rate': 88, 'avg_duration': 143}
            }
        }
    
    def analyze_client_segments(self) -> Dict:
        """Análise de segmentos de clientes"""
        segments = self.data['client_segments']
        
        analysis = []
        total_revenue = sum(seg['revenue'] for seg in segments.values())
        total_clients = sum(seg['count'] for seg in segments.values())
        
        for segment, data in segments.items():
            revenue_share = (data['revenue'] / total_revenue) * 100
            client_share = (data['count'] / total_clients) * 100
            avg_ticket = data['revenue'] / data['count']
            
            analysis.append({
                'segment': segment,
                'client_count': data['count'],
                'revenue': data['revenue'],
                'revenue_share': revenue_share,
                'client_share': client_share,
                'avg_ticket': avg_ticket,
                'satisfaction': data['satisfaction'],
                'value_per_client': avg_ticket,
                'priority': 'alta' if revenue_share > 25 else 'média' if revenue_share > 15 else 'baixa'
            })
        
        # Ordenar por receita
        analysis.sort(key=lambda x: x['revenue'], reverse=True)
        
        insights = [
            f"Segmento '{analysis[0]['segment']}' gera {analysis[0]['revenue_share']:.1f}% da receita",
            f"Ticket médio mais alto: {analysis[0]['segment']} (R$ {analysis[0]['avg_ticket']:,.0f})",
            f"Satisfação média geral: {sum(seg['satisfaction'] for seg in segments.values()) / len(segments):.1f}/5.0"
        ]
        
        return {
            'segment_analysis': analysis,
            'insights': insights,
            'recommendations': [
                'Focar em retenção dos clientes de alto valor',
                'Desenvolver estratégias específicas por segmento',
                'Aumentar ticket médio dos segmentos de menor valor'
            ]
        }
    
    def analyze_practice_areas(self) -> Dict:
        """Análise de áreas de prática"""
        areas = self.data['practice_areas']
        
        analysis = []
        total_revenue = sum(area['revenue'] for area in areas.values())
        total_cases = sum(area['cases'] for area in areas.values())
        
        for area_name, data in areas.items():
            revenue_share = (data['revenue'] / total_revenue) * 100
            case_share = (data['cases'] / total_cases) * 100
            revenue_per_case = data['revenue'] / data['cases']
            
            analysis.append({
                'area': area_name,
                'cases': data['cases'],
                'revenue': data['revenue'],
                'revenue_share': revenue_share,
                'case_share': case_share,
                'revenue_per_case': revenue_per_case,
                'success_rate': data['success_rate'],
                'avg_duration': data['avg_duration'],
                'efficiency_score': (data['success_rate'] / 100) * (200 / data['avg_duration']),
                'profitability': 'alta' if revenue_per_case > 15000 else 'média' if revenue_per_case > 8000 else 'baixa'
            })
        
        # Ordenar por receita por caso
        analysis.sort(key=lambda x: x['revenue_per_case'], reverse=True)
        
        insights = [
            f"Área mais lucrativa: {analysis[0]['area']} (R$ {analysis[0]['revenue_per_case']:,.0f}/caso)",
            f"Taxa de sucesso média: {sum(area['success_rate'] for area in areas.values()) / len(areas):.1f}%",
            f"Duração média geral: {sum(area['avg_duration'] for area in areas.values()) / len(areas):.0f} dias"
        ]
        
        return {
            'area_analysis': analysis,
            'insights': insights,
            'recommendations': [
                'Expandir equipe nas áreas mais lucrativas',
                'Otimizar processos nas áreas de maior duração',
                'Especializar-se em nichos de alto valor'
            ]
        }
    
    def generate_market_analysis(self) -> Dict:
        """Análise de mercado e posicionamento"""
        
        market_data = {
            'market_size': 2500000000,  # R$ 2.5 bi
            'growth_rate': 8.5,  # %
            'our_market_share': 0.12,  # %
            'competitors': [
                {'name': 'Concorrente A', 'market_share': 2.1, 'specialization': 'Empresarial'},
                {'name': 'Concorrente B', 'market_share': 1.8, 'specialization': 'Tributário'},
                {'name': 'Concorrente C', 'market_share': 1.5, 'specialization': 'Civil'},
            ],
            'opportunities': [
                {'segment': 'Direito Digital', 'growth_potential': 'Alto', 'competition': 'Baixa'},
                {'segment': 'ESG Jurídico', 'growth_potential': 'Alto', 'competition': 'Média'},
                {'segment': 'Startups', 'growth_potential': 'Médio', 'competition': 'Alta'},
            ]
        }
        
        our_revenue = sum(area['revenue'] for area in self.data['practice_areas'].values())
        estimated_market_value = our_revenue / (market_data['our_market_share'] / 100)
        
        analysis = {
            'market_overview': {
                'total_market_size': market_data['market_size'],
                'growth_rate': market_data['growth_rate'],
                'our_revenue': our_revenue,
                'our_market_share': market_data['our_market_share'],
                'estimated_addressable_market': estimated_market_value
            },
            'competitive_landscape': market_data['competitors'],
            'market_opportunities': market_data['opportunities'],
            'swot_analysis': {
                'strengths': [
                    'Diversificação em múltiplas áreas',
                    'Alta taxa de sucesso (87.4%)',
                    'Boa satisfação do cliente (4.2/5.0)'
                ],
                'weaknesses': [
                    'Market share ainda baixo',
                    'Dependência de poucos clientes grandes',
                    'Processos podem ser otimizados'
                ],
                'opportunities': [
                    'Mercado em crescimento (8.5% a.a.)',
                    'Digitalização do setor jurídico',
                    'Novos nichos como ESG e Direito Digital'
                ],
                'threats': [
                    'Concorrência estabelecida',
                    'Mudanças regulatórias',
                    'Automação de serviços básicos'
                ]
            }
        }
        
        return analysis
    
    def calculate_kpi_trends(self) -> Dict:
        """Calcular tendências dos KPIs"""
        
        # Dados simulados de tendências dos últimos 6 meses
        months = ['Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        trends = {
            'revenue_trend': [95000, 108000, 115000, 122000, 118000, 125000],
            'cases_trend': [38, 42, 44, 46, 43, 47],
            'satisfaction_trend': [4.1, 4.2, 4.0, 4.3, 4.2, 4.4],
            'success_rate_trend': [85, 87, 86, 89, 88, 89],
            'client_retention_trend': [88, 89, 87, 91, 90, 92]
        }
        
        analysis = {}
        for metric, values in trends.items():
            if len(values) >= 2:
                # Calcular tendência linear
                x = np.arange(len(values))
                coeffs = np.polyfit(x, values, 1)
                slope = coeffs[0]
                
                # Determinar direção da tendência
                if slope > 0.05:
                    direction = "crescente"
                elif slope < -0.05:
                    direction = "decrescente" 
                else:
                    direction = "estável"
                
                # Calcular variação percentual
                change = ((values[-1] - values[0]) / values[0]) * 100
                
                analysis[metric] = {
                    'values': values,
                    'current_value': values[-1],
                    'previous_value': values[-2],
                    'trend_direction': direction,
                    'slope': slope,
                    'change_percentage': change,
                    'volatility': np.std(values) / np.mean(values)
                }
        
        return {
            'trend_analysis': analysis,
            'summary': {
                'improving_metrics': [k for k, v in analysis.items() if v['trend_direction'] == 'crescente'],
                'declining_metrics': [k for k, v in analysis.items() if v['trend_direction'] == 'decrescente'],
                'stable_metrics': [k for k, v in analysis.items() if v['trend_direction'] == 'estável']
            }
        }
    
    def generate_strategic_insights(self) -> Dict:
        """Gerar insights estratégicos"""
        
        client_analysis = self.analyze_client_segments()
        area_analysis = self.analyze_practice_areas()
        market_analysis = self.generate_market_analysis()
        kpi_trends = self.calculate_kpi_trends()
        
        # Identificar oportunidades baseadas em dados
        opportunities = []
        
        # Oportunidade 1: Área mais lucrativa
        most_profitable_area = max(area_analysis['area_analysis'], key=lambda x: x['revenue_per_case'])
        opportunities.append({
            'type': 'Expansão de Área',
            'description': f"Expandir atuação em {most_profitable_area['area']}",
            'potential_impact': 'Alto',
            'investment_required': 'Médio',
            'timeframe': '6-12 meses',
            'rationale': f"Área com maior receita por caso (R$ {most_profitable_area['revenue_per_case']:,.0f})"
        })
        
        # Oportunidade 2: Segmento de maior valor
        highest_value_segment = max(client_analysis['segment_analysis'], key=lambda x: x['avg_ticket'])
        opportunities.append({
            'type': 'Foco em Segmento',
            'description': f"Intensificar aquisição no segmento {highest_value_segment['segment']}",
            'potential_impact': 'Alto',
            'investment_required': 'Baixo',
            'timeframe': '3-6 meses',
            'rationale': f"Maior ticket médio (R$ {highest_value_segment['avg_ticket']:,.0f})"
        })
        
        # Oportunidade 3: Otimização de processos
        slowest_area = max(area_analysis['area_analysis'], key=lambda x: x['avg_duration'])
        opportunities.append({
            'type': 'Otimização de Processos',
            'description': f"Reduzir tempo de resolução em {slowest_area['area']}",
            'potential_impact': 'Médio',
            'investment_required': 'Baixo',
            'timeframe': '2-4 meses',
            'rationale': f"Área com maior duração média ({slowest_area['avg_duration']} dias)"
        })
        
        # Riscos identificados
        risks = []
        
        # Concentração em poucos clientes
        if highest_value_segment['revenue_share'] > 40:
            risks.append({
                'type': 'Concentração de Receita',
                'description': 'Alta dependência do segmento de maior valor',
                'probability': 'Média',
                'impact': 'Alto',
                'mitigation': 'Diversificar base de clientes'
            })
        
        # Áreas pouco lucrativas
        low_profit_areas = [area for area in area_analysis['area_analysis'] if area['profitability'] == 'baixa']
        if low_profit_areas:
            risks.append({
                'type': 'Baixa Lucratividade',
                'description': f"Áreas com baixa margem: {', '.join([area['area'] for area in low_profit_areas])}",
                'probability': 'Alta',
                'impact': 'Médio',
                'mitigation': 'Reavaliar precificação ou focar em áreas mais lucrativas'
            })
        
        return {
            'strategic_opportunities': opportunities,
            'identified_risks': risks,
            'key_performance_drivers': [
                {'driver': 'Especialização', 'impact': 'Alto', 'description': 'Focar em áreas de maior lucratividade'},
                {'driver': 'Eficiência Operacional', 'impact': 'Médio', 'description': 'Reduzir tempo de resolução'},
                {'driver': 'Qualidade de Atendimento', 'impact': 'Alto', 'description': 'Manter alta satisfação do cliente'}
            ],
            'recommendations': [
                'Investir em especialização nas áreas mais lucrativas',
                'Implementar automação para reduzir tempos de processo',
                'Desenvolver programa de retenção para clientes de alto valor',
                'Expandir marketing digital para novos segmentos',
                'Criar métricas de acompanhamento em tempo real'
            ]
        }
    
    def export_bi_report(self) -> Dict:
        """Exportar relatório completo de BI"""
        
        try:
            report = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'report_type': 'business_intelligence',
                    'version': '1.0'
                },
                'executive_summary': {
                    'total_revenue': sum(area['revenue'] for area in self.data['practice_areas'].values()),
                    'total_cases': sum(area['cases'] for area in self.data['practice_areas'].values()),
                    'total_clients': sum(seg['count'] for seg in self.data['client_segments'].values()),
                    'avg_success_rate': sum(area['success_rate'] for area in self.data['practice_areas'].values()) / len(self.data['practice_areas']),
                    'market_position': 'Crescimento sustentável com oportunidades de expansão'
                },
                'client_analysis': self.analyze_client_segments(),
                'practice_area_analysis': self.analyze_practice_areas(),
                'market_analysis': self.generate_market_analysis(),
                'kpi_trends': self.calculate_kpi_trends(),
                'strategic_insights': self.generate_strategic_insights()
            }
            
            return {
                'success': True,
                'report': report,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório BI: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao gerar relatório de Business Intelligence'
            }

# Funções para API
def get_client_segment_analysis() -> Dict:
    """Obter análise de segmentos de clientes"""
    try:
        bi = BusinessIntelligence()
        return {'success': True, **bi.analyze_client_segments()}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_practice_area_analysis() -> Dict:
    """Obter análise de áreas de prática"""
    try:
        bi = BusinessIntelligence()
        return {'success': True, **bi.analyze_practice_areas()}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_full_bi_report() -> Dict:
    """Obter relatório completo de BI"""
    try:
        bi = BusinessIntelligence()
        return bi.export_bi_report()
    except Exception as e:
        return {'success': False, 'error': str(e)}
