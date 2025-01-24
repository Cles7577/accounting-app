from flask import Blueprint, render_template, request, jsonify, g
from models.project import Project
from models.transaction import Transaction
from auth import login_required
import uuid

bp = Blueprint('project', __name__, url_prefix='/projects')

@bp.route('/')
@login_required
def list_projects():
    projects = Project.get_user_projects(g.supabase, g.user['id'])
    return render_template('projects.html', projects=projects)

@bp.route('/<project_id>')
@login_required
def view_project(project_id):
    # Get project details
    project = None
    projects = Project.get_user_projects(g.supabase, g.user['id'])
    for p in projects:
        if p.id == project_id:
            project = p
            break
    
    if not project:
        return 'Project not found', 404

    # Get transactions
    transactions = Transaction.get_project_transactions(project_id)
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == Transaction.TYPE_INCOME)
    total_expenses = sum(t.amount for t in transactions if t.type == Transaction.TYPE_EXPENSE)
    balance = total_income - total_expenses

    return render_template('project_detail.html',
                         project=project,
                         transactions=transactions,
                         balance=balance,
                         total_income=total_income,
                         total_expenses=total_expenses)

# API endpoints
@bp.route('/api/projects', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()
    
    try:
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Create project directly
        project_data = {
            'id': project_id,
            'name': data['name'],
            'description': data['description'],
            'capital': float(data.get('capital', 0)),
            'created_by': g.user['id'],
            'status': 'active'
        }
        
        # Insert project
        project_result = g.supabase.table('projects').insert(project_data).execute()
        
        if not project_result.data:
            raise Exception("Failed to create project")
            
        # Create project member
        member_data = {
            'project_id': project_id,
            'user_id': g.user['id'],
            'role': 'admin'
        }
        
        member_result = g.supabase.table('project_members').insert(member_data).execute()
        
        if not member_result.data:
            # Rollback project creation
            g.supabase.table('projects').delete().eq('id', project_id).execute()
            raise Exception("Failed to add project member")
            
        return jsonify({'id': project_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/api/projects/<project_id>/transactions', methods=['POST'])
@login_required
def create_transaction(project_id):
    data = request.get_json()
    
    try:
        transaction = Transaction.create_transaction(
            g.supabase,
            project_id=project_id,
            amount=float(data['amount']),
            type=data['type'],
            category=data['category'],
            description=data.get('description', ''),
            created_by=g.user['id']
        )
        return jsonify({'id': transaction.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
