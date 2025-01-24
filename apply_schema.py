import os
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def read_file(filename):
    with open(filename, 'r') as file:
        return file.read()

def execute_sql(sql):
    # Prepare headers with service role key
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # SQL endpoint
    sql_url = f'{SUPABASE_URL}/rest/v1/rpc/exec_sql'
    
    # Execute SQL
    response = requests.post(
        sql_url,
        headers=headers,
        json={'query': sql}
    )
    
    return response

def apply_schema():
    try:
        # Read SQL files
        function_sql = read_file('create_function.sql')
        schema_sql = read_file('database/schema.sql')
        
        print("Creating exec_sql function...")
        response = execute_sql(function_sql)
        if response.status_code != 200:
            print(f"Error creating function: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        print("Function created successfully!")
        time.sleep(2)  # Wait for function to be available
        
        print("\nApplying schema...")
        response = execute_sql(schema_sql)
        if response.status_code == 200:
            print("Schema applied successfully!")
        else:
            print(f"Error applying schema: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    apply_schema()
