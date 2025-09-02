from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import datetime

from ..models.auth_models import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    AuthTokenResponse,
    UserRegistrationResponse,
    ErrorResponse
)
from ..services.cognito_service import CognitoService
from ..database.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

cognito_service = CognitoService()
user_repository = UserRepository()


@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegistrationRequest):
    try:
        success, result = cognito_service.register_user(
            email=request.email,
            password=request.password,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        if not success:
            error_mapping = {
                'USER_EXISTS': status.HTTP_409_CONFLICT,
                'INVALID_PASSWORD': status.HTTP_400_BAD_REQUEST,
                'INVALID_PARAMETER': status.HTTP_400_BAD_REQUEST,
                'REGISTRATION_FAILED': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'INTERNAL_ERROR': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
            
            status_code = error_mapping.get(result.get('error'), status.HTTP_400_BAD_REQUEST)
            
            raise HTTPException(
                status_code=status_code,
                detail=ErrorResponse(
                    error=result.get('error', 'UNKNOWN_ERROR'),
                    message=result.get('message', 'Registration failed'),
                    status_code=status_code
                ).dict()
            )
        
        cognito_user_id = result.get('user_sub')
        
        db_result = user_repository.create_user(
            cognito_id=cognito_user_id,
            email=request.email,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name,
            metadata={'confirmed': result.get('user_confirmed', False)}
        )
        
        if db_result and 'error' in db_result:
            logger.error(f"Failed to create user in database: {db_result}")
        
        return UserRegistrationResponse(
            user_id=cognito_user_id,
            email=request.email,
            username=request.username,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred during registration",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).dict()
        )


@router.post("/login", response_model=AuthTokenResponse)
async def login(request: UserLoginRequest):
    try:
        success, result = cognito_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not success:
            error_mapping = {
                'INVALID_CREDENTIALS': status.HTTP_401_UNAUTHORIZED,
                'USER_NOT_FOUND': status.HTTP_404_NOT_FOUND,
                'USER_NOT_CONFIRMED': status.HTTP_403_FORBIDDEN,
                'PASSWORD_RESET_REQUIRED': status.HTTP_403_FORBIDDEN,
                'AUTH_CHALLENGE': status.HTTP_202_ACCEPTED,
                'AUTH_FAILED': status.HTTP_401_UNAUTHORIZED,
                'INTERNAL_ERROR': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
            
            status_code = error_mapping.get(result.get('error'), status.HTTP_401_UNAUTHORIZED)
            
            if result.get('error') == 'AUTH_CHALLENGE':
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED,
                    content={
                        'challenge': result.get('challenge'),
                        'session': result.get('session'),
                        'message': result.get('message')
                    }
                )
            
            raise HTTPException(
                status_code=status_code,
                detail=ErrorResponse(
                    error=result.get('error', 'UNKNOWN_ERROR'),
                    message=result.get('message', 'Authentication failed'),
                    status_code=status_code
                ).dict()
            )
        
        user_repository.update_last_login(email=request.email)
        
        return AuthTokenResponse(
            access_token=result['access_token'],
            id_token=result['id_token'],
            refresh_token=result['refresh_token'],
            expires_in=result['expires_in'],
            token_type=result.get('token_type', 'Bearer')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred during login",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).dict()
        )


@router.post("/refresh-token", response_model=AuthTokenResponse)
async def refresh_token(request: TokenRefreshRequest):
    try:
        success, result = cognito_service.refresh_tokens(
            refresh_token=request.refresh_token
        )
        
        if not success:
            error_mapping = {
                'INVALID_REFRESH_TOKEN': status.HTTP_401_UNAUTHORIZED,
                'REFRESH_FAILED': status.HTTP_400_BAD_REQUEST,
                'INTERNAL_ERROR': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
            
            status_code = error_mapping.get(result.get('error'), status.HTTP_400_BAD_REQUEST)
            
            raise HTTPException(
                status_code=status_code,
                detail=ErrorResponse(
                    error=result.get('error', 'UNKNOWN_ERROR'),
                    message=result.get('message', 'Token refresh failed'),
                    status_code=status_code
                ).dict()
            )
        
        return AuthTokenResponse(
            access_token=result['access_token'],
            id_token=result['id_token'],
            refresh_token=request.refresh_token,
            expires_in=result['expires_in'],
            token_type=result.get('token_type', 'Bearer')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message="An unexpected error occurred during token refresh",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ).dict()
        )