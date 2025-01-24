from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, g, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from supabase import create_client, Client
from dotenv import load_dotenv
from flask_cors import CORS
from flask_session import Session
import os
from datetime import datetime, timedelta
import pytz

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session lifetime
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True

# Initialize Flask-Session
Session(app)

CORS(app)

# Initialize Supabase clients
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Create two clients - one for auth (anon key) and one for database operations (service role key)
supabase_auth: Client = create_client(supabase_url, supabase_key)
supabase_db: Client = create_client(supabase_url, supabase_service_key)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Template filters
@app.template_filter('format_datetime')
def format_datetime(value):
    if not value:
        return ''
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
            
        # Convert to Malaysia timezone (UTC+8)
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        malaysia_time = dt.astimezone(malaysia_tz)
        
        return malaysia_time.strftime('%Y-%m-%d %I:%M %p')
    except Exception as e:
        print(f"Error formatting datetime: {str(e)}")
        return value

@app.template_filter('datetime')
def datetime_filter(value):
    if not value:
        return ''
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
            
        # Convert to Malaysia timezone (UTC+8)
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        malaysia_time = dt.astimezone(malaysia_tz)
        
        return malaysia_time.strftime('%Y-%m-%d %I:%M %p')
    except Exception as e:
        print(f"Error formatting datetime: {str(e)}")
        return value

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.username = user_data.get('username')
        self._is_active = True
        self._is_authenticated = True

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_authenticated(self):
        return self._is_authenticated

    @property
    def is_anonymous(self):
        return False

@login_manager.user_loader
def load_user(user_id):
    try:
        # Use service role client for user data to ensure we can always load the user
        user_data = supabase_db.from_('users').select('*').eq('id', user_id).single().execute()
        if user_data.data:
            return User(user_data.data)
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

