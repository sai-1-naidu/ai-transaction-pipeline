# AI Transaction Pipeline

An AI-powered transaction processing pipeline built using **FastAPI**, **Celery**, **PostgreSQL**, **Redis**, **Docker**, and **Google Gemini AI**.

The application processes CSV and Excel transaction files asynchronously, cleans and validates data, detects anomalies, classifies uncategorized transactions using AI, generates intelligent summaries, and provides REST APIs for monitoring jobs and downloading cleaned data.

---

# Features

- Upload CSV and Excel transaction files
- Asynchronous background processing using Celery
- PostgreSQL database for persistent storage
- Redis as Celery broker and result backend
- Automatic data cleaning
- Duplicate removal
- Missing value handling
- Currency normalization
- Status normalization
- Date normalization
- Rule-based anomaly detection
- AI-powered transaction categorization using Google Gemini
- AI-generated transaction summary
- Dashboard API
- Download cleaned transaction CSV
- Dockerized deployment
- Interactive Swagger API documentation

---

# Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Celery
- Pandas
- OpenPyXL
- Google Gemini API
- Docker
- Docker Compose
- Uvicorn

---

# Project Structure

```text
ai-transaction-pipeline/
│
├── app/
│   ├── api/
│   ├── db/
│   ├── models/
│   ├── services/
│   ├── workers/
│   └── main.py
│
├── uploads/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── celery_worker.py
├── .env.example
├── README.md
└── .gitignore
```

---

# High-Level Architecture

```
                User
                  │
                  ▼
            FastAPI API
          Upload Transactions
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 PostgreSQL             Redis Queue
 (Jobs DB)                  │
                             ▼
                      Celery Worker
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   Data Cleaning      Anomaly Detection     Gemini AI
         └───────────────────┼───────────────────┘
                             ▼
                      PostgreSQL Database
                             │
                             ▼
                  Results / Summary APIs
                             │
                             ▼
                           User
```

---

# Prerequisites

Before running the project, ensure you have:

- Python 3.11+
- Docker Desktop
- Docker Compose
- Google Gemini API Key

---

# Installation

## Clone Repository

```bash
git clone https://github.com/sai-1-naidu/ai-transaction-pipeline.git

cd ai-transaction-pipeline
```

---

## Create Virtual Environment

Windows

```bash
python -m venv venv

venv\Scripts\activate
```

Linux/macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file.

```env
DATABASE_URL=postgresql://postgres:sai@postgres:5432/ai_interview

REDIS_URL=redis://redis:6379/0

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

---

# Run Using Docker

```bash
docker compose up --build
```

API

```
http://localhost:8000
```

Swagger Documentation

```
http://localhost:8000/docs
```

---

# API Endpoints

## Upload Transactions

```
POST /jobs/upload
```

Uploads a CSV or Excel transaction file for background processing.

---

## List Jobs

```
GET /jobs
```

Returns all uploaded jobs.

---

## Job Status

```
GET /jobs/{job_id}/status
```

Returns

- Job Status
- Raw Rows
- Clean Rows
- Created Time
- Completed Time
- Processing Summary

---

## Processing Results

```
GET /jobs/{job_id}/results
```

Returns

- Processed Transactions
- Categories
- Anomaly Details
- AI Classification

---

## Job Summary

```
GET /jobs/{job_id}/summary
```

Returns

- Total INR Spend
- Total USD Spend
- Anomaly Count
- Risk Level
- AI Narrative
- Top Merchants

---

## Dashboard

```
GET /dashboard
```

Returns

- Total Jobs
- Total Anomalies

---

## Download Cleaned CSV

```
GET /jobs/{job_id}/download
```

Downloads the cleaned transaction dataset.

---

# Processing Pipeline

1. User uploads CSV/Excel file
2. FastAPI creates a Job
3. Celery task is published to Redis
4. Celery Worker processes the file
5. Data Cleaning
6. Duplicate Removal
7. Missing Value Handling
8. Currency & Status Normalization
9. Date Normalization
10. Anomaly Detection
11. AI Transaction Categorization
12. AI Summary Generation
13. Store Results in PostgreSQL
14. User retrieves results via REST APIs
15. Download cleaned CSV

---

# AI Features

## Transaction Categorization

Google Gemini automatically classifies uncategorized transactions into categories such as:

- Shopping
- Food & Dining
- Utilities
- Transportation
- Travel
- Cash Withdrawal

---

## AI Summary

Automatically generates:

- Spending Overview
- Risk Level
- Merchant Insights
- Fraud Indicators
- Financial Narrative

If the Gemini API quota is exceeded, the application automatically falls back to a rule-based summary.

---

# Sample Dashboard Response

```json
{
    "total_jobs": 7,
    "total_anomalies": 4
}
```

---

# Future Improvements

- JWT Authentication
- Role-Based Access Control
- React Dashboard
- Email Notifications
- Kubernetes Deployment
- CI/CD using GitHub Actions
- ML-Based Fraud Detection
- Prometheus & Grafana Monitoring

---

# Author

**Tungala Lakshmi Venkata Sai**

GitHub

https://github.com/sai-1-naidu

LinkedIn

https://www.linkedin.com/in/tungala-lakshmi-venkata-sai-5038b6307

---

# License

This project was developed for educational purposes and internship assessment.
