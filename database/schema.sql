-- Drop existing tables if they exist
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS project_users CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS transaction_history CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS team_members CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS for users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Insert existing auth users into users table
INSERT INTO users (id, email, username)
SELECT 
    id,
    email,
    COALESCE(raw_user_meta_data->>'username', split_part(email, '@', 1)) as username
FROM auth.users
ON CONFLICT (id) DO UPDATE 
SET 
    email = EXCLUDED.email,
    username = EXCLUDED.username;

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    capital DECIMAL(10,2) DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_by UUID REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS for projects table
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Create project_users table
CREATE TABLE IF NOT EXISTS project_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(project_id, user_id)
);

-- Enable RLS for project_users table
ALTER TABLE project_users ENABLE ROW LEVEL SECURITY;

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(255) NOT NULL CHECK (type IN ('income', 'expense')),
    amount DECIMAL(10,2) NOT NULL,
    category VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes
CREATE INDEX IF NOT EXISTS transactions_project_id_idx ON transactions(project_id);
CREATE INDEX IF NOT EXISTS transactions_created_by_idx ON transactions(created_by);

-- Enable RLS for transactions table
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Create transaction_history table
CREATE TABLE IF NOT EXISTS transaction_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id UUID NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    amount DECIMAL(10,2) NOT NULL,
    category TEXT NOT NULL,
    name TEXT,
    description TEXT,
    created_by UUID REFERENCES users(id),
    deleted_by UUID REFERENCES users(id),
    deletion_reason TEXT,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Enable RLS for transaction_history table
ALTER TABLE transaction_history ENABLE ROW LEVEL SECURITY;

-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    UNIQUE(name, type)
);

-- Enable RLS for categories table
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

-- Insert default categories
INSERT INTO categories (name, type) 
VALUES 
    ('Salary', 'income'),
    ('Freelance', 'income'),
    ('Investment', 'income'),
    ('Other Income', 'income'),
    ('Rent', 'expense'),
    ('Utilities', 'expense'),
    ('Groceries', 'expense'),
    ('Transportation', 'expense'),
    ('Entertainment', 'expense'),
    ('Healthcare', 'expense'),
    ('Education', 'expense'),
    ('Shopping', 'expense'),
    ('Other Expenses', 'expense')
ON CONFLICT DO NOTHING;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);
CREATE INDEX IF NOT EXISTS idx_transactions_project_id ON transactions(project_id);
CREATE INDEX IF NOT EXISTS idx_project_users_project_id ON project_users(project_id);
CREATE INDEX IF NOT EXISTS idx_project_users_user_id ON project_users(user_id);
CREATE INDEX IF NOT EXISTS idx_transaction_history_project_id ON transaction_history(project_id);
CREATE INDEX IF NOT EXISTS idx_transaction_history_deleted_by ON transaction_history(deleted_by);

-- Create teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create team_members table
CREATE TABLE IF NOT EXISTS team_members (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'member')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    UNIQUE(team_id, user_id)
);

-- Enable RLS for team_members table
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

-- Policy for users to view their own data and data of users in their teams
DROP POLICY IF EXISTS "Users can view their own data and team members" ON users;
CREATE POLICY "Users can view their own data and team members"
    ON users FOR SELECT
    USING (
        auth.uid() = id OR  -- Can view their own data
        EXISTS (  -- Can view data of users in the same team
            SELECT 1 FROM team_members tm1
            JOIN team_members tm2 ON tm1.team_id = tm2.team_id
            WHERE tm1.user_id = auth.uid()
            AND tm2.user_id = users.id
        ) OR
        EXISTS (  -- Can view data of users in teams they own
            SELECT 1 FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            WHERE t.created_by = auth.uid()
            AND tm.user_id = users.id
        )
    );

-- Team policies
DROP POLICY IF EXISTS "Team owners can manage their teams" ON teams;
CREATE POLICY "Team owners can manage their teams"
ON teams
FOR ALL
USING (
    auth.uid() = created_by
);

