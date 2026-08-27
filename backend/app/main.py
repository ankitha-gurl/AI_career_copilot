from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.copilot import router as copilot_router
from app.api.interview import router as interview_router
from app.api.jobs import router as jobs_router
from app.api.profile import router as profile_router
from app.api.resumes import router as resumes_router
from app.api.roadmap import router as roadmap_router
from app.api.skills import router as skills_router
from app.users import router as users_router

from app.database import Base, engine


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Career Copilot API",
    description="AI-powered career intelligence platform",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(skills_router)
app.include_router(roadmap_router)
app.include_router(interview_router)
app.include_router(copilot_router)


@app.get("/")
def root():
    return {
        "message": "AI Career Copilot API is running",
        "status": "success"
    }


@app.get("/health")
def health():
    try:
        with engine.connect():
            database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "database": database_status
    }