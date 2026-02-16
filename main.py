from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine, Base
import Backend
import schemas

app = FastAPI(title="Gym Tracker")

Base.metadata.create_all(bind=engine)

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

# -------- Health (all aliases) --------
@app.get("/health")
@app.get("/health/")
@app.get("/api/health")
@app.get("/api/health/")
def health():
    return {"ok": True}

# -------- Exercises (all aliases) --------
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
    ex = Backend.Exercise(name=name)
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex

# -------- Workouts (all aliases) --------
@app.post("/workouts", response_model=schemas.WorkoutOut)
@app.post("/workouts/", response_model=schemas.WorkoutOut)
@app.post("/api/workouts", response_model=schemas.WorkoutOut)
@app.post("/api/workouts/", response_model=schemas.WorkoutOut)
def create_workout(workout: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    w = Backend.Workout(notes=workout.notes or "")
    db.add(w)
    db.flush()

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

@app.get("/workouts", response_model=List[schemas.WorkoutOut])
@app.get("/workouts/", response_model=List[schemas.WorkoutOut])
@app.get("/api/workouts", response_model=List[schemas.WorkoutOut])
@app.get("/api/workouts/", response_model=List[schemas.WorkoutOut])
def list_workouts(db: Session = Depends(get_db)):
    return db.query(Backend.Workout).order_by(Backend.Workout.started_at.desc()).all()

# -------- Progress: exercise (all aliases) --------
@app.get("/progress/{exercise_id}")
@app.get("/progress/{exercise_id}/")
@app.get("/api/progress/{exercise_id}")
@app.get("/api/progress/{exercise_id}/")
def get_progress(exercise_id: int, db: Session = Depends(get_db)):
    # Join sets to workout to get a timestamp for graphing
    rows = (
        db.query(Backend.SetEntry, Backend.Workout)
        .join(Backend.Workout, Backend.SetEntry.workout_id == Backend.Workout.id)
        .filter(Backend.SetEntry.exercise_id == exercise_id)
        .order_by(Backend.Workout.started_at.asc(), Backend.SetEntry.id.asc())
        .limit(5000)
        .all()
    )

    def epley_1rm(w: float, r: int) -> float:
        return w * (1.0 + r / 30.0)

    best_weight = 0.0
    best_1rm = 0.0
    series = []

    for s, w in rows:
        weight = float(s.weight)
        reps = int(s.reps)
        est = epley_1rm(weight, reps)

        best_weight = max(best_weight, weight)
        best_1rm = max(best_1rm, est)

        series.append({
            "t": w.started_at.isoformat(),
            "weight": weight,
            "reps": reps,
            "e1rm": round(est, 2),
        })

    return {
        "kind": "exercise",
        "exercise_id": exercise_id,
        "best_weight": round(best_weight, 2),
        "best_1rm": round(best_1rm, 2),
        "series": series
    }

# -------- Bodyweight: log + list + progress (all aliases) --------
@app.post("/bodyweight", response_model=schemas.BodyweightOut)
@app.post("/bodyweight/", response_model=schemas.BodyweightOut)
@app.post("/api/bodyweight", response_model=schemas.BodyweightOut)
@app.post("/api/bodyweight/", response_model=schemas.BodyweightOut)
def log_bodyweight(entry: schemas.BodyweightCreate, db: Session = Depends(get_db)):
    bw = Backend.BodyweightEntry(weight=float(entry.weight), notes=entry.notes or "")
    db.add(bw)
    db.commit()
    db.refresh(bw)
    return bw

@app.get("/bodyweight", response_model=List[schemas.BodyweightOut])
@app.get("/bodyweight/", response_model=List[schemas.BodyweightOut])
@app.get("/api/bodyweight", response_model=List[schemas.BodyweightOut])
@app.get("/api/bodyweight/", response_model=List[schemas.BodyweightOut])
def list_bodyweight(db: Session = Depends(get_db)):
    return db.query(Backend.BodyweightEntry).order_by(Backend.BodyweightEntry.measured_at.asc()).all()

@app.get("/progress/bodyweight")
@app.get("/progress/bodyweight/")
@app.get("/api/progress/bodyweight")
@app.get("/api/progress/bodyweight/")
def bodyweight_progress(db: Session = Depends(get_db)):
    rows = db.query(Backend.BodyweightEntry).order_by(Backend.BodyweightEntry.measured_at.asc()).all()
    series = [{"t": r.measured_at.isoformat(), "weight": float(r.weight)} for r in rows]
    best = max([x["weight"] for x in series], default=0.0)
    return {"kind": "bodyweight", "best_weight": round(best, 2), "series": series}

# -------- Serve frontend LAST --------
app.mount("/", StaticFiles(directory=".", html=True), name="static")
