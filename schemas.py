# schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ExerciseOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SetCreate(BaseModel):
    exercise_id: int
    reps: int
    weight: float
    rpe: Optional[float] = None


class SetOut(BaseModel):
    id: int
    exercise_id: int
    reps: int
    weight: float
    rpe: Optional[float] = None

    class Config:
        from_attributes = True


class WorkoutCreate(BaseModel):
    notes: Optional[str] = ""
    sets: List[SetCreate] = []


class WorkoutOut(BaseModel):
    id: int
    started_at: datetime
    notes: str
    sets: List[SetOut] = []

    class Config:
        from_attributes = True
