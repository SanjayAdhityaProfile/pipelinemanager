from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from services.user_services import add_multiple_users, get_all_users
from services.login_services import hash_password
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Create router
user_router = APIRouter(prefix="/users", tags=["Users"])


# Pydantic models
class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"  # Default role


@user_router.post("/")
async def create_multiple_users(users: List[CreateUserRequest]):
    """
    Create multiple users.
    
    Request Body:
        - List of users with username, password, and optional role
        
    Returns:
        - Status message
    """
    try:
        # Hash passwords and prepare user list
        user_list = [
            {
                "username": user.username,
                "password_hash": hash_password(user.password),
                "role": user.role
            }
            for user in users
        ]
        
        # Add users to database
        result = add_multiple_users(user_list)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return {
            "status": "success",
            "message": result["message"],
            "count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Error creating multiple users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating users: {str(e)}"
        )


@user_router.get("/")
async def get_users():
    """
    Get all users.
    
    Returns:
        - List of all users (without password hashes)
    """
    try:
        users = get_all_users()
        
        if users is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching users"
            )
        
        # Convert to list of dictionaries and exclude password_hash
        users_list = [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "created_at": str(user.created_at) if user.created_at else None,
                "updated_at": str(user.updated_at) if user.updated_at else None
            }
            for user in users
        ]
        
        return {
            "status": "success",
            "count": len(users_list),
            "users": users_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )
