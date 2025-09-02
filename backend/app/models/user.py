from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class FitnessLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    cognito_id: str = Field(unique=True, index=True, nullable=False, max_length=255)
    email: str = Field(unique=True, index=True, nullable=False, max_length=255)
    username: str = Field(unique=True, index=True, nullable=False, max_length=100)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    last_login: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    
    profile: Optional["UserProfile"] = Relationship(back_populates="user")
    workout_programs: List["WorkoutProgram"] = Relationship(back_populates="user")


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", unique=True, nullable=False)
    fitness_level: Optional[FitnessLevel] = Field(default=None)
    goals: Optional[List[str]] = Field(default=None, sa_column_kwargs={"type": "JSON"})
    equipment: Optional[List[str]] = Field(default=None, sa_column_kwargs={"type": "JSON"})
    has_completed_onboarding: bool = Field(default=False)
    age: Optional[int] = Field(default=None, ge=13, le=120)
    height_cm: Optional[float] = Field(default=None, ge=50, le=300)
    weight_kg: Optional[float] = Field(default=None, ge=20, le=500)
    preferred_workout_time: Optional[str] = Field(default=None, max_length=50)
    injury_notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    
    user: User = Relationship(back_populates="profile")