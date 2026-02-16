from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text, default="")
    
    sets = relationship("SetEntry", back_populates="workout", cascade="all, delete")
    
class SetEntry(Base):
    __tablename__ = "set_entries"
    id = Column(Integer, primary_key=True, index=True)

    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    
    reps = Column(Integer, nullable=False)
    rpe = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)

    workout = relationship("Workout", back_populates="sets")
    exercise = relationship("Exercise")