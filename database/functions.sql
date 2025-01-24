-- Function to get project users with RLS
CREATE OR REPLACE FUNCTION get_project_users(project_id_param UUID)
RETURNS TABLE (
    user_id UUID,
    role TEXT
) SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pu.user_id,
        pu.role
    FROM project_users pu
    WHERE pu.project_id = project_id_param
    AND EXISTS (
        SELECT 1 FROM projects p
        WHERE p.id = project_id_param
        AND (
            p.created_by = auth.uid() OR
            EXISTS (
                SELECT 1 FROM project_users inner_pu
                WHERE inner_pu.project_id = project_id_param
                AND inner_pu.user_id = auth.uid()
            )
        )
    );
END;
$$ LANGUAGE plpgsql;
