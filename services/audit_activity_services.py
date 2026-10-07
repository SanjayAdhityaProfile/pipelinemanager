from sqlalchemy import select, insert, update, delete, func
from models import audit_activity_history
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def create_audit_entry(conn, audit_data: dict) -> dict:
    """
    Create a new audit entry.

    Args:
        conn: Database connection.
        audit_data: Dictionary with audit fields like user_id, activity, and timestamp.

    Returns:
        Dict with the status or error message.
    """
    try:
        stmt = insert(audit_activity_history).values(audit_data)
        result = conn.execute(stmt)
        conn.commit()
        return {"status": "success", "message": f"Audit entry created with ID {result.inserted_primary_key[0]}"}
    except SQLAlchemyError as e:
        logger.error(f"Error creating audit entry: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_audit_entries(conn, user_id: int = None, limit: int = 10) -> list:

    """
    Fetch audit entries, optionally filtered by user.

    Args:
        conn: Database connection.
        user_id: Optional user ID to filter entries.
        limit: Number of entries to fetch.

    Returns:
        List of audit entries or an error.
    """

    try:
        stmt = select(audit_activity_history).order_by(audit_activity_history.c.timestamp.desc()).limit(limit)
        if user_id:
            stmt = stmt.where(audit_activity_history.c.user_id == user_id)

        result = conn.execute(stmt).fetchall()
        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "activity": row.activity,
                "timestamp": row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "details": row.details,
            }
            for row in result
        ]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching audit entries: {str(e)}")
        return {"status": "error", "message": str(e)}


def update_audit_entry(conn, audit_id: int, update_data: dict) -> dict:
    """
    Update an audit entry by its ID.

    Args:
        conn: Database connection.
        audit_id: ID of the audit entry to update.
        update_data: Dictionary with fields to update.

    Returns:
        Status dict with success or error message.
    """
    try:
        stmt = (
            update(audit_activity_history)
            .where(audit_activity_history.c.id == audit_id)
            .values(**update_data)
        )
        result = conn.execute(stmt)
        conn.commit()

        if result.rowcount == 0:
            return {"status": "error", "message": f"No audit entry found with ID {audit_id}"}
        return {"status": "success", "message": "Audit entry updated successfully"}
    except SQLAlchemyError as e:
        logger.error(f"Error updating audit entry: {str(e)}")
        return {"status": "error", "message": str(e)}


def delete_audit_entry(conn, audit_id: int) -> dict:
    """
    Delete an audit entry by its ID.

    Args:
        conn: Database connection.
        audit_id: ID of the audit entry to delete.

    Returns:
        Status dict with success or error message.
    """
    try:
        stmt = delete(audit_activity_history).where(audit_activity_history.c.id == audit_id)
        result = conn.execute(stmt)
        conn.commit()

        if result.rowcount == 0:
            return {"status": "error", "message": f"No audit entry found with ID {audit_id}"}
        return {"status": "success", "message": "Audit entry deleted successfully"}
    except SQLAlchemyError as e:
        logger.error(f"Error deleting audit entry: {str(e)}")
        return {"status": "error", "message": str(e)}


def get_audit_summary(conn) -> dict:
    """
    Fetch a summary of audit activities.

    Args:
        conn: Database connection.

    Returns:
        A dictionary with counts of activities per user.
    """
    try:
        stmt = select(audit_activity_history.c.user_id, func.count().label("activity_count")).group_by(audit_activity_history.c.user_id)
        result = conn.execute(stmt).fetchall()
        return {row.user_id: row.activity_count for row in result}
    except SQLAlchemyError as e:
        logger.error(f"Error fetching audit summary: {str(e)}")
        return {"status": "error", "message": str(e)}
