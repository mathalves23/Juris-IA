from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sqlite3
import os
import json
from datetime import datetime, timedelta

bp = Blueprint('subscriptions_simple', __name__, url_prefix='/api/subscriptions')

def get_db_connection():
    """Obter conexão com o banco SQLite"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'legalai.db')
    return sqlite3.connect(db_path)

@bp.route('/plans', methods=['GET'])
def get_plans():
    """Lista todos os planos disponíveis"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM plans WHERE is_active = 1")
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
            'plans': plans,
            'total': len(plans)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/plans/<int:plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Obter detalhes de um plano específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM plans WHERE id = ? AND is_active = 1", (plan_id,))
        plan_raw = cursor.fetchone()
        
        if not plan_raw:
            return jsonify({'error': 'Plan not found'}), 404
        
        # Obter nomes das colunas
        cursor.execute("PRAGMA table_info(plans)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Converter para dicionário
        plan_dict = dict(zip(columns, plan_raw))
        if 'features_json' in plan_dict and plan_dict['features_json']:
            try:
                plan_dict['features'] = json.loads(plan_dict['features_json'].replace("'", '"'))
            except:
                plan_dict['features'] = {}
        
        conn.close()
        return jsonify(plan_dict), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_subscription():
    """Obter assinatura atual do usuário"""
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar assinatura do usuário
        cursor.execute("""
            SELECT s.*, p.name as plan_name, p.features_json 
            FROM subscriptions s 
            JOIN plans p ON s.plan_id = p.id 
            WHERE s.user_id = ? 
            ORDER BY s.created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        subscription_raw = cursor.fetchone()
        
        if not subscription_raw:
            return jsonify({
                'subscription': None,
                'has_subscription': False,
                'message': 'No subscription found'
            }), 200
        
        # Converter para dicionário
        columns = ['id', 'user_id', 'plan_id', 'status', 'is_annual', 'start_date', 
                  'end_date', 'trial_end_date', 'amount_paid', 'payment_method', 
                  'stripe_subscription_id', 'monthly_documents_used', 
                  'monthly_templates_used', 'monthly_ai_requests_used', 
                  'last_usage_reset', 'created_at', 'updated_at', 'plan_name', 'features_json']
        
        subscription_dict = dict(zip(columns, subscription_raw))
        
        # Parse features
        if subscription_dict['features_json']:
            try:
                subscription_dict['features'] = json.loads(subscription_dict['features_json'].replace("'", '"'))
            except:
                subscription_dict['features'] = {}
        
        # Calcular dias restantes
        if subscription_dict['end_date']:
            end_date = datetime.fromisoformat(subscription_dict['end_date'].replace('Z', ''))
            days_remaining = max(0, (end_date - datetime.now()).days)
            subscription_dict['days_remaining'] = days_remaining
        
        # Verificar se é trial
        is_trial = False
        if subscription_dict['trial_end_date']:
            trial_end = datetime.fromisoformat(subscription_dict['trial_end_date'].replace('Z', ''))
            is_trial = datetime.now() < trial_end
        subscription_dict['is_trial'] = is_trial
        
        conn.close()
        return jsonify({
            'subscription': subscription_dict,
            'has_subscription': True
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/subscribe', methods=['POST'])
@jwt_required()
def create_subscription():
    """Criar nova assinatura"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        plan_id = data.get('plan_id')
        is_annual = data.get('is_annual', False)
        payment_method = data.get('payment_method', 'credit_card')
        
        if not plan_id:
            return jsonify({'error': 'Plan ID is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se o plano existe
        cursor.execute("SELECT * FROM plans WHERE id = ? AND is_active = 1", (plan_id,))
        plan = cursor.fetchone()
        
        if not plan:
            return jsonify({'error': 'Invalid or inactive plan'}), 400
        
        # Verificar se já tem assinatura ativa
        cursor.execute("""
            SELECT COUNT(*) FROM subscriptions 
            WHERE user_id = ? AND status IN ('active', 'trial')
        """, (user_id,))
        
        existing_count = cursor.fetchone()[0]
        if existing_count > 0:
            return jsonify({'error': 'User already has an active subscription'}), 400
        
        # Criar assinatura
        start_date = datetime.now()
        trial_end = start_date + timedelta(days=7)
        end_date = start_date + timedelta(days=365 if is_annual else 30)
        
        cursor.execute("""
            INSERT INTO subscriptions 
            (user_id, plan_id, status, is_annual, start_date, end_date, trial_end_date, payment_method)
            VALUES (?, ?, 'trial', ?, ?, ?, ?, ?)
        """, (user_id, plan_id, is_annual, start_date, end_date, trial_end, payment_method))
        
        subscription_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Subscription created successfully',
            'subscription_id': subscription_id
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """Obter estatísticas de uso do usuário"""
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar assinatura ativa
        cursor.execute("""
            SELECT s.*, p.features_json 
            FROM subscriptions s 
            JOIN plans p ON s.plan_id = p.id 
            WHERE s.user_id = ? AND s.status IN ('active', 'trial')
            ORDER BY s.created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        subscription = cursor.fetchone()
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Parse features
        features = {}
        if subscription[17]:  # features_json
            try:
                features = json.loads(subscription[17].replace("'", '"'))
            except:
                features = {}
        
        usage_data = {
            'documents': {
                'used': subscription[11],  # monthly_documents_used
                'limit': features.get('monthly_documents', 0)
            },
            'templates': {
                'used': subscription[12],  # monthly_templates_used
                'limit': features.get('monthly_templates', 0)
            },
            'ai_requests': {
                'used': subscription[13],  # monthly_ai_requests_used
                'limit': features.get('monthly_ai_requests', 0)
            }
        }
        
        conn.close()
        return jsonify(usage_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/features', methods=['GET'])
@jwt_required()
def get_available_features():
    """Obter funcionalidades disponíveis no plano atual"""
    try:
        user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar assinatura ativa
        cursor.execute("""
            SELECT s.*, p.features_json, p.name 
            FROM subscriptions s 
            JOIN plans p ON s.plan_id = p.id 
            WHERE s.user_id = ? AND s.status IN ('active', 'trial')
            ORDER BY s.created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        subscription = cursor.fetchone()
        
        if not subscription:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Parse features
        features = {}
        if subscription[17]:  # features_json
            try:
                features = json.loads(subscription[17].replace("'", '"'))
            except:
                features = {}
        
        conn.close()
        return jsonify({
            'plan_name': subscription[18],  # plan name
            'features': features
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500 