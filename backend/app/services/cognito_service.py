import boto3
import hmac
import hashlib
import base64
import os
from typing import Dict, Optional, Tuple
from botocore.exceptions import ClientError
import logging
from google.auth.transport import requests
from google.oauth2 import id_token

from ..core.config import settings

logger = logging.getLogger(__name__)


class CognitoService:
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
    
    async def register_user(
        self,
        email: str,
        password: str,
        username: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        try:
            user_attributes = [
                {'Name': 'email', 'Value': email},
                {'Name': 'preferred_username', 'Value': username},
            ]
            
            if first_name:
                user_attributes.append({'Name': 'given_name', 'Value': first_name})
            if last_name:
                user_attributes.append({'Name': 'family_name', 'Value': last_name})
            
            params = {
                'ClientId': self.client_id,
                'Username': email,
                'Password': password,
                'UserAttributes': user_attributes
            }
            
            secret_hash = self._get_secret_hash(email)
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            response = self.client.sign_up(**params)
            
            return True, {
                'user_sub': response['UserSub'],
                'user_confirmed': response.get('UserConfirmed', False)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Cognito registration error: {error_code} - {error_message}")
            
            return False, {'error': error_code, 'message': error_message}
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return False, {'error': 'INTERNAL_ERROR', 'message': str(e)}
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str
    ) -> Tuple[bool, Dict]:
        try:
            params = {
                'ClientId': self.client_id,
                'AuthFlow': 'USER_PASSWORD_AUTH',
                'AuthParameters': {
                    'USERNAME': email,
                    'PASSWORD': password
                }
            }
            
            secret_hash = self._get_secret_hash(email)
            if secret_hash:
                params['AuthParameters']['SECRET_HASH'] = secret_hash
            
            response = self.client.initiate_auth(**params)
            
            if response.get('ChallengeName'):
                return False, {
                    'error': 'AUTH_CHALLENGE',
                    'challenge': response['ChallengeName'],
                    'session': response.get('Session')
                }
            
            auth_result = response['AuthenticationResult']
            
            return True, {
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': auth_result['RefreshToken'],
                'expires_in': auth_result['ExpiresIn'],
                'token_type': auth_result['TokenType']
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Cognito authentication error: {error_code} - {error_message}")
            
            return False, {'error': error_code, 'message': error_message}
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return False, {'error': 'INTERNAL_ERROR', 'message': str(e)}
    
    async def authenticate_with_google(
        self,
        google_id_token: str
    ) -> Tuple[bool, Dict]:
        try:
            idinfo = id_token.verify_oauth2_token(
                google_id_token,
                requests.Request(),
                os.getenv('GOOGLE_CLIENT_ID')
            )
            
            email = idinfo['email']
            given_name = idinfo.get('given_name', '')
            family_name = idinfo.get('family_name', '')
            
            params = {
                'ClientId': self.client_id,
                'AuthFlow': 'CUSTOM_AUTH',
                'AuthParameters': {
                    'USERNAME': email,
                    'CHALLENGE_NAME': 'GOOGLE_AUTH',
                    'GOOGLE_TOKEN': google_id_token
                }
            }
            
            response = self.client.initiate_auth(**params)
            
            auth_result = response['AuthenticationResult']
            
            return True, {
                'email': email,
                'given_name': given_name,
                'family_name': family_name,
                'user_sub': idinfo['sub'],
                'tokens': {
                    'access_token': auth_result['AccessToken'],
                    'id_token': auth_result['IdToken'],
                    'refresh_token': auth_result['RefreshToken'],
                    'expires_in': auth_result['ExpiresIn'],
                    'token_type': auth_result['TokenType']
                }
            }
            
        except Exception as e:
            logger.error(f"Google authentication error: {str(e)}")
            return False, {'error': 'GOOGLE_AUTH_FAILED', 'message': str(e)}
    
    async def refresh_tokens(
        self,
        refresh_token: str
    ) -> Tuple[bool, Dict]:
        try:
            params = {
                'ClientId': self.client_id,
                'AuthFlow': 'REFRESH_TOKEN_AUTH',
                'AuthParameters': {
                    'REFRESH_TOKEN': refresh_token
                }
            }
            
            if self.client_secret:
                params['AuthParameters']['SECRET_HASH'] = self._get_secret_hash(refresh_token)
            
            response = self.client.initiate_auth(**params)
            auth_result = response['AuthenticationResult']
            
            return True, {
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': refresh_token,
                'expires_in': auth_result['ExpiresIn'],
                'token_type': auth_result['TokenType']
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Token refresh error: {error_code} - {error_message}")
            
            return False, {'error': error_code, 'message': error_message}
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            return False, {'error': 'INTERNAL_ERROR', 'message': str(e)}