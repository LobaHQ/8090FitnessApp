from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class FitnessLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class UserProfileUpdateRequest(BaseModel):
    fitness_level: Optional[FitnessLevel] = None
    goals: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    age: Optional[int] = Field(None, ge=13, le=120)
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=20, le=500)
    preferred_workout_time: Optional[str] = Field(None, max_length=50)
    injury_notes: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    fitness_level: Optional[FitnessLevel]
    goals: Optional[List[str]]
    equipment: Optional[List[str]]
    has_completed_onboarding: bool
    age: Optional[int]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    preferred_workout_time: Optional[str]
    injury_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True