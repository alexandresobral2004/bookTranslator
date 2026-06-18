from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from core.jobs.job_model import JobStatus

class UploadResponse(BaseModel):
    job_id: str
    filename: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    filename: str
    status: JobStatus
    progress: float
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    output_filename: Optional[str] = None
    error_message: Optional[str] = None
