from sqlalchemy import select, insert, update
from models import git

def get_repos_by_namespace(conn, namespace_id: int):
    """
    Retrieve all services for a specific deployment within a specific namespace.

    Args:
        conn: Database connection.
        namespace_id: The ID of the namespace to fetch the services for.
        deployment_id: The ID of the deployment to fetch the services for.

    Returns:
        A list of services for the specified deployment and namespace.
    """
    try:
        git_stmt = select(git).where(
            (git.c.namespace_id == namespace_id)
        )
        git_list = conn.execute(git_stmt).fetchall()
        
        if not git_list:
            return {"error": "Git does not exist in the specified namespace."}

    except Exception as e:
        return {"error": str(e)}