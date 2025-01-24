from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    if not email or not password or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        supabase = current_app.config['supabase']
        # Create auth user in Supabase
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if auth_response.user:
            # Create user profile in our users table
            user = User.create_user(supabase, email, username, auth_response.user.id)
            login_user(user)
            return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        supabase = current_app.config['supabase']
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if auth_response.user:
            user_data = User.get_by_email(supabase, email)
            if user_data:
                user = User(user_data)
                login_user(user)
                return jsonify({'message': 'Logged in successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 401

    return jsonify({'error': 'Invalid credentials'}), 401

@auth.route('/logout')
@login_required
def logout():
    try:
        supabase = current_app.config['supabase']
        supabase.auth.sign_out()
        logout_user()
        return jsonify({'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    try:
        supabase = current_app.config['supabase']
        supabase.auth.reset_password_email(email)
        return jsonify({'message': 'Password reset email sent'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
