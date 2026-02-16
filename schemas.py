from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ExerciseCreate(BaseModel):
    name: str

class ExerciseOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class SetCreate(BaseModel):
    exercise_id: int
    reps: int
    rpe: Optional[float]
    weight: int

class SetOut(BaseModel):
    id: int
    exercise_id: int
    reps: int
    rpe: Optional[float]
    weight: int

    class Config:
        from_attributes = True

class WorkoutCreate(BaseModel):
    notes: Optional[str]
    sets: List[SetCreate] = []

class WorkoutOut(BaseModel):
    id: int
    started_at: datetime
    notes: Optional[str]
    sets: List[SetOut]

    class Config:
        from_attributes = True