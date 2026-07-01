from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
import os
import shutil

from app.db.session import get_db
from app.models.job import Job
from app.models.transaction import Transaction
from app.workers.tasks import process_job
from app.models.job_summary import JobSummary
import json

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------------------------
# Upload CSV/Excel
# ------------------------------------
@router.post("/jobs/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filepath = os.path.join(UPLOAD_DIR, file.filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job = Job(
        filename=file.filename,
        status="pending"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    process_job.delay(job.id, filepath)

    return {
        "job_id": job.id,
        "status": job.status,
        "filename": job.filename
    }


# ------------------------------------
# Job Status
# ------------------------------------
from app.models.job_summary import JobSummary

@router.get("/jobs/{job_id}/status")
def job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "raw_rows": job.row_count_raw,
        "clean_rows": job.row_count_clean,
        "error": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }

    if job.status == "completed":
        summary = db.query(JobSummary).filter(
            JobSummary.job_id == job.id
        ).first()

        if summary:
            response["summary"] = {
                "total_spend_inr": summary.total_spend_inr,
                "total_spend_usd": summary.total_spend_usd,
                "anomaly_count": summary.anomaly_count,
                "risk_level": summary.risk_level,
            }

    return response

# ------------------------------------
# Job Results
# ------------------------------------
@router.get("/jobs/{job_id}/results")
def get_results(job_id: int, db: Session = Depends(get_db)):

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Job is not completed yet"
        )

    transactions = (
        db.query(Transaction)
        .filter(Transaction.job_id == job.id)
        .all()
    )

    summary = (
        db.query(JobSummary)
        .filter(JobSummary.job_id == job.id)
        .first()
    )

    cleaned = []

    for t in transactions:
        cleaned.append({
            "txn_id": t.txn_id,
            "date": str(t.date) if t.date else None,
            "merchant": t.merchant,
            "amount": t.amount,
            "currency": t.currency,
            "status": t.status,
            "category": t.category,
            "account_id": t.account_id,
            "is_anomaly": t.is_anomaly,
            "anomaly_reason": t.anomaly_reason,
            "llm_category": t.llm_category
        })

    anomalies = [
        t for t in cleaned
        if t["is_anomaly"]
    ]

    category_spend = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount)
        )
        .filter(Transaction.job_id == job.id)
        .group_by(Transaction.category)
        .all()
    )

    category_spend = [
        {
            "category": category,
            "amount": float(amount)
        }
        for category, amount in category_spend
    ]

    return {
        "job_id": job.id,
        "filename": job.filename,
        "status": job.status,
        "raw_rows": job.row_count_raw,
        "clean_rows": job.row_count_clean,
        "total_transactions": len(cleaned),
        "total_anomalies": len(anomalies),

        "summary": {
            "total_spend_inr": summary.total_spend_inr if summary else 0,
            "total_spend_usd": summary.total_spend_usd if summary else 0,
            "anomaly_count": summary.anomaly_count if summary else 0,
            "risk_level": summary.risk_level if summary else None,
            "top_merchants": (
                json.loads(summary.top_merchants)
                if summary and summary.top_merchants
                else {}
            ),
            "narrative": summary.narrative if summary else ""
        },

        "category_breakdown": category_spend,

        "flagged_anomalies": anomalies,

        "transactions": cleaned
    }
# ------------------------------------
# Get All Jobs
# ------------------------------------
@router.get("/jobs")
def get_jobs(
    db: Session = Depends(get_db)
):
    jobs = db.query(Job).all()

    return [
        {
            "job_id": job.id,
            "filename": job.filename,
            "status": job.status,
            "raw_rows": job.row_count_raw,
            "clean_rows": job.row_count_clean,
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }
        for job in jobs
    ]
from app.models.job_summary import JobSummary

@router.get("/jobs/{job_id}/summary")
def get_jobs_summary(job_id: int, db: Session = Depends(get_db)):
    summary = (
        db.query(JobSummary)
        .filter(JobSummary.job_id == job_id)
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return {
        "job_id": summary.job_id,
        "total_spend_inr": summary.total_spend_inr,
        "total_spend_usd": summary.total_spend_usd,
        "anomaly_count": summary.anomaly_count,
        "top_merchants": summary.top_merchants,
        "risk_level": summary.risk_level,
        "narrative": summary.narrative
    }
@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    jobs = db.query(Job).count()
    anomalies = db.query(Transaction).filter(
        Transaction.is_anomaly == True
    ).count()

    return {
        "total_jobs": jobs,
        "total_anomalies": anomalies
    }
from fastapi.responses import FileResponse

@router.get("/jobs/{job_id}/download")
def download(job_id: int):
    path = f"uploads/cleaned_job_{job_id}.csv"

    return FileResponse(
        path,
        media_type="text/csv",
        filename=f"cleaned_job_{job_id}.csv"
    )