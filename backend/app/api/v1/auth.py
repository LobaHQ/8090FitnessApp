from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from ...schemas.auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    AuthTokenResponse,
    UserRegistrationResponse,
    GoogleAuthRequest
)
from ...models import User, UserProfile
from ...database.session import get_async_session
from ...services.cognito_service import CognitoService
from ...core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
cognito_service = CognitoService()


@router.post("/register", response_model=UserRegistrationResponse)
async def register(
    request: UserRegistrationRequest,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        success, result = await cognito_service.register_user(
            email=request.email,
            password=request.password,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', 'Registration failed')
            )
        
        user = User(
            cognito_id=result['user_sub'],
            email=request.email,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        profile = UserProfile(user_id=user.id)
        session.add(profile)
        await session.commit()
        
        return UserRegistrationResponse(
            user_id=str(user.id),
            email=user.email,
            username=user.username,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    request: UserLoginRequest,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        success, result = await cognito_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', 'Authentication failed')
            )
        
        stmt = select(User).where(User.email == request.email)
        user_result = await session.execute(stmt)
        user = user_result.scalar_one_or_none()
        
        if user:
            user.last_login = datetime.utcnow()
            await session.commit()
        
        return AuthTokenResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/google", response_model=AuthTokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        success, result = await cognito_service.authenticate_with_google(
            google_id_token=request.google_id_token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', 'Google authentication failed')
            )
        
        email = result.get('email')
        stmt = select(User).where(User.email == email)
        user_result = await session.execute(stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            user = User(
                cognito_id=result['user_sub'],
                email=email,
                username=email.split('@')[0],
                first_name=result.get('given_name'),
                last_name=result.get('family_name')
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            profile = UserProfile(user_id=user.id)
            session.add(profile)
            await session.commit()
        
        return AuthTokenResponse(**result['tokens'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during Google authentication"
        )


@router.post("/refresh-token", response_model=AuthTokenResponse)
async def refresh_token(request: TokenRefreshRequest):
    try:
        success, result = await cognito_service.refresh_tokens(
            refresh_token=request.refresh_token
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', 'Token refresh failed')
            )
        
        return AuthTokenResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh"
        )