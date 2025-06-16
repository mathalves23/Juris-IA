from flask import Blueprint, jsonify
import sqlite3
import os
import json

bp = Blueprint('test_plans', __name__, url_prefix='/api/test')

@bp.route('/plans', methods=['GET'])
def test_plans():
    """Testar acesso direto aos planos via SQLite"""
    try:
        # Caminho do banco
        db_path = os.path.join(os.path.dirname(__file__), '..', 'legalai.db')
        
        if not os.path.exists(db_path):
            return jsonify({
                'error': 'Database file not found',
                'path': db_path,
                'exists': False
            }), 404
        
        # Conectar diretamente
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Verificar planos
        if 'plans' in tables:
            cursor.execute("SELECT * FROM plans")
            plans_raw = cursor.fetchall()
            
            # Obter nomes das colunas
            cursor.execute("PRAGMA table_info(plans)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Converter para dicionários
            plans = []
            for plan_raw in plans_raw:
                plan_dict = dict(zip(columns, plan_raw))
                # Parse features_json
                if 'features_json' in plan_dict and plan_dict['features_json']:
                    try:
                        plan_dict['features'] = json.loads(plan_dict['features_json'].replace("'", '"'))
                    except:
                        plan_dict['features'] = {}
                plans.append(plan_dict)
            
            conn.close()
            return jsonify({
                'success': True,
                'plans': plans,
                'total': len(plans),
                'tables': tables,
                'db_path': db_path
            }), 200
        else:
            conn.close()
            return jsonify({
                'error': 'Plans table not found',
                'tables': tables,
                'db_path': db_path
            }), 404
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'db_path': db_path if 'db_path' in locals() else 'unknown'
        }), 500

@bp.route('/db-info', methods=['GET'])
def db_info():
    """Informações do banco de dados"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'legalai.db')
        
        return jsonify({
            'db_path': db_path,
            'exists': os.path.exists(db_path),
            'size': os.path.getsize(db_path) if os.path.exists(db_path) else 0,
            'current_dir': os.getcwd(),
            'script_dir': os.path.dirname(__file__)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500 