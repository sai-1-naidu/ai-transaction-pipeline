import os
import pandas as pd

from app.services.gemini_service import (
    classify_transactions,
    generate_summary
    
)
from celery_worker import celery
from app.db.database import SessionLocal
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.job_summary import JobSummary
import json
import logging

logger = logging.getLogger(__name__)


@celery.task
def process_job(job_id, file_path):

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            raise Exception(f"Job {job_id} not found")

        job.status = "processing"
        db.commit()

        # -------------------------
        # Read File
        # -------------------------
        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".csv":
            df = pd.read_csv(file_path)

        elif extension in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)

        else:
            raise Exception("Unsupported file format")

        job.row_count_raw = len(df)
        db.commit()

        # -------------------------
        # Data Cleaning
        # -------------------------

        df.columns = df.columns.str.strip()

        # Remove duplicate rows
        df = df.drop_duplicates()

        # Fill missing categories
        if "category" in df.columns:
            df["category"] = df["category"].fillna("Uncategorised")

        # Uppercase status
        if "status" in df.columns:
            df["status"] = df["status"].astype(str).str.upper()

        # Uppercase currency
        if "currency" in df.columns:
            df["currency"] = df["currency"].astype(str).str.upper()

        # Remove $ symbol
        if "amount" in df.columns:
            df["amount"] = (
                df["amount"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .astype(float)
            )

        # Normalize dates
        if "date" in df.columns:
            df["date"] = pd.to_datetime(
                df["date"],
                format="mixed",
                dayfirst=True,
                errors="coerce"
            )

        # -------------------------
        # Anomaly Detection
        # -------------------------

        domestic_merchants = [
            "Swiggy",
            "Ola",
            "IRCTC"
        ]

        median = df.groupby("account_id")["amount"].transform("median")

        df["is_anomaly"] = df["amount"] > (3 * median)

        df["anomaly_reason"] = ""

        df.loc[
            df["amount"] > (3 * median),
            "anomaly_reason"
        ] = "Amount exceeds 3x account median"

        usd_domestic = (
            df["merchant"].isin(domestic_merchants)
            &
            (df["currency"] == "USD")
        )

        df.loc[
            usd_domestic,
            "is_anomaly"
        ] = True

        df.loc[
            usd_domestic,
            "anomaly_reason"
        ] = "Domestic merchant using USD"
       # -------------------------
        # AI Category Classification
        # -------------------------

        df["llm_category"] = None

        missing = df[df["category"] == "Uncategorised"]

        if len(missing) > 0:

            payload = []

            for _, row in missing.iterrows():
                payload.append({
            "txn_id": str(row["txn_id"]) if pd.notna(row["txn_id"]) else None,
            "merchant": str(row["merchant"]),
            "amount": float(row["amount"]),
            "currency": str(row["currency"]),
            "status": str(row["status"])
        })

            logger.info("Calling Gemini once...")
            logger.info(payload)

            df["llm_failed"] = False  # Initialize the column
            df["llm_category"] = None  # Initialize the column

            try:
                predictions = classify_transactions(payload)

                mapping = {
            p["txn_id"]: p["category"]
            for p in predictions
        }

                df.loc[
            df["txn_id"].isin(mapping.keys()),
            "llm_category"
        ] = df["txn_id"].map(mapping)

            except Exception as e:
                print("Gemini failed:", e)
                df.loc[
                    df["txn_id"].isin([p["txn_id"] for p in payload]),
                    "llm_failed"
                ] = True
                df.loc[
                    df["txn_id"].isin([p["txn_id"] for p in payload]),
                    "llm_category"
                ] = None
        # -------------------------
        # Save Transactions
        # -------------------------

        for _, row in df.iterrows():

            transaction = Transaction(
                job_id=job.id,
                txn_id=str(row.get("txn_id")),
                date=row["date"].date() if pd.notna(row["date"]) else None,
        merchant=str(row["merchant"]),
        amount=float(row["amount"]),
        currency=str(row["currency"]),
        status=str(row["status"]),
        category=str(row["llm_category"]) if pd.notna(row["llm_category"]) else str(row["category"]),
        account_id=str(row["account_id"]),
        is_anomaly=bool(row["is_anomaly"]),
        anomaly_reason=str(row["anomaly_reason"]),
        llm_category=str(row["llm_category"]) if pd.notna(row["llm_category"]) else None,
        llm_raw_response=json.dumps(predictions) if 'predictions' in locals() else None,  # You can store the raw response from the LLM if needed
        llm_failed= False if 'predictions' in locals() else True
    )
            db.add(transaction)

        db.commit()

        # -------------------------
        # Save cleaned file
        # -------------------------

        cleaned_path = os.path.join(
            "uploads",
            f"cleaned_job_{job.id}.csv"
        )

        df.to_csv(cleaned_path, index=False)

        # -------------------------
        # Update Job
        # -------------------------

        job.row_count_clean = len(df)
        job.completed_at = pd.Timestamp.now()
        db.commit()
        db.refresh(job)
        

        total_spend_inr = df[df["currency"] == "INR"]["amount"].sum()
        total_spend_usd = df[df["currency"] == "USD"]["amount"].sum()

        anomaly_count = int(df["is_anomaly"].sum())

        top_merchants = (
            df["merchant"]
    .value_counts()
    .head(5)
    .to_dict()
)

        if anomaly_count == 0:
            risk_level = "LOW"
        elif anomaly_count <= 5:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # -------------------------
        # AI Summary
        # -------------------------

        summary_payload = {
    "total_spend_inr": float(total_spend_inr),
    "total_spend_usd": float(total_spend_usd),
    "anomaly_count": anomaly_count,
    "top_merchants": top_merchants
}

        try:
            ai_summary = generate_summary(summary_payload)

            risk_level = ai_summary.get("risk_level", risk_level)
            narrative = ai_summary.get(
        "narrative",
        f"Processed {len(df)} transactions."
    )

        except Exception as e:
            print("Summary generation failed:", e)

            narrative = (
        f"Processed {len(df)} transactions with "
        f"{anomaly_count} anomalies."
    )

        summary = JobSummary(
    job_id=job.id,
    total_spend_inr=float(total_spend_inr),
    total_spend_usd=float(total_spend_usd),
    anomaly_count=anomaly_count,
    top_merchants=json.dumps(top_merchants),
    risk_level=risk_level,
    narrative=narrative
)
        db.add(summary)
        
        job.status = "completed"
        job.completed_at = pd.Timestamp.now()

        db.commit()
        db.refresh(job)

        logger.info("==== Job Processing Completed ===")
        logger.info(df.head())

        return {
            "job_id": job.id,
            "status": "completed"
        }

    except Exception as e:

        if "job" in locals() and job:

            job.status = "failed"
            job.error_message = str(e)

            db.commit()

        raise

    finally:
        db.close()