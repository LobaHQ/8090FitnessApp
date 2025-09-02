from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class ProgramStatus(str, Enum):
    GENERATED = "generated"
    SAVED = "saved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkoutStyle(str, Enum):
    STRENGTH = "Strength"
    CARDIO = "Cardio"
    HYBRID = "Hybrid"
    FLEXIBILITY = "Flexibility"
    HIIT = "HIIT"


class WorkoutProgram(SQLModel, table=True):
    __tablename__ = "workout_programs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    title: str = Field(nullable=False, max_length=255)
    description: Optional[str] = Field(default=None)
    status: ProgramStatus = Field(default=ProgramStatus.GENERATED)
    weekly_frequency: int = Field(nullable=False, ge=1, le=7)
    session_duration_minutes: int = Field(nullable=False, ge=10, le=300)
    workout_style: WorkoutStyle = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    
    user: "User" = Relationship(back_populates="workout_programs")
    workout_days: List["WorkoutDay"] = Relationship(back_populates="program")


class WorkoutDay(SQLModel, table=True):
    __tablename__ = "workout_days"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    program_id: UUID = Field(foreign_key="workout_programs.id", nullable=False, index=True)
    day_number: int = Field(nullable=False, ge=1, le=7)
    day_name: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None)
    
    program: WorkoutProgram = Relationship(back_populates="workout_days")
    program_exercises: List["ProgramExercise"] = Relationship(back_populates="workout_day")


class Exercise(SQLModel, table=True):
    __tablename__ = "exercises"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, nullable=False, max_length=255)
    description: Optional[str] = Field(default=None)
    muscle_groups: Optional[List[str]] = Field(
        default=None, 
        sa_column_kwargs={"type": "JSON"}
    )
    equipment_needed: Optional[List[str]] = Field(
        default=None,
        sa_column_kwargs={"type": "JSON"}
    )
    difficulty_level: Optional[str] = Field(default=None, max_length=50)
    video_url: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)
    instructions: Optional[List[str]] = Field(
        default=None,
        sa_column_kwargs={"type": "JSON"}
    )
    
    program_exercises: List["ProgramExercise"] = Relationship(back_populates="exercise")


class ProgramExercise(SQLModel, table=True):
    __tablename__ = "program_exercises"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    workout_day_id: UUID = Field(foreign_key="workout_days.id", nullable=False, index=True)
    exercise_id: UUID = Field(foreign_key="exercises.id", nullable=False, index=True)
    sets: Optional[int] = Field(default=None, ge=1, le=20)
    reps: Optional[str] = Field(default=None, max_length=50)
    rest_seconds: Optional[int] = Field(default=None, ge=0, le=600)
    notes: Optional[str] = Field(default=None)
    order_index: int = Field(nullable=False, ge=0)
    
    workout_day: WorkoutDay = Relationship(back_populates="program_exercises")
    exercise: Exercise = Relationship(back_populates="program_exercises")


class WorkoutLog(SQLModel, table=True):
    __tablename__ = "workout_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    program_exercise_id: UUID = Field(foreign_key="program_exercises.id", nullable=False)
    completion_date: datetime = Field(nullable=False)
    logged_sets: List[dict] = Field(
        default=None,
        sa_column_kwargs={"type": "JSON"}
    )
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)