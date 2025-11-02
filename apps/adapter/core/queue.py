"""
Background job queue using Redis for asynchronous task processing.

This module provides a robust job queue with:
- Priority-based job processing (high, normal, low)
- Retry logic with exponential backoff
- Job status tracking
- Dead letter queue for failed jobs
- Scheduled/delayed job execution
- Job cancellation and cleanup
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Dict, Callable, Awaitable, List
from dataclasses import dataclass, asdict, field

from .redis_client import RedisClient, get_redis_client
from .logging import get_logger
from .exceptions import AdapterException


logger = get_logger(__name__)


class JobPriority(str, Enum):
    """Job priority levels."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class JobStatus(str, Enum):
    """Job status states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class QueueError(AdapterException):
    """Raised when queue operation fails."""
    pass


@dataclass
class Job:
    """
    Job data structure for queue processing.
    
    Attributes:
        id: Unique job identifier
        queue_name: Name of the queue
        task_name: Name of the task to execute
        payload: Job payload data
        priority: Job priority level
        status: Current job status
        created_at: Job creation timestamp
        scheduled_at: Scheduled execution time
        started_at: Processing start time
        completed_at: Processing completion time
        attempts: Number of execution attempts
        max_retries: Maximum retry attempts
        retry_delay: Base delay for retries (exponential backoff)
        error: Error message if failed
        result: Job result data
        metadata: Additional job metadata
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue_name: str = "default"
    task_name: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    attempts: int = 0
    max_retries: int = 3
    retry_delay: float = 60.0  # Base delay in seconds
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        data = asdict(self)
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """Create job from dictionary."""
        if "priority" in data:
            data["priority"] = JobPriority(data["priority"])
        if "status" in data:
            data["status"] = JobStatus(data["status"])
        return cls(**data)


