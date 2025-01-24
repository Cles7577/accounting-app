import os
from dotenv import load_dotenv
from supabase import create_client
import uuid
import requests

load_dotenv()

def test_project_creation():
    # Initialize Supabase client with service role key
    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not service_role_key:
        raise ValueError("Missing required environment variables")
    
    supabase = create_client(supabase_url, service_role_key)
    
    try:
        # Create a test user in auth.users first
        headers = {
            'apikey': service_role_key,
            'Authorization': f'Bearer {service_role_key}',
            'Content-Type': 'application/json'
        }
        
        test_user_id = str(uuid.uuid4())
        test_email = f"test_{test_user_id}@example.com"
        
        # Create auth user
        auth_response = requests.post(
            f"{supabase_url}/auth/v1/admin/users",
            headers=headers,
            json={
                'id': test_user_id,
                'email': test_email,
                'password': 'test_password',
                'email_confirmed': True
            }
        )
        
        if auth_response.status_code != 200:
            raise Exception(f"Failed to create auth user: {auth_response.text}")
        
        print("Successfully created auth user")
        
        # Create user in public.users table
        supabase.table('users').insert({
            'id': test_user_id,
            'email': test_email,
            'username': f'test_user_{test_user_id[:8]}'
        }).execute()
        print("Successfully created user record")
        
        # Create test project
        project_data = {
            'name': 'Test Project',
            'description': 'Test Description',
            'capital': 1000,
            'created_by': test_user_id,
            'status': 'active'
        }
        
        # Insert project
        response = supabase.table('projects').insert(project_data).execute()
        print("Successfully created test project with data:", response.data)
        
        # Clean up
        if response.data:
            project_id = response.data[0]['id']
            supabase.table('projects').delete().eq('id', project_id).execute()
            print("Successfully cleaned up test project")
        
        # Delete user record
        supabase.table('users').delete().eq('id', test_user_id).execute()
        print("Successfully cleaned up user record")
        
        # Delete auth user
        requests.delete(
            f"{supabase_url}/auth/v1/admin/users/{test_user_id}",
            headers=headers
        )
        print("Successfully cleaned up auth user")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_project_creation()
    print("Test completed")
