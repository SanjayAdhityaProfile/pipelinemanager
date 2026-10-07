from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from models import branches, engine
import logging

# Set up a logger
logger = logging.getLogger(__name__)

# Function to get all branches


def get_all_branches():
    try:
        with engine.connect() as connection:
            result = connection.execute(select(branches))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all branches: {e}")
        return None

# Function to get a branch by ID


def get_branch_by_id(branch_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(branches).where(branches.c.id == branch_id))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching branch by ID {branch_id}: {e}")
        return None

# Function to get a branch by NAME


def get_branch_by_name(branch_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(branches).where(branches.c.name == branch_name))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching branch by ID {branch_name}: {e}")
        return None

# Function to add multiple branches


def add_multiple_branches(branch_list):
    try:
        with engine.connect() as connection:
            insert_stmt = branches.insert().values(branch_list)
            connection.execute(insert_stmt)
            return {"status": "success", "message": "Branches added successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error adding multiple branches: {e}")
        return {"status": "error", "message": f"Error adding branches: {e}"}

# Function to delete a branch by ID


def delete_branch_by_id(branch_id):
    try:
        with engine.connect() as connection:
            delete_stmt = branches.delete().where(branches.c.id == branch_id)
            connection.execute(delete_stmt)
            return {"status": "success", "message": "Branch deleted successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting branch by ID {branch_id}: {e}")
        return {"status": "error", "message": f"Error deleting branch: {e}"}

# Function to update a branch by ID


def update_branch_by_id(branch_id, name=None, repository_id=None):
    try:
        with engine.connect() as connection:
            update_stmt = update(branches).where(branches.c.id == branch_id)
            if name:
                update_stmt = update_stmt.values(name=name)
            if repository_id:
                update_stmt = update_stmt.values(repository_id=repository_id)
            connection.execute(update_stmt)
            return {"status": "success", "message": "Branch updated successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error updating branch by ID {branch_id}: {e}")
        return {"status": "error", "message": f"Error updating branch: {e}"}

# Function to get all branches by repository ID


def get_branches_by_repository_id(repository_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(branches).where(
                branches.c.repository_id == repository_id))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(
            f"Error fetching branches by repository ID {repository_id}: {e}")
        return None
