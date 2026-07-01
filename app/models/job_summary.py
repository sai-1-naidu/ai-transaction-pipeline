from sqlalchemy import Column, Integer, Float, String, ForeignKey
from app.db.database import Base

class JobSummary(Base):
    __tablename__ = "job_summary"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    total_spend_inr = Column(Float)
    total_spend_usd = Column(Float)
    top_merchants = Column(String)
    anomaly_count = Column(Integer)
    narrative = Column(String)
    risk_level = Column(String)