DROP POLICY IF EXISTS "Team members can view their teams" ON teams;
CREATE POLICY "Team members can view their teams"
ON teams
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM team_members
        WHERE team_members.team_id = teams.id
        AND team_members.user_id = auth.uid()
    )
);

-- Team members policies
DROP POLICY IF EXISTS "Team owners can manage team members" ON team_members;
CREATE POLICY "Team owners can manage team members"
ON team_members
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM teams
        WHERE teams.id = team_members.team_id
        AND teams.created_by = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can view team members of their teams" ON team_members;
CREATE POLICY "Users can view team members of their teams"
ON team_members
FOR SELECT
USING (
    -- Can view members of teams you own
    EXISTS (
        SELECT 1
        FROM teams
        WHERE teams.id = team_members.team_id
        AND teams.created_by = auth.uid()
    )
    -- Can view members of teams you're in
    OR EXISTS (
        SELECT 1
        FROM team_members my_membership
        WHERE my_membership.team_id = team_members.team_id
        AND my_membership.user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can view their own team memberships" ON team_members;
CREATE POLICY "Users can view their own team memberships"
ON team_members
FOR SELECT
USING (
    user_id = auth.uid()
);

-- Users table policies
DROP POLICY IF EXISTS "Users can view their own user data" ON users;
DROP POLICY IF EXISTS "Users can view project member data" ON users;
DROP POLICY IF EXISTS "Users can view team member data" ON users;

CREATE POLICY "Users can view their own user data"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can view project member data"
    ON users FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM project_users pu
            WHERE pu.user_id = users.id
            AND (
                pu.user_id = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM project_users pu2
                    WHERE pu2.project_id = pu.project_id
                    AND pu2.user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY "Users can view team member data"
    ON users FOR SELECT
    USING (
        -- Can view if the user is in the same team as you
        EXISTS (
            SELECT 1 FROM team_members tm
            WHERE tm.user_id = users.id
            AND EXISTS (
                SELECT 1 FROM team_members tm2
                WHERE tm2.team_id = tm.team_id
                AND tm2.user_id = auth.uid()
            )
        )
        -- Can view if you own the team they're in
        OR EXISTS (
            SELECT 1 FROM team_members tm
            JOIN teams t ON t.id = tm.team_id
            WHERE tm.user_id = users.id
            AND t.created_by = auth.uid()
        )
        -- Can view team owners of teams you're in
        OR EXISTS (
            SELECT 1 FROM teams t
            JOIN team_members tm ON tm.team_id = t.id
            WHERE t.created_by = users.id
            AND tm.user_id = auth.uid()
        )
    );

-- Projects table policies
DROP POLICY IF EXISTS "Users can view projects they have access to" ON projects;
DROP POLICY IF EXISTS "Users can create projects" ON projects;
DROP POLICY IF EXISTS "Project owners can update their projects" ON projects;

CREATE POLICY "Users can view projects they have access to"
    ON projects FOR SELECT
    USING (
        auth.uid() = projects.created_by OR
        EXISTS (
            SELECT 1 FROM project_users
            WHERE project_users.project_id = projects.id
            AND project_users.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create projects"
    ON projects FOR INSERT
    WITH CHECK (auth.uid() = projects.created_by);

CREATE POLICY "Project owners can update their projects"
    ON projects FOR UPDATE
    USING (auth.uid() = projects.created_by);

-- Project users table policies
DROP POLICY IF EXISTS "Users can view project users" ON project_users;
DROP POLICY IF EXISTS "Project owners can manage project users" ON project_users;

CREATE POLICY "Users can view project users"
    ON project_users FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_users.project_id
            AND (
                p.created_by = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM project_users pu
                    WHERE pu.project_id = p.id
                    AND pu.user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY "Project owners can manage project users"
    ON project_users FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_users.project_id
            AND p.created_by = auth.uid()
        )
    );

-- Transactions table policies
DROP POLICY IF EXISTS "Users can view transactions" ON transactions;
DROP POLICY IF EXISTS "Users can create transactions" ON transactions;
DROP POLICY IF EXISTS "Users can update transactions" ON transactions;
DROP POLICY IF EXISTS "Users can delete transactions" ON transactions;

CREATE POLICY "Users can view transactions"
    ON transactions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = transactions.project_id
            AND (
                p.created_by = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM project_users pu
                    WHERE pu.project_id = p.id
                    AND pu.user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY "Users can create transactions"
    ON transactions FOR INSERT
    WITH CHECK (
        auth.uid() = created_by
        AND EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
            AND (
                p.created_by = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM project_users pu
                    WHERE pu.project_id = p.id
                    AND pu.user_id = auth.uid()
                    AND pu.role IN ('owner', 'editor')
                )
            )
        )
    );

CREATE POLICY "Users can update transactions"
    ON transactions FOR UPDATE
    USING (
        auth.uid() = created_by
        AND EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
            AND (
                p.created_by = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM project_users pu
                    WHERE pu.project_id = p.id
                    AND pu.user_id = auth.uid()
                    AND pu.role IN ('owner', 'editor')
                )
            )
        )
    );

CREATE POLICY "Users can delete transactions"
    ON transactions FOR DELETE
    USING (
        auth.uid() = created_by
        AND EXISTS (
            SELECT 1 FROM projects p
            WHERE p.id = project_id
            AND (
                p.created_by = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM project_users pu
                    WHERE pu.project_id = p.id
                    AND pu.user_id = auth.uid()
                    AND pu.role IN ('owner', 'editor')
                )
            )
        )
    );

