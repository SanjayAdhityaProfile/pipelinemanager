from sqlalchemy.sql import select
from models import namespaces, engine

from models import *


def get_cluster_and_namespace(project_name: str, repo_name: str, branch_name: str):
    """
    Get the cluster and namespace associated with a given project, repository, and branch.

    Args:
        engine (Engine): SQLAlchemy engine instance for database connection.
        project_name (str): Name of the project.
        repo_name (str): Name of the repository.
        branch_name (str): Name of the branch.

    Returns:
        list[dict]: A list of dictionaries containing cluster and namespace details.
    """
    # Define the query
    query = (
        select(
            clusters.c.name.label("cluster_name"),
            namespaces.c.name.label("namespace_name"),
            namespaces.c.registry.label("registry"),
            projects.c.name.label("project_name"),
            repositories.c.name.label("repository_name"),
            deployments.c.application_name.label("deployment_name"),
            branches.c.name.label("branch_name"),
        )
        .select_from(projects)
        .join(repositories, repositories.c.project_id == projects.c.id)
        .join(branches, branches.c.repository_id == repositories.c.id)
        .join(namespaces, namespaces.c.id == branches.c.namespace_id)
        .join(clusters, clusters.c.id == namespaces.c.cluster_id)
        .join(deployments, deployments.c.id == repositories.c.deployment_id)
        .where(projects.c.name == project_name)
        .where(repositories.c.name == repo_name)
        .where(branches.c.name == branch_name)
    )

    try:
        # Execute the query
        with engine.connect() as connection:
            result = connection.execute(query)
            # Parse and return the results
            return [
                {
                    "cluster_name": row.cluster_name,
                    "namespace_name": row.namespace_name,
                    "project_name": row.project_name,
                    "registry_name": row.registry,
                    "repository_name": row.repository_name,
                    "deployment_name": row.deployment_name,
                    "branch_name": row.branch_name,
                }
                for row in result
            ]
    except Exception as e:
        raise RuntimeError(f"Failed to execute query: {e}")


def get_deployment_by_project_repo_branch(project_name, repo_name, branch_name):
    """
    Get deployment names associated with a given project, repository, and branch.

    Args:
        engine (Engine): SQLAlchemy engine instance for database connection.
        project_name (str): Name of the project.
        repo_name (str): Name of the repository.
        branch_name (str): Name of the branch.

    Returns:
        list[dict]: A list of dictionaries containing deployment details.
    """

    # Define the query
    query = (
        select(
            # deployments.c.application_name.label("deployment_name"),
            namespaces.c.name.label("namespace_name"),
            projects.c.name.label("project_name"),
            repositories.c.name.label("repository_name"),
            branches.c.name.label("branch_name"),
        )
        .select_from(projects)
        .join(repositories, repositories.c.project_id == projects.c.id)
        .join(branches, branches.c.repository_id == repositories.c.id)
        .join(namespaces, namespaces.c.id == branches.c.namespace_id)
        .join(deployments, deployments.c.namespace_id == namespaces.c.id)
        .where(projects.c.name == project_name)
        .where(repositories.c.name == repo_name)
        .where(branches.c.name == branch_name)
    )

    try:
        # Execute the query
        with engine.connect() as connection:
            result = connection.execute(query)
            # Parse and return the results
            return [
                {
                    "deployment_name": row.deployment_name,
                    "namespace_name": row.namespace_name,
                    "project_name": row.project_name,
                    "repository_name": row.repository_name,
                    "branch_name": row.branch_name,
                }
                for row in result
            ]
    except Exception as e:
        raise RuntimeError(f"Failed to execute query: {e}")
