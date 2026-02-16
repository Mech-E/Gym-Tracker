from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine, Base
import Backend
import schemas

app = FastAPI(title="Gym Tracker")

# Create tables
Base.metadata.create_all(bind=engine)

# CORS (ok for now; tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_sdb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Exercises ----------
@app.get("/exercises/", response_model=List[schemas.ExerciseOut])
def list_exercises(db: Session = Depends(get_sdb)):
    return db.query(Backend.Exercise).order_by(Backend.Exercise.name.asc()).all()

@app.post("/exercises/", response_model=schemas.ExerciseOut)
def create_exercise(exercise: schemas.ExerciseCreate, db: Session = Depends(get_sdb)):
    ex = Backend.Exercise(name=exercise.name.strip())
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex

# ---------- Workouts ----------
@app.post("/workouts/", response_model=schemas.WorkoutOut)
def create_workout(workout: schemas.WorkoutCreate, db: Session = Depends(get_sdb)):
    w = Backend.Workout(notes=workout.notes)
    db.add(w)
    db.flush()  # get w.id without committing yet

    for s in workout.sets:
        se = Backend.SetEntry(
            workout_id=w.id,
            exercise_id=s.exercise_id,
            reps=s.reps,
            rpe=s.rpe,
            weight=s.weight
        )
        db.add(se)

    db.commit()
    db.refresh(w)
    return w

@app.get("/workouts/", response_model=List[schemas.WorkoutOut])
def list_workouts(db: Session = Depends(get_sdb)):
    return db.query(Backend.Workout).order_by(Backend.Workout.started_at.desc()).all()

# ---------- Progress ----------
@app.get("/progress/{exercise_id}")
def get_progress(exercise_id: int, db: Session = Depends(get_sdb)):
    sets = (
        db.query(Backend.SetEntry)
        .filter(Backend.SetEntry.exercise_id == exercise_id)
        .order_by(Backend.SetEntry.id.asc())
        .limit(2000)
        .all()
    )

    def epley_1rm(w, r):
        return w * (1.0 + r / 30.0)

    best_weight = 0.0
    best_1rm = 0.0
    series = []

    for s in sets:
        best_weight = max(best_weight, s.weight)
        best_1rm = max(best_1rm, epley_1rm(s.weight, s.reps))
        series.append({
            "set_id": s.id,
            "weight": s.weight,   # fixed typo
            "reps": s.reps,
            "e1rm": round(epley_1rm(s.weight, s.reps), 2)
        })

    return {
        "exercise_id": exercise_id,
        "best_weight": best_weight,
        "best_1rm": round(best_1rm, 2),
        "series": series
    }

# ---------- Serve frontend LAST ----------
# If your index.html/app.js are in repo root:
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# If they are inside a folder named "app", use instead:
# app.mount("/", StaticFiles(directory="app", html=True), name="static")
