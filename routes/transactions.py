from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models.transaction import Transaction
from models.project import ProjectMember

bp = Blueprint('transactions', __name__)

def check_project_access(supabase, project_id, required_role=ProjectMember.ROLE_VIEWER):
    response = supabase.table('project_members').select('role').eq('project_id', project_id).eq('user_id', current_user.id).execute()
    if not response.data:
        return False
    
    user_role = response.data[0]['role']
    role_hierarchy = {
        ProjectMember.ROLE_ADMIN: 3,
        ProjectMember.ROLE_EDITOR: 2,
        ProjectMember.ROLE_VIEWER: 1
    }
    return role_hierarchy[user_role] >= role_hierarchy[required_role]

@bp.route('/<project_id>/transactions', methods=['GET'])
@login_required
def get_transactions(project_id):
    try:
        supabase = current_app.config['supabase']
        if not check_project_access(supabase, project_id):
            return jsonify({'error': 'Access denied'}), 403

        transactions = Transaction.get_project_transactions(supabase, project_id)
        return jsonify([{
            'id': t.id,
            'amount': t.amount,
            'type': t.type,
            'category': t.category,
            'description': t.description,
            'created_at': t.created_at
        } for t in transactions])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<project_id>/transactions', methods=['POST'])
@login_required
def create_transaction(project_id):
    if not check_project_access(supabase, project_id, ProjectMember.ROLE_EDITOR):
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    amount = data.get('amount')
    type = data.get('type')
    category = data.get('category')
    description = data.get('description')

    if not amount or not type or not category:
        return jsonify({'error': 'Amount, type, and category are required'}), 400

    if type not in [Transaction.TYPE_INCOME, Transaction.TYPE_EXPENSE]:
        return jsonify({'error': 'Invalid transaction type'}), 400

    try:
        supabase = current_app.config['supabase']
        transaction = Transaction.create_transaction(
            supabase, project_id, amount, type, category, 
            description, current_user.id
        )
        
        return jsonify({
            'id': transaction.id,
            'amount': transaction.amount,
            'type': transaction.type,
            'category': transaction.category,
            'description': transaction.description,
            'created_at': transaction.created_at
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<project_id>/summary', methods=['GET'])
@login_required
def get_project_summary(project_id):
    try:
        supabase = current_app.config['supabase']
        if not check_project_access(supabase, project_id):
            return jsonify({'error': 'Access denied'}), 403

        summary = Transaction.get_project_summary(supabase, project_id)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
