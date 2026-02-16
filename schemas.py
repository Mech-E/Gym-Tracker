from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    name: str


class ExerciseOut(BaseModel):
    id: int
    name: str

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


# ✅ NEW: Bodyweight
class BodyweightCreate(BaseModel):
    weight: float
    notes: Optional[str] = ""


class BodyweightOut(BaseModel):
    id: int
    measured_at: datetime
    weight: float
    notes: str

    class Config:
        from_attributes = True
