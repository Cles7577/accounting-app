from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models.project import Project, ProjectMember

bp = Blueprint('projects', __name__)

@bp.route('/', methods=['GET'])
@login_required
def get_projects():
    try:
        supabase = current_app.config['supabase']
        projects = Project.get_user_projects(supabase, current_user.id)
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'created_at': p.created_at
        } for p in projects])
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Project name is required'}), 400

    try:
        supabase = current_app.config['supabase']
        project = Project.create_project(supabase, name, description, current_user.id)
        
        # Add creator as admin
        ProjectMember.add_member(supabase, project.id, current_user.id, ProjectMember.ROLE_ADMIN)
        
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/<project_id>/members', methods=['POST'])
@login_required
def add_member(project_id):
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')

    if not email or not role:
        return jsonify({'error': 'Email and role are required'}), 400

    if role not in [ProjectMember.ROLE_ADMIN, ProjectMember.ROLE_EDITOR, ProjectMember.ROLE_VIEWER]:
        return jsonify({'error': 'Invalid role'}), 400

    try:
        supabase = current_app.config['supabase']
        
        # Check if user exists
        user_data = User.get_by_email(supabase, email)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        # Add member
        member = ProjectMember.add_member(supabase, project_id, user_data['id'], role)
        return jsonify({
            'project_id': member.project_id,
            'user_id': member.user_id,
            'role': member.role,
            'joined_at': member.joined_at
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
