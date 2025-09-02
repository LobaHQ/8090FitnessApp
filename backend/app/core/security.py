from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import boto3
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
import logging

from .config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class CognitoAuth:
    def __init__(self):
        self.client = boto3.client(
            'cognito-idp',
            region_name=settings.AWS_REGION
        )
        self.user_pool_id = settings.COGNITO_USER_POOL_ID
        self.client_id = settings.COGNITO_CLIENT_ID
        self.client_secret = settings.COGNITO_CLIENT_SECRET
    
    def _get_secret_hash(self, username: str) -> Optional[str]:
        if not self.client_secret:
            return None
        
        message = bytes(username + self.client_id, 'utf-8')
        key = bytes(self.client_secret, 'utf-8')
        secret_hash = base64.b64encode(
            hmac.new(key, message, digestmod=hashlib.sha256).digest()
        ).decode()
        return secret_hash
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            response = self.client.get_user(AccessToken=token)
            user_attributes = {}
            for attr in response['UserAttributes']:
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'username': response['Username'],
                'attributes': user_attributes,
                'sub': user_attributes.get('sub')
            }
        except ClientError as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )


cognito_auth = CognitoAuth()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    
    try:
        user_info = cognito_auth.verify_token(token)
        return user_info
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )