import asyncio
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    params: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    position: int = 0


class QueueService:
    """
    Simple in-memory queue for image generation.
    Limits concurrent generations to prevent server overload.
    """

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.jobs: Dict[str, Job] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.active_count = 0
        self._lock = asyncio.Lock()
        self._workers_started = False

    async def start_workers(self):
        """Start background workers (call once at startup)"""
        if self._workers_started:
            return
        self._workers_started = True
        for i in range(self.max_concurrent):
            asyncio.create_task(self._worker(i))

    async def _worker(self, worker_id: int):
        """Background worker that processes jobs from the queue"""
        while True:
            job_id = await self.queue.get()
            try:
                job = self.jobs.get(job_id)
                if job and job.status == JobStatus.PENDING:
                    async with self._lock:
                        self.active_count += 1
                        job.status = JobStatus.PROCESSING

                    try:
                        # Import here to avoid circular imports
                        from app.services.pollinations import PerchanceService

                        params = job.params
                        job_type = params.pop("job_type", "generate")

                        if job_type == "img2img":
                            success, image_url, seed, error = await PerchanceService.image_to_image(
                                **params
                            )
                        else:
                            success, image_url, seed, error = await PerchanceService.generate_image(
                                **params
                            )

                        if success:
                            job.status = JobStatus.COMPLETED
                            job.result = {
                                "success": True,
                                "image_url": image_url,
                                "seed": seed,
                                "model": params.get("model", PerchanceService.DEFAULT_MODEL)
                            }
                        else:
                            job.status = JobStatus.FAILED
                            job.error = error

                    except Exception as e:
                        job.status = JobStatus.FAILED
                        job.error = str(e)

                    async with self._lock:
                        self.active_count -= 1

            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
            finally:
                self.queue.task_done()
                await self._update_positions()

    async def _update_positions(self):
        """Update position numbers for pending jobs"""
        position = 1
        # Get items in queue order (approximate)
        for job_id, job in self.jobs.items():
            if job.status == JobStatus.PENDING:
                job.position = position
                position += 1

    async def add_job(self, params: Dict[str, Any]) -> Job:
        """Add a new job to the queue"""
        job_id = str(uuid.uuid4())

        async with self._lock:
            queue_size = self.queue.qsize()
            position = queue_size + 1

        job = Job(
            id=job_id,
            params=params,
            position=position
        )
        self.jobs[job_id] = job
        await self.queue.put(job_id)

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        pending = sum(1 for j in self.jobs.values() if j.status == JobStatus.PENDING)
        processing = sum(1 for j in self.jobs.values() if j.status == JobStatus.PROCESSING)

        return {
            "pending": pending,
            "processing": processing,
            "max_concurrent": self.max_concurrent,
            "available_slots": max(0, self.max_concurrent - self.active_count)
        }

    async def cleanup_old_jobs(self, max_age_seconds: int = 300):
        """Remove completed/failed jobs older than max_age_seconds"""
        now = datetime.now()
        to_remove = []

        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                age = (now - job.created_at).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self.jobs[job_id]


# Global queue instance
queue_service = QueueService(max_concurrent=3)
