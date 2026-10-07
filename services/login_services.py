from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from models import users, engine
from sqlalchemy import select
import logging
import os
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

# Set up a logger
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """
#     Verify a plain password against a hashed password.
    
#     Args:
#         plain_password: The plain text password
#         hashed_password: The hashed password from database
        
#     Returns:
#         True if password matches, False otherwise
#     """
#     return pwd_context.verify(plain_password, hashed_password)


# def get_password_hash(password: str) -> str:
#     """
#     Hash a password for storing.
    
#     Args:
#         password: The plain text password
        
#     Returns:
#         Hashed password
#     """
#     return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing token data (e.g., username, role)
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def authenticate_user(username: str, password: str):
    """
    Authenticate a user by username and password.
    
    Args:
        username: The username
        password: The plain text password
        
    Returns:
        User data if authentication successful, None otherwise
    """
    try:
        with engine.connect() as connection:
            # Get user by username
            result = connection.execute(
                select(users).where(users.c.username == username)
            )
            user = result.fetchone()
            
            if not user:
                logger.warning(f"Login attempt failed: User '{username}' not found")
                return None
            
            # Verify password
            if not verify_password(password, user.password_hash):
                logger.warning(f"Login attempt failed: Invalid password for user '{username}'")
                return None
            
            logger.info(f"User '{username}' authenticated successfully")
            
            # Return user data (excluding password)
            return {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "created_at": user.created_at
            }
            
    except SQLAlchemyError as e:
        logger.error(f"Error authenticating user '{username}': {e}")
        return None


def login_user(username: str, password: str):
    """
    Login a user and return access token.
    
    Args:
        username: The username
        password: The plain text password
        
    Returns:
        Dictionary with access token and user info, or error message
    """
    user = authenticate_user(username, password)
    
    if not user:
        return {
            "status": "error",
            "message": "Invalid username or password"
        }
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    }


def verify_token(token: str):
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token
        
    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
            
        return payload
        
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        return None

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed.encode("utf-8"),
    )