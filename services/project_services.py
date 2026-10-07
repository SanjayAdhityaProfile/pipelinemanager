from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from models import projects
import logging
from models import engine

# Set up a logger
logger = logging.getLogger(__name__)

# Function to get all projects


def get_all_projects():
    try:
        with engine.connect() as connection:
            result = connection.execute(select(projects))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all projects: {e}")
        return None

# Function to get a project by ID


def get_project_by_id(project_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(projects).where(projects.c.id == project_id))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching project by ID {project_id}: {e}")
        return None

# Function to get a cluster by NAME


def get_project_by_name(project_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(projects).where(projects.c.name == project_name))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching branch by ID {project_name}: {e}")
        return None

# Function to add multiple projects


def add_multiple_projects(project_list):
    try:
        with engine.connect() as connection:
            insert_stmt = projects.insert().values(project_list)
            connection.execute(insert_stmt)
            return {"status": "success", "message": "Projects added successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error adding multiple projects: {e}")
        return {"status": "error", "message": f"Error adding projects: {e}"}

# Function to delete a project by ID


def delete_project_by_id(project_id):
    try:
        with engine.connect() as connection:
            delete_stmt = projects.delete().where(projects.c.id == project_id)
            connection.execute(delete_stmt)
            return {"status": "success", "message": "Project deleted successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting project by ID {project_id}: {e}")
        return {"status": "error", "message": f"Error deleting project: {e}"}

# Function to update a project by ID


def update_project_by_id(project_id, name=None, description=None):
    try:
        with engine.connect() as connection:
            update_stmt = update(projects).where(projects.c.id == project_id)
            if name:
                update_stmt = update_stmt.values(name=name)
            if description:
                update_stmt = update_stmt.values(description=description)
            connection.execute(update_stmt)
            return {"status": "success", "message": "Project updated successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error updating project by ID {project_id}: {e}")
        return {"status": "error", "message": f"Error updating project: {e}"}
