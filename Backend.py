from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("name", name="uq_exercises_name"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    notes = Column(Text, default="", nullable=False)

    sets = relationship(
        "SetEntry",
        back_populates="workout",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SetEntry(Base):
    __tablename__ = "set_entries"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)

    reps = Column(Integer, nullable=False)
    rpe = Column(Float, nullable=True)
    weight = Column(Float, nullable=False)

    workout = relationship("Workout", back_populates="sets")
    exercise = relationship("Exercise")


# ✅ NEW: Bodyweight logging table
class BodyweightEntry(Base):
    __tablename__ = "bodyweight_entries"

    id = Column(Integer, primary_key=True, index=True)
    measured_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    weight = Column(Float, nullable=False)  # bodyweight
    notes = Column(Text, default="", nullable=False)