class JobQueue:
    """
    Redis-backed job queue for background task processing.
    
    Features:
    - Priority queues (high, normal, low)
    - Retry with exponential backoff
    - Job status tracking
    - Dead letter queue
    - Scheduled jobs
    - Job cleanup
    
    Example:
        ```python
        queue = JobQueue()
        await queue.connect()
        
        # Enqueue job
        job_id = await queue.enqueue(
            task_name="send_email",
            payload={"to": "user@example.com"},
            priority=JobPriority.HIGH
        )
        
        # Process jobs
        async for job in queue.process():
            # Execute job logic
            result = await execute_task(job)
            await queue.complete(job.id, result)
        ```
    """
    
    # Redis key prefixes
    KEY_PREFIX = "queue"
    JOB_DATA_PREFIX = "job:data"
    JOB_STATUS_PREFIX = "job:status"
    SCHEDULED_PREFIX = "scheduled"
    DLQ_PREFIX = "dlq"
    
    def __init__(
        self,
        queue_name: str = "default",
        redis_client: Optional[RedisClient] = None
    ):
        """
        Initialize job queue.
        
        Args:
            queue_name: Name of the queue
            redis_client: Redis client instance
        """
        self.queue_name = queue_name
        self.redis_client = redis_client
        self._initialized = False
        self._processing = False
        
        logger.info(f"Initialized JobQueue: {queue_name}")
    
    async def _ensure_initialized(self) -> None:
        """Ensure Redis client is initialized."""
        if not self._initialized:
            if self.redis_client is None:
                self.redis_client = await get_redis_client()
            self._initialized = True
    
    def _queue_key(self, priority: JobPriority) -> str:
        """Get queue key for priority level."""
        return f"{self.KEY_PREFIX}:{self.queue_name}:{priority.value}"
    
    def _job_data_key(self, job_id: str) -> str:
        """Get job data key."""
        return f"{self.JOB_DATA_PREFIX}:{job_id}"
    
    def _job_status_key(self, job_id: str) -> str:
        """Get job status key."""
        return f"{self.JOB_STATUS_PREFIX}:{job_id}"
    
    def _scheduled_key(self) -> str:
        """Get scheduled jobs key."""
        return f"{self.SCHEDULED_PREFIX}:{self.queue_name}"
    
    def _dlq_key(self) -> str:
        """Get dead letter queue key."""
        return f"{self.DLQ_PREFIX}:{self.queue_name}"
    
    async def enqueue(
        self,
        task_name: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3,
        retry_delay: float = 60.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add job to queue.
        
        Args:
            task_name: Task to execute
            payload: Job payload data
            priority: Job priority level
            scheduled_at: Schedule for future execution
            max_retries: Maximum retry attempts
            retry_delay: Base retry delay in seconds
            metadata: Additional metadata
            
        Returns:
            Job ID
        """
        await self._ensure_initialized()
        
        # Create job
        job = Job(
            queue_name=self.queue_name,
            task_name=task_name,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            metadata=metadata or {}
        )
        
        # Handle scheduled jobs
        if scheduled_at:
            job.scheduled_at = scheduled_at.timestamp()
            await self._schedule_job(job)
        else:
            await self._enqueue_job(job)
        
        logger.info(
            f"Job enqueued: {job.id}",
            extra={
                "job_id": job.id,
                "task_name": task_name,
                "priority": priority.value,
                "scheduled": scheduled_at is not None
            }
        )
        
        return job.id
    
    async def _enqueue_job(self, job: Job) -> None:
        """Add job to priority queue."""
        # Store job data
        await self.redis_client.set(
            self._job_data_key(job.id),
            job.to_dict(),
            ttl=86400  # 24 hours
        )
        
        # Add to priority queue
        queue_key = self._queue_key(job.priority)
        await self.redis_client._client.lpush(queue_key, job.id)
    
    async def _schedule_job(self, job: Job) -> None:
        """Schedule job for future execution."""
        # Store job data
        await self.redis_client.set(
            self._job_data_key(job.id),
            job.to_dict(),
            ttl=86400 * 7  # 7 days for scheduled jobs
        )
        
        # Add to scheduled set with score as timestamp
        scheduled_key = self._scheduled_key()
        await self.redis_client._client.zadd(
            scheduled_key,
            {job.id: job.scheduled_at}
        )
    
    async def dequeue(self, timeout: float = 0) -> Optional[Job]:
        """
        Remove and return next job from queue.
        
        Args:
            timeout: Block timeout in seconds (0 = non-blocking)
            
        Returns:
            Job instance or None if queue is empty
        """
        await self._ensure_initialized()
        
        # Check scheduled jobs first
        await self._process_scheduled_jobs()
        
        # Try each priority queue in order
        for priority in [JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW]:
            queue_key = self._queue_key(priority)
            
            if timeout > 0:
                # Blocking pop
                result = await self.redis_client._client.brpop(queue_key, timeout=int(timeout))
                if result:
                    _, job_id = result
                    job_id = job_id.decode() if isinstance(job_id, bytes) else job_id
                else:
                    continue
            else:
                # Non-blocking pop
                job_id = await self.redis_client._client.rpop(queue_key)
                if not job_id:
                    continue
                job_id = job_id.decode() if isinstance(job_id, bytes) else job_id
            
            # Get job data
            job_data = await self.redis_client.get(self._job_data_key(job_id))
            if not job_data:
                logger.warning(f"Job data not found: {job_id}")
                continue
            
            job = Job.from_dict(job_data)
            job.status = JobStatus.PROCESSING
            job.started_at = time.time()
            job.attempts += 1
            
            # Update job status
            await self._update_job(job)
            
            logger.debug(f"Job dequeued: {job.id} (attempt {job.attempts})")
            return job
        
        return None
    
    async def complete(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark job as completed.
        
        Args:
            job_id: Job identifier
            result: Job result data
        """
        await self._ensure_initialized()
        
        job_data = await self.redis_client.get(self._job_data_key(job_id))
        if not job_data:
            logger.warning(f"Job not found for completion: {job_id}")
            return
        
        job = Job.from_dict(job_data)
        job.status = JobStatus.COMPLETED
        job.completed_at = time.time()
        job.result = result
        
        await self._update_job(job)
        
        logger.info(
            f"Job completed: {job_id}",
            extra={
                "job_id": job_id,
                "attempts": job.attempts,
                "duration_ms": int((job.completed_at - job.started_at) * 1000) if job.started_at else 0
            }
        )
    
    async def fail(self, job_id: str, error: str, retry: bool = True) -> None:
        """
        Mark job as failed and optionally retry.
        
        Args:
            job_id: Job identifier
            error: Error message
            retry: Whether to retry the job
        """
        await self._ensure_initialized()
        
        job_data = await self.redis_client.get(self._job_data_key(job_id))
        if not job_data:
            logger.warning(f"Job not found for failure: {job_id}")
            return
        
        job = Job.from_dict(job_data)
        job.error = error
        
        # Check if should retry
        if retry and job.attempts < job.max_retries:
            # Calculate retry delay with exponential backoff
            delay = job.retry_delay * (2 ** (job.attempts - 1))
            scheduled_at = datetime.now() + timedelta(seconds=delay)
            
            job.status = JobStatus.RETRY
            job.scheduled_at = scheduled_at.timestamp()
            
            await self._update_job(job)
            await self._schedule_job(job)
            
            logger.warning(
                f"Job retry scheduled: {job_id}",
                extra={
                    "job_id": job_id,
                    "attempt": job.attempts,
                    "max_retries": job.max_retries,
                    "retry_delay": delay,
                    "error": error
                }
            )
        else:
            # Move to dead letter queue
            job.status = JobStatus.FAILED
            job.completed_at = time.time()
            
            await self._update_job(job)
            await self._move_to_dlq(job)
            
            logger.error(
                f"Job failed permanently: {job_id}",
                extra={
                    "job_id": job_id,
                    "attempts": job.attempts,
                    "error": error
                }
            )
    
    async def cancel(self, job_id: str) -> bool:
        """
        Cancel pending job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        await self._ensure_initialized()
        
        job_data = await self.redis_client.get(self._job_data_key(job_id))
        if not job_data:
            return False
        
        job = Job.from_dict(job_data)
        
        # Can only cancel pending jobs
        if job.status not in [JobStatus.PENDING, JobStatus.RETRY]:
            logger.warning(f"Cannot cancel job in status: {job.status}")
            return False
        
        job.status = JobStatus.CANCELLED
        job.completed_at = time.time()
        
        await self._update_job(job)
        
        # Remove from queues
        if job.scheduled_at:
            await self.redis_client._client.zrem(self._scheduled_key(), job_id)
        else:
            # Remove from priority queue (may not be efficient for large queues)
            queue_key = self._queue_key(job.priority)
            await self.redis_client._client.lrem(queue_key, 0, job_id)
        
        logger.info(f"Job cancelled: {job_id}")
        return True
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job instance or None
        """
        await self._ensure_initialized()
        
        job_data = await self.redis_client.get(self._job_data_key(job_id))
        if not job_data:
            return None
        
        return Job.from_dict(job_data)
    
    async def get_queue_size(self, priority: Optional[JobPriority] = None) -> int:
        """
        Get number of pending jobs in queue.
        
        Args:
            priority: Specific priority or None for all
            
        Returns:
            Number of pending jobs
        """
        await self._ensure_initialized()
        
        if priority:
            queue_key = self._queue_key(priority)
            return await self.redis_client._client.llen(queue_key)
        
        # Sum all priorities
        total = 0
        for p in JobPriority:
            queue_key = self._queue_key(p)
            total += await self.redis_client._client.llen(queue_key)
        
        return total
    
    async def get_scheduled_count(self) -> int:
        """Get number of scheduled jobs."""
        await self._ensure_initialized()
        return await self.redis_client._client.zcard(self._scheduled_key())
    
    async def _process_scheduled_jobs(self) -> None:
        """Move due scheduled jobs to main queue."""
        scheduled_key = self._scheduled_key()
        now = time.time()
        
        # Get jobs due for execution
        due_jobs = await self.redis_client._client.zrangebyscore(
            scheduled_key,
            0,
            now
        )
        
        for job_id_bytes in due_jobs:
            job_id = job_id_bytes.decode() if isinstance(job_id_bytes, bytes) else job_id_bytes
            
            job_data = await self.redis_client.get(self._job_data_key(job_id))
            if not job_data:
                # Clean up orphaned entry
                await self.redis_client._client.zrem(scheduled_key, job_id)
                continue
            
            job = Job.from_dict(job_data)
            job.status = JobStatus.PENDING
            job.scheduled_at = None
            
            # Move to main queue
            await self._update_job(job)
            await self._enqueue_job(job)
            
            # Remove from scheduled set
            await self.redis_client._client.zrem(scheduled_key, job_id)
            
            logger.debug(f"Scheduled job moved to queue: {job_id}")
    
    async def _update_job(self, job: Job) -> None:
        """Update job data in Redis."""
        await self.redis_client.set(
            self._job_data_key(job.id),
            job.to_dict(),
            ttl=86400  # 24 hours
        )
    
    async def _move_to_dlq(self, job: Job) -> None:
        """Move failed job to dead letter queue."""
        dlq_key = self._dlq_key()
        await self.redis_client._client.lpush(dlq_key, job.id)
        
        # Keep DLQ size from growing too large
        await self.redis_client._client.ltrim(dlq_key, 0, 999)  # Keep last 1000
    
    async def process(
        self,
        timeout: float = 5.0,
        max_jobs: Optional[int] = None
    ) -> Any:
        """
        Process jobs from queue (generator).
        
        Args:
            timeout: Dequeue timeout in seconds
            max_jobs: Maximum number of jobs to process (None = infinite)
            
        Yields:
            Job instances to process
        """
        await self._ensure_initialized()
        
        self._processing = True
        jobs_processed = 0
        
        try:
            while self._processing:
                if max_jobs and jobs_processed >= max_jobs:
                    break
                
                job = await self.dequeue(timeout=timeout)
                if job:
                    yield job
                    jobs_processed += 1
                else:
                    # No jobs available, sleep briefly
                    await asyncio.sleep(0.1)
                    
        except asyncio.CancelledError:
            logger.info("Job processing cancelled")
            self._processing = False
            raise
    
    def stop_processing(self) -> None:
        """Stop processing jobs."""
        self._processing = False
        logger.info("Job processing stopped")