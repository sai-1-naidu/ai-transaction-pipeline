from fastapi import FastAPI
from app.db.database import engine, Base
from app.api.jobs import router as jobs_router

import app.models.job
import app.models.transaction
import app.models.job_summary
from app.api.summary import router as summary_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Transaction Pipeline", description="An AI-powered transaction processing pipeline.", version="1.0.0")
app.include_router(jobs_router)
app.include_router(summary_router)

@app.get("/")
def home():
    return {"message": "Welcome to the AI Transaction Pipeline!"}