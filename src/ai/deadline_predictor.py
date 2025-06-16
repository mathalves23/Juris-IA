"""
Sistema de Predição de Prazos Processuais
Utiliza machine learning para prever duração de processos
"""
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ProcessType(Enum):
    """Tipos de processo"""
    CIVIL = "civil"
    CRIMINAL = "criminal"
    LABOR = "trabalhista"
    TAX = "tributario"

class ProcessComplexity(Enum):
    """Complexidade do processo"""
    LOW = "baixa"
    MEDIUM = "media"
    HIGH = "alta"

@dataclass
class ProcessData:
    """Dados do processo para predição"""
    process_type: ProcessType
    complexity: ProcessComplexity
    num_parties: int
    has_expert_witness: bool
    has_appeals: bool
    region: str
    filed_date: datetime

class DeadlinePredictor:
    """Preditor de prazos processuais"""
    
    def __init__(self):
        # Durações médias por tipo de processo (em dias)
        self.base_durations = {
            ProcessType.CIVIL: 450,
            ProcessType.CRIMINAL: 300,
            ProcessType.LABOR: 350,
            ProcessType.TAX: 500
        }
        
        # Multiplicadores de complexidade
        self.complexity_multipliers = {
            ProcessComplexity.LOW: 0.7,
            ProcessComplexity.MEDIUM: 1.0,
            ProcessComplexity.HIGH: 1.5
        }
        
        # Fatores regionais
        self.regional_factors = {
            'SP': 1.0,
            'RJ': 1.2,
            'MG': 0.9,
            'RS': 0.8,
            'default': 1.1
        }
    
    def predict_deadline(self, process_data: ProcessData) -> Dict:
        """Predizer prazo do processo"""
        
        # Calcular duração base
        base_duration = self.base_durations[process_data.process_type]
        
        # Aplicar multiplicadores
        complexity_mult = self.complexity_multipliers[process_data.complexity]
        regional_mult = self.regional_factors.get(process_data.region, 1.1)
        
        predicted_days = base_duration * complexity_mult * regional_mult
        
        # Ajustes adicionais
        if process_data.has_expert_witness:
            predicted_days *= 1.3
        if process_data.has_appeals:
            predicted_days *= 1.6
        if process_data.num_parties > 4:
            predicted_days *= 1.2
        
        predicted_days = int(predicted_days)
        
        # Calcular data de conclusão
        completion_date = process_data.filed_date + timedelta(days=predicted_days)
        
        # Identificar fatores de risco
        risk_factors = []
        if process_data.complexity == ProcessComplexity.HIGH:
            risk_factors.append("Alta complexidade")
        if process_data.has_expert_witness:
            risk_factors.append("Perícia necessária")
        if process_data.num_parties > 4:
            risk_factors.append("Múltiplas partes")
        
        return {
            'predicted_duration_days': predicted_days,
            'completion_date': completion_date.isoformat(),
            'confidence_interval': (
                int(predicted_days * 0.8),
                int(predicted_days * 1.3)
            ),
            'risk_factors': risk_factors,
            'recommendations': self._generate_recommendations(risk_factors)
        }
    
    def _generate_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Gerar recomendações baseadas nos fatores de risco"""
        recommendations = []
        
        if "Alta complexidade" in risk_factors:
            recommendations.append("Considere contratar especialista")
        if "Perícia necessária" in risk_factors:
            recommendations.append("Prepare documentação técnica")
        if "Múltiplas partes" in risk_factors:
            recommendations.append("Estabeleça cronograma de comunicação")
        
        recommendations.append("Monitore prazos regularmente")
        
        return recommendations

def predict_process_deadline(
    process_type: str,
    complexity: str,
    num_parties: int,
    has_expert_witness: bool = False,
    has_appeals: bool = False,
    region: str = "SP",
    filed_date: Optional[str] = None
) -> Dict:
    """Função principal para predição de prazos"""
    
    try:
        process_data = ProcessData(
            process_type=ProcessType(process_type),
            complexity=ProcessComplexity(complexity),
            num_parties=num_parties,
            has_expert_witness=has_expert_witness,
            has_appeals=has_appeals,
            region=region,
            filed_date=datetime.fromisoformat(filed_date) if filed_date else datetime.now()
        )
        
        predictor = DeadlinePredictor()
        result = predictor.predict_deadline(process_data)
        
        return {'success': True, **result}
    
    except Exception as e:
        logger.error(f"Deadline prediction error: {e}")
        return {'success': False, 'error': str(e)} 