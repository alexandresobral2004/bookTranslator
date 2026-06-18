from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    TRANSLATING = "translating"
    POSTEDITING = "postediting"
    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(BaseModel):
    job_id: str
    filename: str
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    message: str = "Aguardando início do processamento..."
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    output_filename: Optional[str] = None
    error_message: Optional[str] = None
