from datetime import datetime
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.username = user_data.get('username')
        self.created_at = user_data.get('created_at')
        
    @staticmethod
    def get_by_email(supabase, email):
        response = supabase.table('users').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def create_user(supabase, email, username, user_id):
        user_data = {
            'id': user_id,
            'email': email,
            'username': username,
            'created_at': datetime.utcnow().isoformat()
        }
        supabase.table('users').insert(user_data).execute()
        return User(user_data)
