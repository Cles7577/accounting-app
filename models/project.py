from datetime import datetime
import uuid

class Project:
    def __init__(self, project_data):
        self.id = project_data.get('id')
        self.name = project_data.get('name')
        self.description = project_data.get('description')
        self.capital = project_data.get('capital', 0)  # Default to 0 if not specified
        self.created_by = project_data.get('created_by')
        self.created_at = project_data.get('created_at')
        self.status = project_data.get('status', 'active')  # Default to active if not specified

    @staticmethod
    def create_project(supabase, name, description, created_by, capital=0):
        # Generate a new UUID for the project
        project_id = str(uuid.uuid4())
        
        # SQL to insert project and member
        sql = """
        WITH new_project AS (
            INSERT INTO projects (id, name, description, capital, created_by, status)
            VALUES ($1, $2, $3, $4, $5, 'active')
            RETURNING *
        )
        INSERT INTO project_members (project_id, user_id, role)
        SELECT id, created_by, 'admin'
        FROM new_project
        RETURNING (SELECT row_to_json(new_project.*) FROM new_project);
        """
        
        # Execute the SQL
        result = supabase.rpc(
            'exec_sql_with_result',
            {
                'query': sql,
                'params': [project_id, name, description, capital, created_by]
            }
        ).execute()
        
        if not result.data or not result.data[0] or 'row_to_json' not in result.data[0]:
            raise Exception("Failed to create project")
            
        return Project(result.data[0]['row_to_json'])

    @staticmethod
    def get_user_projects(supabase, user_id):
        # SQL to get user's projects
        sql = """
        SELECT p.*
        FROM projects p
        INNER JOIN project_members pm ON p.id = pm.project_id
        WHERE pm.user_id = $1;
        """
        
        # Execute the SQL
        result = supabase.rpc(
            'exec_sql_with_result',
            {
                'query': sql,
                'params': [user_id]
            }
        ).execute()
        
        if not result.data:
            return []
            
        return [Project(project) for project in result.data]

class ProjectMember:
    ROLE_ADMIN = 'admin'
    ROLE_EDITOR = 'editor'
    ROLE_VIEWER = 'viewer'

    def __init__(self, member_data):
        self.project_id = member_data.get('project_id')
        self.user_id = member_data.get('user_id')
        self.role = member_data.get('role')
        self.joined_at = member_data.get('joined_at')

    @staticmethod
    def add_member(supabase, project_id, user_id, role):
        sql = """
        INSERT INTO project_members (project_id, user_id, role)
        VALUES ($1, $2, $3)
        RETURNING *;
        """
        
        result = supabase.rpc(
            'exec_sql_with_result',
            {
                'query': sql,
                'params': [project_id, user_id, role]
            }
        ).execute()
        
        if not result.data:
            raise Exception("Failed to add member")
            
        return ProjectMember(result.data[0])