@app.before_request
def before_request():
    g.supabase_auth = supabase_auth
    g.supabase = supabase_db  # Use service role client for database operations
    if current_user.is_authenticated:
        g.user = {'id': current_user.id, 'email': current_user.email, 'username': current_user.username}
        session.permanent = True  # Make the session permanent

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username = request.form.get('username')

        try:
            # Use auth client for registration
            auth_response = supabase_auth.auth.sign_up({
                "email": email,
                "password": password
            })

            if auth_response.user and auth_response.user.id:
                # Use service role client for user data
                user_data = {
                    'id': auth_response.user.id,
                    'email': email,
                    'username': username
                }
                supabase_db.from_('users').insert(user_data).execute()

                # Log the user in
                user = User(user_data)
                login_user(user)
                session.permanent = True  # Make the session permanent
                
                flash('Registration successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Registration failed. Please try again.', 'error')

        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        try:
            print(f"Attempting login for email: {email}")
            # Use auth client for login
            auth_response = supabase_auth.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            print(f"Auth response user: {auth_response.user}")
            if auth_response.user:
                print(f"User authenticated: {auth_response.user.id}")
                # Use service role client for user data
                user_data = supabase_db.from_('users').select('*').eq('id', auth_response.user.id).single().execute()
                print(f"User data: {user_data.data}")
                
                if user_data.data:
                    user = User(user_data.data)
                    login_user(user, remember=remember)
                    session['user_id'] = user.id  # Store user ID in session
                    session.permanent = True  # Make the session permanent
                    flash('Login successful!', 'success')
                    print("Redirecting to dashboard...")
                    
                    # Get the next page from the URL parameters, defaulting to dashboard
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('dashboard')
                    return redirect(next_page)
            
            flash('Invalid email or password.', 'error')

        except Exception as e:
            print(f"Login error: {str(e)}")
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    try:
        supabase_auth.auth.sign_out()
        logout_user()
        session.clear()  # Clear the session
        flash('You have been logged out.', 'success')
    except Exception as e:
        flash(f'Logout failed: {str(e)}', 'error')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        print("\n=== Loading Dashboard ===")
        print(f"User ID: {current_user.id}")
        print(f"User Email: {current_user.email}")
        print(f"User Username: {current_user.username}")
        
        # Initialize empty lists and sets
        teams_data = []
        team_ids = set()
        projects_data = {}  # Change to dict to track unique projects by ID
        project_ids = set()
        transactions_data = []
        total_income = 0
        total_expenses = 0
        
        try:
            # 1. Get teams where user is owner
            print("\nFetching owned teams...")
            owned_teams = supabase_db.from_('teams').select('*').eq('created_by', current_user.id).execute()
            print(f"Owned teams: {owned_teams.data}")
            if owned_teams.data:
                teams_data.extend(owned_teams.data)
                team_ids.update(team['id'] for team in owned_teams.data)
        except Exception as e:
            print(f"Error fetching owned teams: {str(e)}")
        
        try:
            # 2. Get teams where user is a member
            print("\nFetching team memberships...")
            team_memberships = supabase_db.from_('team_members').select('team_id').eq('user_id', current_user.id).execute()
            print(f"Team memberships: {team_memberships.data}")
            if team_memberships.data:
                member_team_ids = [tm['team_id'] for tm in team_memberships.data]
                member_teams = supabase_db.from_('teams').select('*').in_('id', member_team_ids).execute()
                print(f"Member teams: {member_teams.data}")
                if member_teams.data:
                    teams_data.extend(member_teams.data)
                    team_ids.update(team['id'] for team in member_teams.data)
        except Exception as e:
            print(f"Error fetching team memberships: {str(e)}")
        
        # Get team members for each team
        try:
            print("\nFetching team members...")
            for team in teams_data:
                print(f"\n=== Processing Team {team['id']} ===")
                print(f"Team name: {team.get('name')}")
                print(f"Team owner: {team.get('created_by')}")
                team['members'] = []
                
                # Add owner first
                print("\nGetting owner info...")
                owner_result = supabase_db.from_('users').select('*').eq('id', team['created_by']).execute()
                print(f"Owner query result: {owner_result.data}")
                
                if owner_result.data:
                    owner = owner_result.data[0]
                    team['members'].append({
                        'username': owner['username'],
                        'email': owner['email'],
                        'role': 'owner'
                    })
                    print(f"Added owner: {owner['username']}")
                
                # Get all team members
                print("\nGetting team members...")
                members_query = supabase_db.from_('team_members')\
                    .select('*')\
                    .eq('team_id', team['id'])\
                    .execute()
                print(f"Team users query: {members_query}")
                print(f"Members query result: {members_query.data}")
                
                if members_query.data:
                    print(f"\nFound {len(members_query.data)} team members")
                    for member in members_query.data:
                        print(f"\nProcessing member: {member}")
                        # Get user details
                        user_result = supabase_db.from_('users')\
                            .select('id, username, email')\
                            .eq('id', member['user_id'])\
                            .execute()
                        print(f"User query result: {user_result.data}")
                        
                        if user_result.data:
                            user = user_result.data[0]
                            print(f"User ID: {user['id']}")
                            print(f"Team owner ID: {team['created_by']}")
                            
                            # Only add if not the owner
                            if str(user['id']) != str(team['created_by']):
                                team['members'].append({
                                    'username': user['username'],
                                    'email': user['email'],
                                    'role': member['role']
                                })
                                print(f"Added team member: {user['username']}")
                            else:
                                print("Skipping owner")
                        else:
                            print(f"Warning: Could not find user data for member {member['user_id']}")
                else:
                    print("No additional members found")
                
                print(f"\nFinal team {team['id']} members: {team['members']}")
        except Exception as e:
            print(f"Error fetching team members: {str(e)}")
        
        try:
            # 3. Get projects where user is owner
            print("\nFetching owned projects...")
            owned_projects = supabase_db.from_('projects').select('*').eq('created_by', current_user.id).execute()
            print(f"Owned projects: {owned_projects.data}")
            if owned_projects.data:
                for project in owned_projects.data:
                    if project['id'] not in projects_data:
                        projects_data[project['id']] = project
                        project_ids.add(project['id'])
        except Exception as e:
            print(f"Error fetching owned projects: {str(e)}")
        
        try:
            # 4. Get projects where user is direct member
            print("\nFetching project memberships...")
            project_memberships = supabase_db.from_('project_users').select('project_id').eq('user_id', current_user.id).execute()
            print(f"Project memberships: {project_memberships.data}")
            if project_memberships.data:
                member_project_ids = [pm['project_id'] for pm in project_memberships.data]
                member_projects = supabase_db.from_('projects').select('*').in_('id', member_project_ids).execute()
                print(f"Member projects: {member_projects.data}")
                if member_projects.data:
                    for project in member_projects.data:
                        if project['id'] not in projects_data:
                            projects_data[project['id']] = project
                            project_ids.add(project['id'])
        except Exception as e:
            print(f"Error fetching project memberships: {str(e)}")
        
        try:
            # 5. Get projects from teams
            if team_ids:
                print("\nFetching team projects...")
                team_projects = supabase_db.from_('projects').select('*').in_('team_id', list(team_ids)).execute()
                print(f"Team projects: {team_projects.data}")
                if team_projects.data:
                    for project in team_projects.data:
                        if project['id'] not in projects_data:
                            projects_data[project['id']] = project
                            project_ids.add(project['id'])
        except Exception as e:
            print(f"Error fetching team projects: {str(e)}")
        
        try:
            # 6. Get all transactions from accessible projects
            if project_ids:
                print("\nFetching transactions...")
                transactions = supabase_db.from_('transactions') \
                    .select('*, projects(name)') \
                    .in_('project_id', list(project_ids)) \
                    .order('created_at', desc=True) \
                    .limit(10) \
                    .execute()
                print(f"Transactions: {transactions.data}")
                
                if transactions.data:
                    # Get usernames for transaction creators
                    user_ids = set(t['created_by'] for t in transactions.data)
                    users = supabase_db.from_('users').select('id, username').in_('id', list(user_ids)).execute()
                    print(f"Users: {users.data}")
                    user_map = {u['id']: u['username'] for u in users.data} if users.data else {}
                    
                    for t in transactions.data:
                        t['created_by_username'] = user_map.get(t['created_by'], 'Unknown')
                        t['project_name'] = t['projects']['name'] if t['projects'] else 'Unknown Project'
                    transactions_data = transactions.data
        except Exception as e:
            print(f"Error fetching transactions: {str(e)}")
        
        try:
            # Calculate project-specific totals and member counts
            for project in projects_data.values():
                project_id = project['id']
                print(f"\nCalculating totals for project {project_id}")
                
                # Get total income and expenses for this project
                income_result = supabase_db.from_('transactions') \
                    .select('amount') \
                    .eq('project_id', project_id) \
                    .eq('type', 'income') \
                    .execute()
                
                expense_result = supabase_db.from_('transactions') \
                    .select('amount') \
                    .eq('project_id', project_id) \
                    .eq('type', 'expense') \
                    .execute()
                
                # Calculate total balance
                project_income = sum(float(t['amount']) for t in income_result.data) if income_result.data else 0
                project_expenses = sum(float(t['amount']) for t in expense_result.data) if expense_result.data else 0
                total_balance = project_income - project_expenses
                print(f"Project total balance: {total_balance}")
                
                # Get total number of members
                member_count_result = supabase_db.from_('project_users') \
                    .select('id') \
                    .eq('project_id', project_id) \
                    .execute()
                member_count = len(member_count_result.data) if member_count_result.data else 1  # At least 1 member (owner)
                print(f"Project member count: {member_count}")
                
                # Calculate per-member share
                per_member_share = total_balance / member_count if member_count > 0 else 0
                print(f"Per member share: {per_member_share}")
                
                # Calculate current user's contribution/deduction
                user_transactions = supabase_db.from_('transactions') \
                    .select('type, amount') \
                    .eq('project_id', project_id) \
                    .eq('created_by', current_user.id) \
                    .execute()
                
                user_total = 0
                if user_transactions.data:
                    for t in user_transactions.data:
                        if t['type'] == 'income':
                            user_total += float(t['amount'])
                        else:  # expense
                            user_total -= float(t['amount'])
                
                # Final initial capital calculation
                initial_capital = per_member_share - user_total
                print(f"User's total transactions: {user_total}")
                print(f"Final initial capital: {initial_capital}")
                
                # Update the project data with the calculated initial capital
                project['initial_capital'] = round(initial_capital, 2)
        except Exception as e:
            print(f"Error calculating project totals: {str(e)}")
        
        try:
            # 7. Calculate totals
            if project_ids:
                print("\nCalculating totals...")
                # Calculate total income
                income_result = supabase_db.from_('transactions') \
                    .select('amount') \
                    .in_('project_id', list(project_ids)) \
                    .eq('type', 'income') \
                    .execute()
                print(f"Income transactions: {income_result.data}")
                if income_result.data:
                    total_income = sum(float(t['amount']) for t in income_result.data)
                
                # Calculate total expenses
                expense_result = supabase_db.from_('transactions') \
                    .select('amount') \
                    .in_('project_id', list(project_ids)) \
                    .eq('type', 'expense') \
                    .execute()
                print(f"Expense transactions: {expense_result.data}")
                if expense_result.data:
                    total_expenses = sum(float(t['amount']) for t in expense_result.data)
        except Exception as e:
            print(f"Error calculating totals: {str(e)}")
        
        print("\n=== Dashboard Data ===")
        print(f"Teams: {len(teams_data)}")
        print(f"Projects: {len(projects_data)}")
        print(f"Recent Transactions: {len(transactions_data)}")
        print(f"Total Income: {total_income}")
        print(f"Total Expenses: {total_expenses}")
        
        return render_template('dashboard.html', 
            user=current_user,
            teams=teams_data,
            projects=list(projects_data.values()),  # Convert dict values to list
            transactions=transactions_data,
            total_income=total_income,
            total_expenses=total_expenses)
                           
    except Exception as e:
        print("\n=== Dashboard Error ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error loading dashboard data.', 'error')
        return render_template('dashboard.html',
            user=current_user,
            teams=[],
            projects=[],
            transactions=[],
            total_income=0,
            total_expenses=0)

@app.route('/team', methods=['POST'])
@login_required
def create_team():
    try:
        print("\n=== Creating Team ===")
        name = request.form.get('name')
        print(f"Team name: {name}")
        
        if not name:
            print("No team name provided")
            flash('Team name is required.', 'error')
            return redirect(url_for('dashboard'))
            
        # Create team
        team_data = {
            'name': name,
            'created_by': current_user.id
        }
        print(f"Creating team with data: {team_data}")
        
        team_result = supabase_db.from_('teams').insert(team_data).execute()
        print(f"Team creation result: {team_result.data}")
        
        if team_result.data:
            team_id = team_result.data[0]['id']
            
            # Add creator as team owner
            owner_data = {
                'team_id': team_id,
                'user_id': current_user.id,
                'role': 'owner'
            }
            print(f"Adding owner with data: {owner_data}")
            
            try:
                owner_result = supabase_db.from_('team_members').insert(owner_data).execute()
                print(f"Owner addition result: {owner_result.data}")
                
                if owner_result.data:
                    flash('Team created successfully!', 'success')
                else:
                    print("Failed to add owner")
                    flash('Team created but failed to set owner.', 'warning')
            except Exception as owner_error:
                print(f"Error adding owner: {str(owner_error)}")
                flash('Team created but failed to set owner.', 'warning')
        else:
            print("Failed to create team")
            flash('Failed to create team.', 'error')
            
    except Exception as e:
        print(f"Error creating team: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error creating team. Please try again.', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/team/<team_id>/member', methods=['POST'])
@login_required
def add_team_member(team_id):
    try:
        print(f"\n=== Adding Team Member ===")
        print(f"Team ID: {team_id}")
        print(f"Current User: {current_user.id}")
        
        # Get username from form
        username = request.form.get('username')
        print(f"Username to add: {username}")
        
        if not username:
            print("No username provided")
            flash('Username is required.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get team and verify ownership
        print(f"Checking team ownership for team {team_id} and user {current_user.id}")
        
        # First, let's check if the team exists and get its details
        team_details = supabase_db.from_('teams')\
            .select('*')\
            .eq('id', team_id)\
            .execute()
        print(f"Team details: {team_details.data}")
        
        if not team_details.data:
            print("Team not found")
            flash('Team not found.', 'error')
            return redirect(url_for('dashboard'))
            
        # Now check team membership and role
        team_query = supabase_db.from_('team_members')\
            .select('*')\
            .eq('team_id', team_id)\
            .eq('user_id', current_user.id)\
            .execute()
        print(f"Team membership details: {team_query.data}")
        
        # Check if user is either the team owner or the team creator
        is_team_owner = any(member['role'] == 'owner' for member in team_query.data)
        is_team_creator = team_details.data[0]['created_by'] == current_user.id
        
        print(f"Is team owner: {is_team_owner}")
        print(f"Is team creator: {is_team_creator}")
        
        if not (is_team_owner or is_team_creator):
            print("Not team owner or creator")
            flash('You must be the team owner to add members.', 'error')
            return redirect(url_for('dashboard'))
        
        # Find user by username
        user_query = supabase_db.from_('users')\
            .select('id, username')\
            .eq('username', username)\
            .execute()
        print(f"User lookup result: {user_query.data}")
        
        if not user_query.data:
            print("User not found")
            flash('User not found.', 'error')
            return redirect(url_for('dashboard'))
            
        user_to_add = user_query.data[0]
        
        # Check if already a member
        member_check = supabase_db.from_('team_members')\
            .select('id')\
            .eq('team_id', team_id)\
            .eq('user_id', user_to_add['id'])\
            .execute()
        print(f"Member check result: {member_check.data}")
        
        if member_check.data:
            print("Already a member")
            flash(f'{username} is already a member of this team.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Add to team
        member_data = {
            'team_id': team_id,
            'user_id': user_to_add['id'],
            'role': 'member'
        }
        print(f"Adding member with data: {member_data}")
        
        result = supabase_db.from_('team_members')\
            .insert(member_data)\
            .execute()
        print(f"Add member result: {result.data}")
        
        if result.data:
            print("Successfully added member")
            flash(f'{username} added to team successfully!', 'success')
        else:
            print("Failed to add member")
            flash('Failed to add member. Please try again.', 'error')
            
    except Exception as e:
        print(f"Error adding member: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error adding team member. Please try again.', 'error')
        
    return redirect(url_for('dashboard'))

@app.route('/new-project', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description', '')
            capital = request.form.get('capital', 0)
            team_members = request.form.getlist('team_members')  # Get selected team members
            
            # Create project
            project_data = {
                'name': name,
                'description': description,
                'capital': float(capital),
                'created_by': current_user.id
            }
            
            project_result = supabase_db.from_('projects').insert(project_data).execute()
            
            if project_result.data:
                project_id = project_result.data[0]['id']
                
                # Add creator as owner
                member_data = {
                    'project_id': project_id,
                    'user_id': current_user.id,
                    'role': 'owner'  # Changed from 'admin' to 'owner'
                }
                supabase_db.from_('project_users').insert(member_data).execute()
                
                # Add selected team members
                for user_id in team_members:
                    member_data = {
                        'project_id': project_id,
                        'user_id': user_id,
                        'role': 'editor'  # Default role for team members
                    }
                    supabase_db.from_('project_users').insert(member_data).execute()
                
                flash('Project created successfully!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Failed to create project.', 'error')
        except Exception as e:
            flash(f'Error creating project: {str(e)}', 'error')

    # Get teams for the form
    try:
        # Get teams where user is owner
        owned_teams = supabase_db.from_('teams').select('*').eq('created_by', current_user.id).execute()
        print("\nOwned teams:", owned_teams.data)
        
        # Get teams where user is a member
        member_teams = supabase_db.from_('team_members').select('team_id').eq('user_id', current_user.id).execute()
        member_team_ids = [t['team_id'] for t in member_teams.data]
        print("\nMember team IDs:", member_team_ids)
        
        if member_team_ids:
            member_teams_data = supabase_db.from_('teams').select('*').in_('id', member_team_ids).execute()
            teams = owned_teams.data + member_teams_data.data
        else:
            teams = owned_teams.data
            
        print("\nAll teams:", teams)
        
        # Get members for each team
        for team in teams:
            print(f"\nProcessing team {team['name']} ({team['id']})")
            team['members'] = []
            
            # Get owner info first
            owner_result = supabase_db.from_('users').select('id, username, email').eq('id', team['created_by']).execute()
            print("Owner data:", owner_result.data)
            
            if owner_result.data:
                owner = owner_result.data[0]
                team['members'].append({
                    'user_id': owner['id'],
                    'username': owner['username'],
                    'email': owner['email'],
                    'role': 'owner'
                })
                print(f"Added owner: {owner['username']}")
            
            # Get all team members
            members_result = supabase_db.from_('team_members').select('*').eq('team_id', team['id']).execute()
            print(f"Team members: {members_result.data}")
            
            if members_result.data:
                for member in members_result.data:
                    # Get user data separately
                    user_result = supabase_db.from_('users').select('id, username, email').eq('id', member['user_id']).execute()
                    print(f"User data for {member['user_id']}: {user_result.data}")
                    
                    if user_result.data:
                        user = user_result.data[0]
                        # Only add if not already in list (avoid duplicate owner)
                        if not any(m['user_id'] == user['id'] for m in team['members']):
                            team['members'].append({
                                'user_id': user['id'],
                                'username': user['username'],
                                'email': user['email'],
                                'role': member['role']
                            })
                            print(f"Added member: {user['username']}")
            
            print(f"Final team members: {[m['username'] for m in team['members']]}")
    except Exception as e:
        print(f"Error loading teams: {str(e)}")
        teams = []

    return render_template('new_project.html', teams=teams)

@app.route('/project/<project_id>')
@login_required
def view_project(project_id):
    try:
        print(f"\n=== Loading Project {project_id} ===")
        print(f"Current user: {current_user.id}")
        
        # Get project details
        project_result = supabase_db.from_('projects').select('*').eq('id', project_id).single().execute()
        if not project_result.data:
            flash('Project not found.', 'error')
            return redirect(url_for('dashboard'))
            
        project = project_result.data
        
        # Calculate total income and expenses for the project
        income_result = supabase_db.from_('transactions') \
            .select('amount') \
            .eq('project_id', project_id) \
            .eq('type', 'income') \
            .execute()
        
        expense_result = supabase_db.from_('transactions') \
            .select('amount') \
            .eq('project_id', project_id) \
            .eq('type', 'expense') \
            .execute()
        
        # Calculate total balance
        total_income = sum(float(t['amount']) for t in income_result.data) if income_result.data else 0
        total_expenses = sum(float(t['amount']) for t in expense_result.data) if expense_result.data else 0
        total_balance = total_income - total_expenses
        print(f"Project total balance: {total_balance}")
        
        # Get total number of members
        member_count_result = supabase_db.from_('project_users') \
            .select('id') \
            .eq('project_id', project_id) \
            .execute()
        member_count = len(member_count_result.data) if member_count_result.data else 1
        print(f"Project member count: {member_count}")
        
        # Calculate per-member share
        per_member_share = total_balance / member_count if member_count > 0 else 0
        print(f"Per member share: {per_member_share}")
        
        # Calculate current user's contribution/deduction
        user_transactions = supabase_db.from_('transactions') \
            .select('type, amount') \
            .eq('project_id', project_id) \
            .eq('created_by', current_user.id) \
            .execute()
        
        user_total = 0
        if user_transactions.data:
            for t in user_transactions.data:
                if t['type'] == 'income':
                    user_total += float(t['amount'])
                else:  # expense
                    user_total -= float(t['amount'])
        
        # Final initial capital calculation
        initial_capital = per_member_share - user_total
        print(f"User's total transactions: {user_total}")
        print(f"Final initial capital: {initial_capital}")
        
        # Update the project data with the calculated initial capital
        project['initial_capital'] = round(initial_capital, 2)
        
        # Initialize project users list
        project_users = []
        
        # Add owner first
        print("\nFetching owner info...")
        owner_result = supabase_db.from_('users').select('*').eq('id', project['created_by']).execute()
        print(f"Owner query result: {owner_result.data}")
        print("Owner query error:", getattr(owner_result, 'error', None))
        
        if owner_result.data:
            owner = owner_result.data[0]
            project_users.append({
                'user_id': owner['id'],
                'username': owner['username'],
                'email': owner['email'],
                'role': 'owner'
            })
            print(f"Added owner: {owner['username']}")
        else:
            print("Warning: Could not find owner info")
        
        # Get all project members
        print("\nFetching project members...")
        members_result = supabase_db.from_('project_users').select('*').eq('project_id', project_id).execute()
        print(f"Members query result: {members_result.data}")
        print("Members query error:", getattr(members_result, 'error', None))
        
        if members_result.data:
            for member in members_result.data:
                print(f"\nProcessing member: {member}")
                # Get user data separately
                user_result = supabase_db.from_('users').select('id, username, email').eq('id', member['user_id']).execute()
                print(f"User query result: {user_result.data}")
                print("User query error:", getattr(user_result, 'error', None))
                
                if user_result.data and str(user_result.data[0]['id']) != str(project['created_by']):  # Don't duplicate owner
                    user = user_result.data[0]
                    project_users.append({
                        'user_id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'role': member['role']
                    })
                    print(f"Added project member: {user['username']}")
                else:
                    print(f"Warning: Could not find user data for member {member['user_id']}")
        
        print(f"\nFinal project users list: {project_users}")
        
        # Get transactions for the project
        print("\nFetching project transactions...")
        transactions_result = supabase_db.from_('transactions').select('*').eq('project_id', project_id).order('created_at', desc=True).execute()
        print(f"Transactions query result: {transactions_result.data}")
        print("Transactions query error:", getattr(transactions_result, 'error', None))
        
        transactions = []
        total_income = 0
        total_expenses = 0
        
        if transactions_result.data:
            for transaction in transactions_result.data:
                # Get user info
                user_result = supabase_db.from_('users').select('username').eq('id', transaction['created_by']).execute()
                username = user_result.data[0]['username'] if user_result.data else 'Unknown User'
                
                transaction['created_by_username'] = username
                transactions.append(transaction)
                
                amount = float(transaction['amount'])
                if transaction['type'] == 'income':
                    total_income += amount
                else:  # expense
                    total_expenses += amount
        
        print(f"\nProcessed transactions: {transactions}")
        
        # Initialize user totals for all project members
        user_totals = {}
        
        # First add all project members with zero totals
        for user in project_users:
            user_totals[user['user_id']] = {
                'username': user['username'],
                'income': 0,
                'expenses': 0,
                'total': 0
            }
        
        # Add owner if not already in totals
        if project['created_by'] not in user_totals:
            owner_result = supabase_db.from_('users').select('username').eq('id', project['created_by']).execute()
            if owner_result.data:
                user_totals[project['created_by']] = {
                    'username': owner_result.data[0]['username'],
                    'income': 0,
                    'expenses': 0,
                    'total': 0
                }
        
        # Calculate totals from transactions
        if transactions_result.data:
            for transaction in transactions_result.data:
                user_id = transaction['created_by']
                amount = float(transaction['amount'])
                
                if transaction['type'] == 'income':
                    user_totals[user_id]['income'] += amount
                    user_totals[user_id]['total'] += amount
                else:  # expense
                    user_totals[user_id]['expenses'] += amount
                    user_totals[user_id]['total'] -= amount
        
        print(f"\nUser totals: {user_totals}")
        
        return render_template('project.html', 
                            project=project,
                            project_users=project_users,
                            transactions=transactions,
                            user_totals=user_totals,
                            total_income=total_income,
                            total_expenses=total_expenses)
                            
    except Exception as e:
        print(f"Error loading project: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error loading project. Please try again.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/project/<project_id>/transaction', methods=['POST'])
@login_required
def create_transaction(project_id):
    try:
        print(f"\n=== Creating Transaction for Project {project_id} ===")
        print(f"Current User ID: {current_user.id}")
        print(f"Current User Email: {current_user.email}")
        print(f"Current User Username: {current_user.username}")
        print(f"Form Data: {request.form}")
        
        # Get project details
        project_result = supabase_db.from_('projects').select('*').eq('id', project_id).execute()
        print(f"Project result: {project_result.data}")
        
        if not project_result.data:
            print("Project not found")
            flash('Project not found.', 'error')
            return redirect(url_for('dashboard'))
            
        project = project_result.data[0]
        print(f"Project details: {project}")
        
        # Check if user has access to the project
        has_access = False
        
        # 1. Check if user is project owner
        if project['created_by'] == current_user.id:
            has_access = True
            print("User is project owner")
            
        # 2. Check if user is in project_users
        if not has_access:
            try:
                project_user_result = supabase_db.from_('project_users').select('*').eq('project_id', project_id).eq('user_id', current_user.id).execute()
                print(f"Project user result: {project_user_result.data}")
                if project_user_result.data:
                    has_access = True
                    print("User is direct project member")
            except Exception as e:
                print(f"Error checking project_users: {str(e)}")
        
        # 3. Check if user is in the project's team
        if not has_access and project.get('team_id'):
            try:
                print(f"Checking team membership for team {project['team_id']}")
                # Check if user is team owner
                team_result = supabase_db.from_('teams').select('*').eq('id', project['team_id']).execute()
                print(f"Team result: {team_result.data}")
                if team_result.data and team_result.data[0]['created_by'] == current_user.id:
                    has_access = True
                    print("User is team owner")
                
                # Check if user is team member
                if not has_access:
                    team_user_result = supabase_db.from_('team_members').select('*').eq('team_id', project['team_id']).eq('user_id', current_user.id).execute()
                    print(f"Team user result: {team_user_result.data}")
                    if team_user_result.data:
                        has_access = True
                        print("User is team member")
            except Exception as e:
                print(f"Error checking team membership: {str(e)}")
        
        if not has_access:
            print("User does not have access to this project")
            flash('You do not have permission to add transactions to this project.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get form data
        transaction_type = request.form.get('type')
        amount = request.form.get('amount')
        name = request.form.get('name')
        category = request.form.get('category')
        description = request.form.get('description')
        
        print(f"Form values: type={transaction_type}, amount={amount}, name={name}, category={category}, description={description}")
        
        # Validate required fields
        if not all([transaction_type, amount, name, category]):
            print("Missing required fields")
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('view_project', project_id=project_id))
        
        try:
            # Convert amount to float for validation
            amount_float = float(amount)
            if amount_float <= 0:
                print("Invalid amount")
                flash('Amount must be greater than 0.', 'error')
                return redirect(url_for('view_project', project_id=project_id))
        except ValueError:
            print("Invalid amount format")
            flash('Invalid amount format.', 'error')
            return redirect(url_for('view_project', project_id=project_id))
        
        # Create the transaction
        transaction_data = {
            'project_id': project_id,
            'type': transaction_type,
            'amount': str(amount_float),
            'name': name,
            'category': category,
            'description': description or '',
            'created_by': current_user.id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        print(f"Creating transaction with data: {transaction_data}")
        
        # Insert transaction
        try:
            print("\nInserting transaction into database...")
            print(f"Table: transactions")
            print(f"Data: {transaction_data}")
            
            result = supabase_db.from_('transactions').insert(transaction_data).execute()
            print(f"\nTransaction creation response:")
            print(f"Data: {result.data}")
            print(f"Error: {getattr(result, 'error', None)}")
            
            if result.data:
                print("Transaction created successfully")
                flash('Transaction added successfully!', 'success')
                return redirect(url_for('view_project', project_id=project_id))
            else:
                print("No data returned from transaction creation")
                flash('Error creating transaction: No data returned', 'error')
                return redirect(url_for('view_project', project_id=project_id))
            
        except Exception as e:
            print(f"\nError inserting transaction:")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            print(f"Error args: {getattr(e, 'args', [])}")
            
            if hasattr(e, 'response'):
                print(f"Response status: {getattr(e.response, 'status_code', None)}")
                print(f"Response text: {getattr(e.response, 'text', None)}")
            
            flash('Error creating transaction: Database error', 'error')
            return redirect(url_for('view_project', project_id=project_id))
        
    except Exception as e:
        print("\n=== Transaction Creation Error ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Error creating transaction. Please try again.', 'error')
        return redirect(url_for('view_project', project_id=project_id))

@app.route('/project/<project_id>/transaction/<transaction_id>/delete', methods=['POST'])
@login_required
def delete_transaction(project_id, transaction_id):
    try:
        # Verify project exists and user is owner
        project_result = supabase_db.from_('projects').select('*').eq('id', project_id).eq('created_by', current_user.id).execute()
        
        if not project_result.data:
            flash('Project not found.', 'error')
            return redirect(url_for('dashboard'))
            
        # Get transaction before deleting
        transaction_result = supabase_db.from_('transactions').select('*').eq('id', transaction_id).single().execute()
        
        if not transaction_result.data:
            flash('Transaction not found.', 'error')
            return redirect(url_for('view_project', project_id=project_id))
        
        transaction = transaction_result.data
            
        # Record in transaction history
        history_data = {
            'transaction_id': transaction_id,
            'project_id': project_id,
            'type': transaction['type'],
            'amount': transaction['amount'],
            'category': transaction['category'],
            'name': transaction.get('name'),
            'description': transaction.get('description'),
            'created_by': transaction['created_by'],
            'deleted_by': current_user.id,
            'deletion_reason': request.form.get('deletion_reason'),
            'deleted_at': datetime.utcnow().isoformat()
        }
        
        # Save to history and delete transaction
        supabase_db.from_('transaction_history').insert(history_data).execute()
        supabase_db.from_('transactions').delete().eq('id', transaction_id).execute()
        
        flash('Transaction deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting transaction: {str(e)}', 'error')
        
    return redirect(url_for('view_project', project_id=project_id))

@app.route('/project/<project_id>/history')
@login_required
def view_transaction_history(project_id):
    try:
        # Verify project exists and user has access
        project_result = supabase_db.from_('projects').select('*').eq('id', project_id).eq('created_by', current_user.id).single().execute()
        
        if not project_result.data:
            flash('Project not found.', 'error')
            return redirect(url_for('dashboard'))
            
        # Get transaction history with deleted by username
        history_result = supabase_db.from_('transaction_history').select(
            'id, transaction_id, project_id, type, amount, category, name, description, created_by, deleted_by, deletion_reason, deleted_at'
        ).eq('project_id', project_id).order('deleted_at', desc=True).execute()
        
        # Get usernames for deleted_by users
        if history_result.data:
            deleted_by_ids = [item['deleted_by'] for item in history_result.data if item['deleted_by']]
            users_result = supabase_db.from_('users').select('id, username').in_('id', deleted_by_ids).execute()
            users_map = {user['id']: user['username'] for user in users_result.data} if users_result.data else {}
            
            # Add username to history items
            for item in history_result.data:
                item['deleted_by_username'] = users_map.get(item['deleted_by'], 'Unknown')
        
        history = history_result.data if history_result.data else []
        
        return render_template('transaction_history.html',
                             project=project_result.data,
                             history=history)
                             
    except Exception as e:
        flash(f'Error loading transaction history: {str(e)}', 'error')
        return redirect(url_for('view_project', project_id=project_id))

@app.route('/project/<project_id>/user', methods=['POST'])
@login_required
def add_project_user(project_id):
    try:
        print(f"Adding user to project {project_id}")
        
        # Verify project exists and user is owner
        project_result = supabase_db.from_('projects').select('*').eq('id', project_id).eq('created_by', current_user.id).execute()
        print(f"Project result: {project_result.data}")
        
        if not project_result.data:
            flash('Project not found or you do not have permission.', 'error')
            return redirect(url_for('dashboard'))
            
        # Get user by email
        email = request.form.get('email')
        if not email:
            flash('Email is required.', 'error')
            return redirect(url_for('view_project', project_id=project_id))
            
        print(f"Looking up user with email: {email}")
        user_result = supabase_db.from_('users').select('*').eq('email', email).execute()
        print(f"User result: {user_result.data}")
        
        if not user_result.data:
            flash('User not found. Make sure the user has registered.', 'error')
            return redirect(url_for('view_project', project_id=project_id))
            
        user_to_add = user_result.data[0]
        
        # Check if user is already in project
        existing_member = supabase_db.from_('project_users').select('*').eq('project_id', project_id).eq('user_id', user_to_add['id']).execute()
        print(f"Existing member check: {existing_member.data}")
        
        if existing_member.data:
            flash(f'User {email} is already a member of this project.', 'warning')
            return redirect(url_for('view_project', project_id=project_id))
            
        # Add user to project
        role = request.form.get('role', 'viewer')  # Default to viewer if role not specified
        project_user_data = {
            'project_id': project_id,
            'user_id': user_to_add['id'],
            'role': role
        }
        
        print(f"Adding user with data: {project_user_data}")
        result = supabase_db.from_('project_users').insert(project_user_data).execute()
        print(f"Insert result: {result.data}")
        
        flash(f'User {email} added to project successfully!', 'success')
        
    except Exception as e:
        import traceback
        print(f"Error adding user: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        flash('Error adding user to project. Please try again.', 'error')
        
    return redirect(url_for('view_project', project_id=project_id))

@app.route('/project/<project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    try:
        # Verify project exists and user is owner
        project_result = supabase_db.from_('projects').select('*').eq('id', project_id).eq('created_by', current_user.id).execute()
        
        if not project_result.data:
            flash('Project not found or you do not have permission to delete it.', 'error')
            return redirect(url_for('dashboard'))
            
        # Delete project (cascade will handle related records)
        supabase_db.from_('projects').delete().eq('id', project_id).execute()
        
        flash('Project deleted successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        print(f"Error deleting project: {str(e)}")
        flash('Error deleting project. Please try again.', 'error')
        return redirect(url_for('view_project', project_id=project_id))

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/api/user/profile')
@login_required
def get_user_profile():
    try:
        user_data = supabase_db.from_('users').select('*').eq('id', current_user.id).single().execute()
        return jsonify(user_data.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')
