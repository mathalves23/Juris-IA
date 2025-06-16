"""
Sistema de Relatórios Preditivos
Machine learning para previsões jurídicas e de negócio
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PredictionType(Enum):
    """Tipos de predição"""
    REVENUE = "revenue"
    CASES = "cases"
    CLIENT_CHURN = "client_churn"
    CASE_DURATION = "case_duration"
    DEMAND = "demand"

class TimeHorizon(Enum):
    """Horizontes temporais para predição"""
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

@dataclass
class PredictionResult:
    """Resultado de uma predição"""
    prediction_type: PredictionType
    predicted_value: float
    confidence_interval: tuple
    accuracy_score: float
    trend: str  # "increasing", "decreasing", "stable"
    factors: List[str]
    generated_at: datetime

class PredictiveReports:
    """Sistema de relatórios preditivos"""
    
    def __init__(self):
        # Dados históricos simulados
        self.historical_data = self._generate_historical_data()
        
        # Configurações de modelos
        self.model_configs = {
            PredictionType.REVENUE: {
                'seasonal_factor': 0.1,
                'trend_factor': 0.05,
                'volatility': 0.15
            },
            PredictionType.CASES: {
                'seasonal_factor': 0.08,
                'trend_factor': 0.03,
                'volatility': 0.12
            }
        }
    
    def _generate_historical_data(self) -> pd.DataFrame:
        """Gerar dados históricos simulados"""
        
        # 24 meses de dados
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=730),
            end=datetime.now(),
            freq='D'
        )
        
        n_days = len(dates)
        
        # Receita diária com tendência e sazonalidade
        trend = np.linspace(3000, 4000, n_days)
        seasonal = 500 * np.sin(2 * np.pi * np.arange(n_days) / 365.25)
        noise = np.random.normal(0, 300, n_days)
        revenue = trend + seasonal + noise
        revenue = np.maximum(revenue, 1000)  # Mínimo R$ 1000
        
        # Casos novos
        cases_base = 2 + 0.5 * np.sin(2 * np.pi * np.arange(n_days) / 365.25)
        cases = np.random.poisson(cases_base)
        
        # Satisfação do cliente
        satisfaction = 4.0 + 0.5 * np.sin(2 * np.pi * np.arange(n_days) / 365.25) + np.random.normal(0, 0.2, n_days)
        satisfaction = np.clip(satisfaction, 1, 5)
        
        # Criar DataFrame
        df = pd.DataFrame({
            'date': dates,
            'revenue': revenue,
            'cases': cases,
            'satisfaction': satisfaction,
            'day_of_week': dates.dayofweek,
            'month': dates.month,
            'quarter': dates.quarter,
            'year': dates.year
        })
        
        return df
    
    def predict_revenue(self, horizon: TimeHorizon = TimeHorizon.MONTH) -> PredictionResult:
        """Predizer receita futura"""
        
        # Calcular períodos
        periods_map = {
            TimeHorizon.WEEK: 7,
            TimeHorizon.MONTH: 30,
            TimeHorizon.QUARTER: 90,
            TimeHorizon.YEAR: 365
        }
        
        days_ahead = periods_map[horizon]
        
        # Dados recentes para análise de tendência
        recent_data = self.historical_data.tail(90)
        
        # Calcular tendência
        recent_revenue = recent_data['revenue'].values
        x = np.arange(len(recent_revenue))
        coeffs = np.polyfit(x, recent_revenue, 1)
        daily_trend = coeffs[0]
        
        # Valor base (média dos últimos 30 dias)
        base_value = recent_data.tail(30)['revenue'].mean()
        
        # Predição simples com tendência
        predicted_daily = base_value + (daily_trend * days_ahead / 2)
        predicted_total = predicted_daily * days_ahead
        
        # Fator sazonal baseado no mês atual
        current_month = datetime.now().month
        seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * current_month / 12)
        predicted_total *= seasonal_factor
        
        # Intervalo de confiança (±15%)
        margin = predicted_total * 0.15
        confidence_interval = (
            predicted_total - margin,
            predicted_total + margin
        )
        
        # Determinar tendência
        if daily_trend > 50:
            trend = "increasing"
        elif daily_trend < -50:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Fatores influenciadores
        factors = [
            f"Tendência diária: {'positiva' if daily_trend > 0 else 'negativa'} (R$ {daily_trend:.0f}/dia)",
            f"Sazonalidade: {'+' if seasonal_factor > 1 else ''}{(seasonal_factor-1)*100:.1f}%",
            "Baseado em dados dos últimos 90 dias"
        ]
        
        return PredictionResult(
            prediction_type=PredictionType.REVENUE,
            predicted_value=predicted_total,
            confidence_interval=confidence_interval,
            accuracy_score=0.85,  # Score simulado
            trend=trend,
            factors=factors,
            generated_at=datetime.now()
        )
    
    def predict_case_volume(self, horizon: TimeHorizon = TimeHorizon.MONTH) -> PredictionResult:
        """Predizer volume de casos"""
        
        periods_map = {
            TimeHorizon.WEEK: 7,
            TimeHorizon.MONTH: 30,
            TimeHorizon.QUARTER: 90,
            TimeHorizon.YEAR: 365
        }
        
        days_ahead = periods_map[horizon]
        recent_data = self.historical_data.tail(60)
        
        # Média de casos por dia
        avg_daily_cases = recent_data['cases'].mean()
        
        # Tendência
        cases_values = recent_data['cases'].values
        x = np.arange(len(cases_values))
        coeffs = np.polyfit(x, cases_values, 1)
        daily_trend = coeffs[0]
        
        # Predição
        predicted_daily = avg_daily_cases + (daily_trend * days_ahead / 2)
        predicted_total = predicted_daily * days_ahead
        
        # Intervalo de confiança
        margin = predicted_total * 0.2
        confidence_interval = (
            max(0, predicted_total - margin),
            predicted_total + margin
        )
        
        # Tendência
        if daily_trend > 0.05:
            trend = "increasing"
        elif daily_trend < -0.05:
            trend = "decreasing"
        else:
            trend = "stable"
        
        factors = [
            f"Média atual: {avg_daily_cases:.1f} casos/dia",
            f"Tendência: {'+' if daily_trend > 0 else ''}{daily_trend:.3f} casos/dia",
            "Baseado em padrões dos últimos 60 dias"
        ]
        
        return PredictionResult(
            prediction_type=PredictionType.CASES,
            predicted_value=predicted_total,
            confidence_interval=confidence_interval,
            accuracy_score=0.78,
            trend=trend,
            factors=factors,
            generated_at=datetime.now()
        )
    
    def predict_client_satisfaction(self) -> PredictionResult:
        """Predizer satisfação do cliente"""
        
        recent_data = self.historical_data.tail(30)
        current_satisfaction = recent_data['satisfaction'].mean()
        
        # Tendência de satisfação
        satisfaction_values = recent_data['satisfaction'].values
        x = np.arange(len(satisfaction_values))
        coeffs = np.polyfit(x, satisfaction_values, 1)
        trend_slope = coeffs[0]
        
        # Predição para próximo mês
        predicted_satisfaction = current_satisfaction + (trend_slope * 30)
        predicted_satisfaction = np.clip(predicted_satisfaction, 1, 5)
        
        # Intervalo de confiança
        std_dev = recent_data['satisfaction'].std()
        margin = 1.96 * std_dev / np.sqrt(len(recent_data))
        confidence_interval = (
            max(1, predicted_satisfaction - margin),
            min(5, predicted_satisfaction + margin)
        )
        
        # Tendência
        if trend_slope > 0.01:
            trend = "increasing"
        elif trend_slope < -0.01:
            trend = "decreasing"
        else:
            trend = "stable"
        
        factors = [
            f"Satisfação atual: {current_satisfaction:.2f}/5.0",
            f"Tendência mensal: {'+' if trend_slope > 0 else ''}{trend_slope:.3f}",
            f"Volatilidade: {std_dev:.2f}"
        ]
        
        return PredictionResult(
            prediction_type=PredictionType.CLIENT_CHURN,
            predicted_value=predicted_satisfaction,
            confidence_interval=confidence_interval,
            accuracy_score=0.82,
            trend=trend,
            factors=factors,
            generated_at=datetime.now()
        )
    
    def generate_demand_forecast(self) -> Dict[str, Any]:
        """Gerar previsão de demanda por área jurídica"""
        
        # Dados simulados de demanda por área
        areas = [
            'Direito Civil',
            'Direito Trabalhista', 
            'Direito Tributário',
            'Direito Criminal',
            'Direito Empresarial'
        ]
        
        current_demand = [45, 32, 28, 18, 24]
        predicted_demand = [48, 35, 30, 16, 26]
        growth_rates = [
            (pred - curr) / curr * 100 
            for curr, pred in zip(current_demand, predicted_demand)
        ]
        
        forecast_data = []
        for area, current, predicted, growth in zip(areas, current_demand, predicted_demand, growth_rates):
            forecast_data.append({
                'area': area,
                'current_cases': current,
                'predicted_cases': predicted,
                'growth_rate': growth,
                'trend': 'crescente' if growth > 0 else 'decrescente' if growth < 0 else 'estável'
            })
        
        return {
            'forecast_data': forecast_data,
            'summary': {
                'total_current': sum(current_demand),
                'total_predicted': sum(predicted_demand),
                'overall_growth': sum(growth_rates) / len(growth_rates)
            },
            'recommendations': [
                'Aumentar equipe para Direito Civil e Trabalhista',
                'Considerar especialização em Direito Empresarial',
                'Monitorar redução em Direito Criminal'
            ]
        }
    
    def generate_risk_assessment(self) -> Dict[str, Any]:
        """Gerar avaliação de riscos"""
        
        # Análise de riscos baseada em dados históricos
        recent_data = self.historical_data.tail(30)
        
        # Volatilidade da receita
        revenue_volatility = recent_data['revenue'].std() / recent_data['revenue'].mean()
        
        # Tendência de satisfação
        satisfaction_trend = np.polyfit(range(len(recent_data)), recent_data['satisfaction'], 1)[0]
        
        # Carga de trabalho
        avg_cases = recent_data['cases'].mean()
        workload_risk = 'alto' if avg_cases > 3 else 'médio' if avg_cases > 2 else 'baixo'
        
        risks = [
            {
                'category': 'Financeiro',
                'risk': 'Volatilidade de Receita',
                'level': 'alto' if revenue_volatility > 0.2 else 'médio' if revenue_volatility > 0.1 else 'baixo',
                'value': f"{revenue_volatility:.1%}",
                'recommendation': 'Diversificar fontes de receita' if revenue_volatility > 0.2 else 'Monitorar tendências'
            },
            {
                'category': 'Cliente',
                'risk': 'Satisfação em Declínio',
                'level': 'alto' if satisfaction_trend < -0.01 else 'médio' if satisfaction_trend < 0 else 'baixo',
                'value': f"{satisfaction_trend:.3f}/mês",
                'recommendation': 'Melhorar qualidade do atendimento' if satisfaction_trend < 0 else 'Manter padrão'
            },
            {
                'category': 'Operacional',
                'risk': 'Sobrecarga de Trabalho',
                'level': workload_risk,
                'value': f"{avg_cases:.1f} casos/dia",
                'recommendation': 'Contratar mais advogados' if workload_risk == 'alto' else 'Otimizar processos'
            }
        ]
        
        return {
            'risks': risks,
            'overall_risk_score': 7.2,  # Score de 0-10
            'risk_trend': 'estável',
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_full_report(self) -> Dict[str, Any]:
        """Gerar relatório preditivo completo"""
        
        try:
            # Obter todas as predições
            revenue_pred = self.predict_revenue(TimeHorizon.MONTH)
            cases_pred = self.predict_case_volume(TimeHorizon.MONTH)
            satisfaction_pred = self.predict_client_satisfaction()
            demand_forecast = self.generate_demand_forecast()
            risk_assessment = self.generate_risk_assessment()
            
            return {
                'success': True,
                'report': {
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'period': 'monthly',
                        'report_type': 'predictive_analysis'
                    },
                    'predictions': {
                        'revenue': {
                            'predicted_value': revenue_pred.predicted_value,
                            'confidence_interval': revenue_pred.confidence_interval,
                            'trend': revenue_pred.trend,
                            'factors': revenue_pred.factors,
                            'accuracy': revenue_pred.accuracy_score
                        },
                        'cases': {
                            'predicted_value': cases_pred.predicted_value,
                            'confidence_interval': cases_pred.confidence_interval,
                            'trend': cases_pred.trend,
                            'factors': cases_pred.factors,
                            'accuracy': cases_pred.accuracy_score
                        },
                        'satisfaction': {
                            'predicted_value': satisfaction_pred.predicted_value,
                            'confidence_interval': satisfaction_pred.confidence_interval,
                            'trend': satisfaction_pred.trend,
                            'factors': satisfaction_pred.factors,
                            'accuracy': satisfaction_pred.accuracy_score
                        }
                    },
                    'demand_forecast': demand_forecast,
                    'risk_assessment': risk_assessment,
                    'summary': {
                        'overall_outlook': 'positivo',
                        'key_insights': [
                            'Receita com tendência de crescimento',
                            'Volume de casos estável',
                            'Satisfação do cliente mantendo-se alta'
                        ],
                        'action_items': [
                            'Investir em marketing para sustentabilidade',
                            'Otimizar processos internos',
                            'Monitorar satisfação continuamente'
                        ]
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório preditivo: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao gerar relatório preditivo'
            }

# Funções para API
def get_revenue_prediction(horizon: str = "month") -> Dict:
    """Obter predição de receita"""
    try:
        reports = PredictiveReports()
        horizon_enum = TimeHorizon(horizon)
        prediction = reports.predict_revenue(horizon_enum)
        
        return {
            'success': True,
            'prediction': {
                'value': prediction.predicted_value,
                'confidence_interval': prediction.confidence_interval,
                'trend': prediction.trend,
                'factors': prediction.factors,
                'accuracy': prediction.accuracy_score
            },
            'generated_at': prediction.generated_at.isoformat()
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_full_predictive_report() -> Dict:
    """Obter relatório preditivo completo"""
    try:
        reports = PredictiveReports()
        return reports.generate_full_report()
    except Exception as e:
        return {'success': False, 'error': str(e)}
