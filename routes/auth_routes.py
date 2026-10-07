from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from services.login_services import login_user, verify_token
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme
security = HTTPBearer()


# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    status: str
    access_token: str
    token_type: str
    user: dict


class ErrorResponse(BaseModel):
    status: str
    message: str


@auth_router.post("/login", response_model=LoginResponse | ErrorResponse)
async def login(login_request: LoginRequest):
    """
    Login endpoint - Authenticate user and return JWT token.
    
    Request Body:
        - username: User's username
        - password: User's password
        
    Returns:
        - access_token: JWT token for authentication
        - token_type: Bearer
        - user: User information (id, username, role)
    """
    result = login_user(login_request.username, login_request.password)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result


@auth_router.get("/verify")
async def verify_token_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token endpoint - Check if the provided token is valid.
    
    Headers:
        - Authorization: Bearer <token>
        
    Returns:
        - User information from the token
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "status": "success",
        "message": "Token is valid",
        "user": {
            "username": payload.get("sub"),
            "role": payload.get("role")
        }
    }


@auth_router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user information from JWT token.
    
    Headers:
        - Authorization: Bearer <token>
        
    Returns:
        - Current user information
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "username": payload.get("sub"),
        "role": payload.get("role")
    }
