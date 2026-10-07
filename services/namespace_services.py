from sqlalchemy import select, update, insert, func
from sqlalchemy.exc import SQLAlchemyError
from models import namespaces,user_namespace_subscriptions,users, engine
import logging

# Set up a logger
logger = logging.getLogger(__name__)

# Function to get all namespaces

def get_all_namespaces():
    try:
        with engine.connect() as connection:
            result = connection.execute(select(namespaces))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all namespaces: {e}")
        return None

def get_all_namespaces_user(username):
    try:
        user_id = get_user_id_by_username(username)
        namespace_ids = get_all_namespace_ids_for_user(user_id)
        namespaces = []
        for i in namespace_ids:
            data = get_namespace_by_id(i)
            namespaces.append({"id":data[0], "name": data[1]})
        return namespaces

    except SQLAlchemyError as e:
        logger.error(f"Error fetching all namespaces: {e}")
        return None

# Function to get user_id from username
def get_user_id_by_username(username):
    try:
        with engine.connect() as connection:
            query = select(users.c.id).where(users.c.username == username)
            result = connection.execute(query).scalar()
            return result  # Returns None if the user does not exist
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user ID for username '{username}': {e}")
        return None

# Function to get all namespace IDs for a given user_id
def get_all_namespace_ids_for_user(user_id):
    try:
        with engine.connect() as connection:
            query = select(user_namespace_subscriptions.c.namespace_id).where(
                user_namespace_subscriptions.c.user_id == user_id
            )
            result = connection.execute(query)
            result = [int(row[0]) for row in result.fetchall()]
            return result


    except SQLAlchemyError as e:    
        logger.error(f"Error fetching namespaces for user {user_id}: {e}")
        return None

def add_user_subscription(user_id, namespace_id):
    try:
        with engine.connect() as connection:
            query = insert(user_namespace_subscriptions).values(
                user_id=user_id,
                namespace_id=namespace_id,
                subscription_date=func.getdate()
            )
            connection.execute(query)
            connection.commit()
            return f"User {user_id} subscribed to namespace {namespace_id} successfully."
    except SQLAlchemyError as e:
        logger.error(f"Error subscribing user {user_id} to namespace {namespace_id}: {e}")
        return None


def get_all_user_namespace_subscriptions():
    """
    Get all user-namespace subscriptions.
    
    Returns:
        List of all subscription records
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(select(user_namespace_subscriptions))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all user-namespace subscriptions: {e}")
        return None


# Function to get a namespace by ID
def get_namespace_by_id(namespace_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(namespaces).where(namespaces.c.id == namespace_id))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching namespace by ID {namespace_id}: {e}")
        return None

# Function to get a namespace by name (assuming name is unique)


def get_namespace_by_name(namespace_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(namespaces).where(
                namespaces.c.name == namespace_name))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching namespace by name {namespace_name}: {e}")
        return None

# Function to add multiple namespaces


def add_multiple_namespaces(namespace_list):
    try:
        with engine.connect() as connection:
            insert_stmt = namespaces.insert().values(namespace_list)
            connection.execute(insert_stmt)
            return {"status": "success", "message": "Namespaces added successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error adding multiple namespaces: {e}")
        return {"status": "error", "message": f"Error adding namespaces: {e}"}

# Function to delete a namespace by ID


def delete_namespace_by_id(namespace_id):
    try:
        with engine.connect() as connection:
            delete_stmt = namespaces.delete().where(namespaces.c.id == namespace_id)
            connection.execute(delete_stmt)
            connection.commit()
            return {"status": "success", "message": "Namespace deleted successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting namespace by ID {namespace_id}: {e}")
        return {"status": "error", "message": f"Error deleting namespace: {e}"}

# Function to update a namespace by ID


def update_namespace_by_id(namespace_id, name=None, cluster_id=None, branch_id=None):
    try:
        with engine.connect() as connection:
            update_stmt = update(namespaces).where(
                namespaces.c.id == namespace_id)
            if name:
                update_stmt = update_stmt.values(name=name)
            if cluster_id:
                update_stmt = update_stmt.values(cluster_id=cluster_id)
            if branch_id:
                update_stmt = update_stmt.values(branch_id=branch_id)
            connection.execute(update_stmt)
            return {"status": "success", "message": "Namespace updated successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error updating namespace by ID {namespace_id}: {e}")
        return {"status": "error", "message": f"Error updating namespace: {e}"}

# Function to get all namespaces by cluster ID


def get_all_namespaces_by_cluster_id(cluster_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(namespaces).where(
                namespaces.c.cluster_id == cluster_id))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(
            f"Error fetching namespaces for cluster ID {cluster_id}: {e}")
        return None

# Function to get all namespaces by branch ID


def get_all_namespaces_by_branch_id(branch_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(select(namespaces).where(
                namespaces.c.branch_id == branch_id))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(
            f"Error fetching namespaces for branch ID {branch_id}: {e}")
        return None
