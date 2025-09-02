import boto3
import hmac
import hashlib
import base64
import os
from typing import Dict, Optional, Tuple
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class CognitoService:
    def __init__(self):
        self.client = boto3.client(
            'cognito-idp',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        self.client_secret = os.getenv('COGNITO_CLIENT_SECRET')
        
        if not all([self.user_pool_id, self.client_id]):
            raise ValueError("Missing required Cognito configuration")
    
    def _get_secret_hash(self, username: str) -> str:
        if not self.client_secret:
            return None
        
        message = bytes(username + self.client_id, 'utf-8')
        key = bytes(self.client_secret, 'utf-8')
        secret_hash = base64.b64encode(
            hmac.new(key, message, digestmod=hashlib.sha256).digest()
        ).decode()
        return secret_hash
    
    def register_user(
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
                'user_confirmed': response.get('UserConfirmed', False),
                'code_delivery_details': response.get('CodeDeliveryDetails')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"Cognito registration error: {error_code} - {error_message}")
            
            if error_code == 'UsernameExistsException':
                return False, {'error': 'USER_EXISTS', 'message': 'User with this email already exists'}
            elif error_code == 'InvalidPasswordException':
                return False, {'error': 'INVALID_PASSWORD', 'message': error_message}
            elif error_code == 'InvalidParameterException':
                return False, {'error': 'INVALID_PARAMETER', 'message': error_message}
            else:
                return False, {'error': 'REGISTRATION_FAILED', 'message': 'Failed to register user'}
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return False, {'error': 'INTERNAL_ERROR', 'message': 'An unexpected error occurred'}
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Dict]:
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
                    'session': response.get('Session'),
                    'message': 'Authentication challenge required'
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
            
            if error_code == 'NotAuthorizedException':
                return False, {'error': 'INVALID_CREDENTIALS', 'message': 'Invalid email or password'}
            elif error_code == 'UserNotFoundException':
                return False, {'error': 'USER_NOT_FOUND', 'message': 'User not found'}
            elif error_code == 'UserNotConfirmedException':
                return False, {'error': 'USER_NOT_CONFIRMED', 'message': 'User account not confirmed'}
            elif error_code == 'PasswordResetRequiredException':
                return False, {'error': 'PASSWORD_RESET_REQUIRED', 'message': 'Password reset required'}
            else:
                return False, {'error': 'AUTH_FAILED', 'message': 'Authentication failed'}
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return False, {'error': 'INTERNAL_ERROR', 'message': 'An unexpected error occurred'}
    
    def refresh_tokens(self, refresh_token: str) -> Tuple[bool, Dict]:
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
                'expires_in': auth_result['ExpiresIn'],
                'token_type': auth_result['TokenType']
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"Cognito token refresh error: {error_code} - {error_message}")
            
            if error_code == 'NotAuthorizedException':
                return False, {'error': 'INVALID_REFRESH_TOKEN', 'message': 'Invalid or expired refresh token'}
            else:
                return False, {'error': 'REFRESH_FAILED', 'message': 'Failed to refresh tokens'}
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            return False, {'error': 'INTERNAL_ERROR', 'message': 'An unexpected error occurred'}
    
    def get_user_info(self, access_token: str) -> Tuple[bool, Dict]:
        try:
            response = self.client.get_user(AccessToken=access_token)
            
            user_attributes = {}
            for attr in response['UserAttributes']:
                user_attributes[attr['Name']] = attr['Value']
            
            return True, {
                'username': response['Username'],
                'attributes': user_attributes,
                'user_create_date': response.get('UserCreateDate'),
                'user_last_modified_date': response.get('UserLastModifiedDate')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Cognito get user error: {error_code}")
            
            if error_code == 'NotAuthorizedException':
                return False, {'error': 'INVALID_TOKEN', 'message': 'Invalid or expired access token'}
            else:
                return False, {'error': 'GET_USER_FAILED', 'message': 'Failed to get user information'}
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {str(e)}")
            return False, {'error': 'INTERNAL_ERROR', 'message': 'An unexpected error occurred'}