from sqlalchemy import select, update, insert, delete
from sqlalchemy.exc import SQLAlchemyError
from models import users, engine
import logging

# Set up a logger
logger = logging.getLogger(__name__)

# Function to get all users


def get_all_users():
    try:
        with engine.connect() as connection:
            result = connection.execute(select(users))
            return result.fetchall()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all users: {e}")
        return None

# Function to get a user by ID


def get_user_by_id(user_id):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(users).where(users.c.id == user_id))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by ID {user_id}: {e}")
        return None

# Function to get a user by username (assuming username is unique)


def get_user_by_username(username):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                select(users).where(users.c.username == username))
            return result.fetchone()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by username {username}: {e}")
        return None

# Function to add multiple users


def add_multiple_users(user_list):
    try:
        with engine.connect() as connection:
            insert_stmt = users.insert().values(user_list)
            connection.execute(insert_stmt)
            connection.commit()
            return {"status": "success", "message": "Users added successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error adding multiple users: {e}")
        return {"status": "error", "message": f"Error adding users: {e}"}

# Function to delete a user by ID


def delete_user_by_id(user_id):
    try:
        with engine.connect() as connection:
            delete_stmt = users.delete().where(users.c.id == user_id)
            connection.execute(delete_stmt)
            connection.commit()
            return {"status": "success", "message": "User deleted successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting user by ID {user_id}: {e}")
        return {"status": "error", "message": f"Error deleting user: {e}"}

# Function to update a user by ID


def update_user_by_id(user_id, username=None, password_hash=None, role=None):
    try:
        with engine.connect() as connection:
            update_stmt = update(users).where(users.c.id == user_id)
            if username:
                update_stmt = update_stmt.values(username=username)
            if password_hash:
                update_stmt = update_stmt.values(password_hash=password_hash)
            if role:
                update_stmt = update_stmt.values(role=role)
            connection.execute(update_stmt)
            connection.commit()
            return {"status": "success", "message": "User updated successfully."}
    except SQLAlchemyError as e:
        logger.error(f"Error updating user by ID {user_id}: {e}")
        return {"status": "error", "message": f"Error updating user: {e}"}
