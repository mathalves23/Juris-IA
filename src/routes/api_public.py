from flask import Blueprint, request, jsonify
import time
import random
from datetime import datetime

api_public_bp = Blueprint('api_public', __name__)

# === CORS HELPER ===
def add_cors_headers(response):
    """Adiciona headers CORS a qualquer response"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# === ROTAS PÚBLICAS PARA DEMONSTRAÇÃO ===

@api_public_bp.route('/generate', methods=['POST', 'OPTIONS'])
def generate_text():
    """Gerar texto jurídico usando IA (versão pública)."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
        
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Gerar documento jurídico')
        
        # Simular processamento IA
        time.sleep(0.5)
        
        response_data = {
            "success": True,
            "generated_text": f"Texto gerado para: {prompt}. Este é um documento jurídico modelo gerado pela IA.",
            "suggestions": ["Revisar cláusulas", "Adicionar referências"],
            "confidence": 0.9
        }
        
        response = jsonify(response_data)
        return add_cors_headers(response), 200
        
    except Exception as e:
        response = jsonify({"success": False, "error": str(e)})
        return add_cors_headers(response), 500

@api_public_bp.route('/contract-analyzer/analyses', methods=['GET', 'OPTIONS'])
def get_analyses():
    """Retorna lista de análises de contratos."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
        
    try:
        mock_analyses = [
            {"id": 1, "title": "Contrato de Prestação", "status": "completed"},
            {"id": 2, "title": "Contrato de Locação", "status": "analyzing"}
        ]
        
        response = jsonify({'success': True, 'data': mock_analyses})
        return add_cors_headers(response), 200
        
    except Exception as e:
        response = jsonify({'success': False, 'error': str(e)})
        return add_cors_headers(response), 500

@api_public_bp.route('/contract-analyzer/stats', methods=['GET', 'OPTIONS'])
def get_stats():
    """Retorna estatísticas das análises."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
        
    try:
        mock_stats = {
            "total_analyses": 15,
            "completed_analyses": 12,
            "pending_analyses": 3
        }
        
        response = jsonify({'success': True, 'data': mock_stats})
        return add_cors_headers(response), 200
        
    except Exception as e:
        response = jsonify({'success': False, 'error': str(e)})
        return add_cors_headers(response), 500

@api_public_bp.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Health check das APIs públicas."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        return add_cors_headers(response)
    
    response = jsonify({
        'status': 'healthy',
        'service': 'JurisIA Public API',
        'version': '2.0.0'
    })
    return add_cors_headers(response), 200 