-- Transaction history table policies
CREATE POLICY "Users can view transaction history for their projects"
    ON transaction_history FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = transaction_history.project_id
            AND (
                projects.created_by = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM project_users
                    WHERE project_users.project_id = transaction_history.project_id
                    AND project_users.user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY "Users can create transaction history"
    ON transaction_history FOR INSERT
    WITH CHECK (auth.uid() = transaction_history.deleted_by);

-- Teams table policies
DROP POLICY IF EXISTS "Users can create teams" ON teams;
DROP POLICY IF EXISTS "Users can view their teams" ON teams;
DROP POLICY IF EXISTS "Users can update their teams" ON teams;
DROP POLICY IF EXISTS "Users can delete their teams" ON teams;

CREATE POLICY "Users can create teams"
    ON teams FOR INSERT
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can view their teams"
    ON teams FOR SELECT
    USING (
        auth.uid() = created_by
        OR EXISTS (
            SELECT 1 FROM team_members
            WHERE team_members.team_id = teams.id
            AND team_members.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their teams"
    ON teams FOR UPDATE
    USING (auth.uid() = created_by)
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can delete their teams"
    ON teams FOR DELETE
    USING (auth.uid() = created_by);

-- Team members table policies
DROP POLICY IF EXISTS "Users can add team members" ON team_members;
DROP POLICY IF EXISTS "Users can view team members" ON team_members;
DROP POLICY IF EXISTS "Users can update team members" ON team_members;
DROP POLICY IF EXISTS "Users can delete team members" ON team_members;

CREATE POLICY "Users can add team members"
    ON team_members FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM teams
            WHERE teams.id = team_members.team_id
            AND teams.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can view team members"
    ON team_members FOR SELECT
    USING (
        auth.uid() = user_id
        OR EXISTS (
            SELECT 1 FROM teams
            WHERE teams.id = team_members.team_id
            AND (
                teams.created_by = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM team_members tm2
                    WHERE tm2.team_id = team_members.team_id
                    AND tm2.user_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY "Users can update team members"
    ON team_members FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM teams
            WHERE teams.id = team_members.team_id
            AND teams.created_by = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM teams
            WHERE teams.id = team_members.team_id
            AND teams.created_by = auth.uid()
        )
    );

CREATE POLICY "Users can delete team members"
    ON team_members FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM teams
            WHERE teams.id = team_members.team_id
            AND teams.created_by = auth.uid()
        )
    );

-- Categories table policies
CREATE POLICY "Everyone can view categories"
    ON categories FOR SELECT
    USING (true);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_teams_created_by ON teams(created_by);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
