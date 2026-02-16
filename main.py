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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Health (support /health and /api/health)
# -----------------------------
@app.get("/health")
@app.get("/health/")
@app.get("/api/health")
@app.get("/api/health/")
def health():
    return {"ok": True}

# -----------------------------
# Exercises (support /exercises and /api/exercises, with and without trailing slash)
# -----------------------------
@app.get("/exercises", response_model=List[schemas.ExerciseOut])
@app.get("/exercises/", response_model=List[schemas.ExerciseOut])
@app.get("/api/exercises", response_model=List[schemas.ExerciseOut])
@app.get("/api/exercises/", response_model=List[schemas.ExerciseOut])
def list_exercises(db: Session = Depends(get_db)):
    return db.query(Backend.Exercise).order_by(Backend.Exercise.name.asc()).all()

@app.post("/exercises", response_model=schemas.ExerciseOut)
@app.post("/exercises/", response_model=schemas.ExerciseOut)
@app.post("/api/exercises", response_model=schemas.ExerciseOut)
@app.post("/api/exercises/", response_model=schemas.ExerciseOut)
def create_exercise(exercise: schemas.ExerciseCreate, db: Session = Depends(get_db)):
    name = (exercise.name or "").strip()
    if not name:
        # FastAPI will normally return 422 if schema requires it, but keep safe
        return {"id": -1, "name": ""}

    ex = Backend.Exercise(name=name)
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex

# -----------------------------
# Workouts (support /workouts and /api/workouts, with and without trailing slash)
# -----------------------------
@app.post("/workouts", response_model=schemas.WorkoutOut)
@app.post("/workouts/", response_model=schemas.WorkoutOut)
@app.post("/api/workouts", response_model=schemas.WorkoutOut)
@app.post("/api/workouts/", response_model=schemas.WorkoutOut)
def create_workout(workout: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    w = Backend.Workout(notes=workout.notes)
    db.add(w)
    db.flush()  # get w.id without committing yet

    for s in workout.sets:
        se = Backend.SetEntry(
            workout_id=w.id,
            exercise_id=s.exercise_id,
            reps=s.reps,
            rpe=s.rpe,
            weight=s.weight,
        )
        db.add(se)

    db.commit()
    db.refresh(w)
    return w

@app.get("/workouts", response_model=List[schemas.WorkoutOut])
@app.get("/workouts/", response_model=List[schemas.WorkoutOut])
@app.get("/api/workouts", response_model=List[schemas.WorkoutOut])
@app.get("/api/workouts/", response_model=List[schemas.WorkoutOut])
def list_workouts(db: Session = Depends(get_db)):
    return db.query(Backend.Workout).order_by(Backend.Workout.started_at.desc()).all()

# -----------------------------
# Progress (support /progress and /api/progress)
# -----------------------------
@app.get("/progress/{exercise_id}")
@app.get("/progress/{exercise_id}/")
@app.get("/api/progress/{exercise_id}")
@app.get("/api/progress/{exercise_id}/")
def get_progress(exercise_id: int, db: Session = Depends(get_db)):
    sets = (
        db.query(Backend.SetEntry)
        .filter(Backend.SetEntry.exercise_id == exercise_id)
        .order_by(Backend.SetEntry.id.asc())
        .limit(2000)
        .all()
    )

    def epley_1rm(w: float, r: int) -> float:
        return w * (1.0 + r / 30.0)

    best_weight = 0.0
    best_1rm = 0.0
    series = []

    for s in sets:
        w = float(s.weight)
        r = int(s.reps)

        best_weight = max(best_weight, w)
        best_1rm = max(best_1rm, epley_1rm(w, r))

        series.append(
            {
                "set_id": s.id,
                "weight": w,
                "reps": r,
                "rpe": None if s.rpe is None else float(s.rpe),
                "e1rm": round(epley_1rm(w, r), 2),
            }
        )

    return {
        "exercise_id": exercise_id,
        "best_weight": round(best_weight, 2),
        "best_1rm": round(best_1rm, 2),
        "series": series,
    }

# -----------------------------
# Serve frontend LAST
# -----------------------------
app.mount("/", StaticFiles(directory=".", html=True), name="static")
