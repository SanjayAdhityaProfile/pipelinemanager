from sqlalchemy import select, update, insert, delete
from sqlalchemy.exc import SQLAlchemyError
from models import pipelines, engine
import logging

# Set up a logger
logger = logging.getLogger(__name__)

# Function to get all pipelines


def get_all_pipelines():
    try:
        with engine.connect() as connection:
            result = connection.execute(select(pipelines))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all pipelines: {e}")
        return None

# Function to get a pipeline by ID


def get_pipeline_by_id(pipeline_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(pipelines).where(pipelines.c.id == pipeline_id))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching pipeline by ID {pipeline_id}: {e}")
        return None

# Function to get a pipeline by name


def get_pipeline_by_name(name):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(pipelines).where(pipelines.c.name == name))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching pipeline by name {name}: {e}")
        return None

# Function to get all pipelines by project ID


def get_pipelines_by_project_id(project_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(pipelines).where(
                pipelines.c.project_id == project_id))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(
            f"Error fetching pipelines by project ID {project_id}: {e}")
        return None

# Function to add multiple pipelines


def add_multiple_pipelines(pipeline_list):
    try:
        with engine.connect() as connection:
            insert_stmt = pipelines.insert().values(pipeline_list)
            connection.execute(insert_stmt)
            return {"status": "success", "message": "Pipelines added successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error adding multiple pipelines: {e}")
        return {"status": "error", "message": f"Error adding pipelines: {e}"}

# Function to delete a pipeline by ID


def delete_pipeline_by_id(pipeline_id):
    try:
        with engine.connect() as connection:
            delete_stmt = pipelines.delete().where(pipelines.c.id == pipeline_id)
            connection.execute(delete_stmt)
            return {"status": "success", "message": "Pipeline deleted successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting pipeline by ID {pipeline_id}: {e}")
        return {"status": "error", "message": f"Error deleting pipeline: {e}"}

# Function to update a pipeline by ID


def update_pipeline_by_id(pipeline_id, name=None, status=None, trigger_event=None):
    try:
        with engine.connect() as connection:
            update_stmt = update(pipelines).where(
                pipelines.c.id == pipeline_id)
            if name:
                update_stmt = update_stmt.values(name=name)
            if status:
                update_stmt = update_stmt.values(status=status)
            if trigger_event:
                update_stmt = update_stmt.values(trigger_event=trigger_event)
            connection.execute(update_stmt)
            return {"status": "success", "message": "Pipeline updated successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error updating pipeline by ID {pipeline_id}: {e}")
        return {"status": "error", "message": f"Error updating pipeline: {e}"}
