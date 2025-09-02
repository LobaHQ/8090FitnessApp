from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import os

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cognito_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    metadata = Column(Text, nullable=True)


class UserRepository:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///./app.db')
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def create_user(
        self,
        cognito_id: str,
        email: str,
        username: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        session = self.get_session()
        try:
            user = User(
                id=str(uuid.uuid4()),
                cognito_id=cognito_id,
                email=email.lower(),
                username=username.lower(),
                first_name=first_name,
                last_name=last_name,
                metadata=str(metadata) if metadata else None
            )
            
            session.add(user)
            session.commit()
            
            logger.info(f"User created successfully: {user.id}")
            
            return {
                'id': user.id,
                'cognito_id': user.cognito_id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error creating user: {str(e)}")
            
            if 'email' in str(e):
                return {'error': 'EMAIL_EXISTS', 'message': 'Email already exists'}
            elif 'username' in str(e):
                return {'error': 'USERNAME_EXISTS', 'message': 'Username already exists'}
            elif 'cognito_id' in str(e):
                return {'error': 'COGNITO_ID_EXISTS', 'message': 'Cognito ID already exists'}
            else:
                return {'error': 'DUPLICATE_USER', 'message': 'User already exists'}
                
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating user: {str(e)}")
            return {'error': 'DATABASE_ERROR', 'message': 'Failed to create user in database'}
            
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error creating user: {str(e)}")
            return {'error': 'INTERNAL_ERROR', 'message': 'An unexpected error occurred'}
            
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email.lower()).first()
            
            if not user:
                return None
            
            return {
                'id': user.id,
                'cognito_id': user.cognito_id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by email: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def get_user_by_cognito_id(self, cognito_id: str) -> Optional[Dict[str, Any]]:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.cognito_id == cognito_id).first()
            
            if not user:
                return None
            
            return {
                'id': user.id,
                'cognito_id': user.cognito_id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching user by Cognito ID: {str(e)}")
            return None
            
        finally:
            session.close()
    
    def update_last_login(self, email: str) -> bool:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email.lower()).first()
            
            if not user:
                return False
            
            user.last_login = datetime.utcnow()
            session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating last login: {str(e)}")
            return False
            
        finally:
            session.close()
    
    def delete_user(self, email: str) -> bool:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email.lower()).first()
            
            if not user:
                return False
            
            session.delete(user)
            session.commit()
            
            logger.info(f"User deleted successfully: {email}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deleting user: {str(e)}")
            return False
            
        finally:
            session.close()