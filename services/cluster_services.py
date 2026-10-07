from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from models import clusters
import logging
from models import engine

# Set up a logger
logger = logging.getLogger(__name__)

# Function to get all clusters


def get_all_clusters():
    try:
        with engine.connect() as connection:
            result = connection.execute(select(clusters))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all clusters: {e}")
        return None

# Function to get a cluster by ID


def get_cluster_by_id(cluster_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(clusters).where(clusters.c.id == cluster_id))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching cluster by ID {cluster_id}: {e}")
        return None

# Function to get a cluster by NAME


def get_cluster_by_name(cluster_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(clusters).where(clusters.c.name == cluster_name))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching branch by ID {cluster_name}: {e}")
        return None


# Function to add multiple clusters
def add_multiple_clusters(cluster_list):
    try:
        with engine.connect() as connection:
            insert_stmt = clusters.insert().values(cluster_list)
            connection.execute(insert_stmt)
            return {"status": "success", "message": "Clusters added successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error adding multiple clusters: {e}")
        return {"status": "error", "message": f"Error adding clusters: {e}"}

# Function to delete a cluster by ID


def delete_cluster_by_id(cluster_id):
    try:
        with engine.connect() as connection:
            delete_stmt = clusters.delete().where(clusters.c.id == cluster_id)
            connection.execute(delete_stmt)
            return {"status": "success", "message": "Cluster deleted successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting cluster by ID {cluster_id}: {e}")
        return {"status": "error", "message": f"Error deleting cluster: {e}"}

# Function to update a cluster by ID


def update_cluster_by_id(cluster_id, name=None, description=None):
    try:
        with engine.connect() as connection:
            update_stmt = update(clusters).where(clusters.c.id == cluster_id)
            if name:
                update_stmt = update_stmt.values(name=name)
            if description:
                update_stmt = update_stmt.values(description=description)
            connection.execute(update_stmt)
            return {"status": "success", "message": "Cluster updated successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error updating cluster by ID {cluster_id}: {e}")
        return {"status": "error", "message": f"Error updating cluster: {e}"}
