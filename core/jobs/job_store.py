import threading
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from core.jobs.job_model import Job, JobStatus

class JobStore:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, job_id: str, filename: str) -> Job:
        with self._lock:
            job = Job(job_id=job_id, filename=filename)
            self._jobs[job_id] = job
            return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        output_filename: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            
            if status is not None:
                job.status = status
                if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    job.completed_at = datetime.utcnow()
            if progress is not None:
                job.progress = min(max(progress, 0.0), 100.0)
            if message is not None:
                job.message = message
            if output_filename is not None:
                job.output_filename = output_filename
            if error_message is not None:
                job.error_message = error_message
                
            return job

    def list_jobs(self) -> List[Job]:
        with self._lock:
            return list(self._jobs.values())

    def clean_old_jobs(self, max_age_hours: int) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed_count = 0
        with self._lock:
            keys_to_remove = []
            for job_id, job in self._jobs.items():
                # Remove apenas se estiver finalizado ou falhado
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    ref_time = job.completed_at or job.created_at
                    if ref_time < cutoff:
                        keys_to_remove.append(job_id)
            
            for key in keys_to_remove:
                del self._jobs[key]
                removed_count += 1
        return removed_count

# Singleton de store de jobs
job_store = JobStore()
