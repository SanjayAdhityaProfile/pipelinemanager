from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from models import repositories, engine, deployments, namespaces
import logging

# Set up a logger
logger = logging.getLogger(__name__)

# Function to get all repositories


def get_all_repositories():
    try:
        with engine.connect() as connection:
            result = connection.execute(select(repositories))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all repositories: {e}")
        return None

# Function to get a repository by ID


def get_repository_by_id(repository_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(repositories).where(
                repositories.c.id == repository_id))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching repository by ID {repository_id}: {e}")
        return None

# Function to get a cluster by NAME


def get_repository_by_name(repository_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(repositories).where(
                repositories.c.name == repository_name))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching branch by ID {repository_name}: {e}")
        return None

# Function to get a cluster by NAME


def get_repository_by_deploymentname(deployment_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(deployments).where(
                deployments.c.application_name == deployment_name[0].application_name))
            result = result.fetchone()
            namespace_result = connection.execute(
                select(namespaces).where(namespaces.c.id == result[1]))
            namespace_result = namespace_result.fetchone()
            data = {
                "registry_name": namespace_result[5], "namespace": namespace_result[1]}
            return data
    except SQLAlchemyError as e:
        logger.error(f"Error fetching branch by ID {deployment_name}: {e}")
        return None

# Function to add multiple repositories


def add_multiple_repositories(repository_list):
    try:
        with engine.connect() as connection:
            insert_stmt = repositories.insert().values(repository_list)
            connection.execute(insert_stmt)
            return {"status": "success", "message": "Repositories added successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error adding multiple repositories: {e}")
        return {"status": "error", "message": f"Error adding repositories: {e}"}

# Function to delete a repository by ID


def delete_repository_by_id(repository_id):
    try:
        with engine.connect() as connection:
            delete_stmt = repositories.delete().where(repositories.c.id == repository_id)
            connection.execute(delete_stmt)
            return {"status": "success", "message": "Repository deleted successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting repository by ID {repository_id}: {e}")
        return {"status": "error", "message": f"Error deleting repository: {e}"}

# Function to update a repository by ID


def update_repository_by_id(repository_id, url=None, project_id=None):
    try:
        with engine.connect() as connection:
            update_stmt = update(repositories).where(
                repositories.c.id == repository_id)
            if url:
                update_stmt = update_stmt.values(url=url)
            if project_id:
                update_stmt = update_stmt.values(project_id=project_id)
            connection.execute(update_stmt)
            return {"status": "success", "message": "Repository updated successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error updating repository by ID {repository_id}: {e}")
        return {"status": "error", "message": f"Error updating repository: {e}"}

# Function to get all repositories by project ID


def get_repositories_by_project_id(project_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(repositories).where(
                repositories.c.project_id == project_id))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(
            f"Error fetching repositories by project ID {project_id}: {e}")
        return None
