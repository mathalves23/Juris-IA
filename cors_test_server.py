#!/usr/bin/env python3
"""
Servidor de teste para resolver problemas de CORS rapidamente
Execute: python cors_test_server.py
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import time
import random
import json

# Criar app Flask
app = Flask(__name__)

# CORS MUITO PERMISSIVO
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": "*"
    }
})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# === HEALTH CHECK ===
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'JurisIA Test API',
        'version': '2.0.0',
        'cors': 'enabled'
    })

# === IA ROUTES ===
@app.route('/api/ai/generate', methods=['POST', 'OPTIONS'])
def ai_generate():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Teste')
        
        # Simular processamento
        time.sleep(0.5)
        
        responses = [
            f"Com base no prompt '{prompt}', elaborei um documento jurídico completo considerando a legislação brasileira.",
            f"Analisando '{prompt}', sugiro o seguinte texto legal com base nos precedentes jurisprudenciais.",
            f"Para '{prompt}', criei um documento que atende aos requisitos legais vigentes."
        ]
        
        return jsonify({
            "success": True,
            "generated_text": random.choice(responses),
            "suggestions": [
                "Revisar cláusulas específicas",
                "Adicionar referências legais",
                "Verificar formatação"
            ],
            "confidence": round(random.uniform(0.85, 0.98), 2),
            "metadata": {
                "model": "JurisIA-GPT-4",
                "tokens": random.randint(100, 500)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# === CONTRACT ANALYZER ROUTES ===
@app.route('/api/contract-analyzer/analyses', methods=['GET', 'OPTIONS'])
def contract_analyses():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        limit = request.args.get('limit', 20, type=int)
        
        mock_data = [
            {
                "id": 1,
                "title": "Contrato de Prestação de Serviços",
                "status": "completed",
                "score_risco": 3,
                "nivel_complexidade": "medium",
                "created_at": "2024-12-13T10:00:00Z",
                "clausulas_extraidas": ["Pagamento", "Rescisão", "Confidencialidade"],
                "riscos_identificados": ["Ausência de multa por atraso"]
            },
            {
                "id": 2,
                "title": "Contrato de Locação Comercial", 
                "status": "analyzing",
                "score_risco": 2,
                "nivel_complexidade": "low",
                "created_at": "2024-12-13T11:00:00Z",
                "clausulas_extraidas": ["Prazo", "Valor", "Reajuste"],
                "riscos_identificados": ["Índice não especificado"]
            },
            {
                "id": 3,
                "title": "Contrato de Compra e Venda",
                "status": "completed",
                "score_risco": 1,
                "nivel_complexidade": "low",
                "created_at": "2024-12-13T09:00:00Z",
                "clausulas_extraidas": ["Preço", "Entrega", "Garantia"],
                "riscos_identificados": []
            }
        ]
        
        return jsonify({
            'success': True,
            'data': mock_data[:limit],
            'total': len(mock_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contract-analyzer/stats', methods=['GET', 'OPTIONS'])
def contract_stats():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        return jsonify({
            'success': True,
            'data': {
                "total_analyses": 25,
                "completed_analyses": 20,
                "pending_analyses": 5,
                "average_risk_score": 2.3,
                "risk_distribution": {
                    "low": 12,
                    "medium": 8,
                    "high": 5
                },
                "analyses_this_month": 15,
                "time_saved_hours": 67.5
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# === ROOT ===
@app.route('/')
def root():
    return jsonify({
        'message': 'JurisIA Test API funcionando!',
        'version': '2.0.0',
        'cors': 'habilitado',
        'endpoints': [
            '/health',
            '/api/ai/generate',
            '/api/contract-analyzer/analyses',
            '/api/contract-analyzer/stats'
        ]
    })

if __name__ == '__main__':
    print("🚀 Iniciando servidor de teste JurisIA...")
    print("📍 URL: http://localhost:5000")
    print("🔧 CORS: Totalmente habilitado")
    print("✅ APIs funcionais para demonstração")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    ) 