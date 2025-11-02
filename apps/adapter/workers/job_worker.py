"""
Background job worker for processing asynchronous tasks.

This worker process:
- Processes jobs from Redis queue
- Handles workflow execution
- Sends emails
- Performs data cleanup
- Supports graceful shutdown
"""

import asyncio
import signal
import sys
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.queue import JobQueue, Job, JobPriority, JobStatus
from ..core.redis_client import get_redis_client
from ..core.database import get_db
from ..core.config import settings
from ..core.logging import get_logger
from ..core.exceptions import AdapterException


logger = get_logger(__name__)


class WorkerError(AdapterException):
    """Raised when worker encounters an error."""
    pass


class JobWorker:
    """
    Background job worker for processing tasks from Redis queue.
    
    Supported task types:
    - workflow.execute: Execute workflow asynchronously
    - email.send: Send email notifications
    - data.cleanup: Perform data cleanup tasks
    - cache.warm: Warm cache with frequently accessed data
    
    Example:
        ```python
        worker = JobWorker(queue_name="default")
        await worker.start()
        ```
    """
    
    def __init__(
        self,
        queue_name: str = "default",
        max_concurrent_jobs: int = 5,
        poll_interval: float = 1.0
    ):
        """
        Initialize job worker.
        
        Args:
            queue_name: Name of the queue to process
            max_concurrent_jobs: Maximum concurrent job executions
            poll_interval: Interval between queue polls in seconds
        """
        self.queue_name = queue_name
        self.max_concurrent_jobs = max_concurrent_jobs
        self.poll_interval = poll_interval
        
        self.queue: Optional[JobQueue] = None
        self.running = False
        self.active_jobs: Dict[str, asyncio.Task] = {}
        
        # Task handlers registry
        self.task_handlers: Dict[str, Callable[[Job], Awaitable[Any]]] = {
            "workflow.execute": self._handle_workflow_execution,
            "email.send": self._handle_email_send,
            "data.cleanup": self._handle_data_cleanup,
            "cache.warm": self._handle_cache_warm,
        }
        
        logger.info(
            f"Initialized JobWorker: {queue_name}",
            extra={
                "queue_name": queue_name,
                "max_concurrent_jobs": max_concurrent_jobs
            }
        )
    
    async def start(self) -> None:
        """Start the job worker."""
        logger.info("Starting job worker...")
        
        # Initialize Redis connection
        redis_client = await get_redis_client()
        
        # Initialize job queue
        self.queue = JobQueue(
            queue_name=self.queue_name,
            redis_client=redis_client
        )
        await self.queue._ensure_initialized()
        
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        logger.info("Job worker started successfully")
        
        # Start processing loop
        await self._process_loop()
    
    async def stop(self) -> None:
        """Stop the job worker gracefully."""
        if not self.running:
            return
        
        logger.info("Stopping job worker...")
        self.running = False
        
        # Wait for active jobs to complete (with timeout)
        if self.active_jobs:
            logger.info(f"Waiting for {len(self.active_jobs)} active jobs to complete...")
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_jobs.values(), return_exceptions=True),
                    timeout=30.0  # 30 second grace period
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for jobs to complete, cancelling...")
                for task in self.active_jobs.values():
                    task.cancel()
        
        logger.info("Job worker stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self.running:
            try:
                # Check if we can accept more jobs
                if len(self.active_jobs) >= self.max_concurrent_jobs:
                    # Wait for a job to complete
                    await asyncio.sleep(self.poll_interval)
                    continue
                
                # Dequeue next job
                job = await self.queue.dequeue(timeout=self.poll_interval)
                
                if job:
                    # Process job in background
                    task = asyncio.create_task(self._process_job(job))
                    self.active_jobs[job.id] = task
                    
                    # Cleanup completed tasks
                    self._cleanup_completed_tasks()
                else:
                    # No jobs available, brief sleep
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                logger.info("Processing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)  # Back off on error
    
    def _cleanup_completed_tasks(self) -> None:
        """Remove completed tasks from active jobs."""
        completed = [job_id for job_id, task in self.active_jobs.items() if task.done()]
        for job_id in completed:
            del self.active_jobs[job_id]
    
    async def _process_job(self, job: Job) -> None:
        """
        Process a single job.
        
        Args:
            job: Job to process
        """
        logger.info(
            f"Processing job: {job.id}",
            extra={
                "job_id": job.id,
                "task_name": job.task_name,
                "attempt": job.attempts
            }
        )
        
        try:
            # Get handler for task
            handler = self.task_handlers.get(job.task_name)
            
            if not handler:
                raise WorkerError(
                    message=f"Unknown task type: {job.task_name}",
                    details={"task_name": job.task_name}
                )
            
            # Execute handler
            result = await handler(job)
            
            # Mark job as completed
            await self.queue.complete(job.id, result)
            
            logger.info(
                f"Job completed: {job.id}",
                extra={
                    "job_id": job.id,
                    "task_name": job.task_name,
                    "duration_ms": int((datetime.now().timestamp() - job.started_at) * 1000) if job.started_at else 0
                }
            )
            
        except Exception as e:
            logger.error(
                f"Job failed: {job.id}",
                exc_info=e,
                extra={
                    "job_id": job.id,
                    "task_name": job.task_name,
                    "error": str(e)
                }
            )
            
            # Mark job as failed (will retry if possible)
            await self.queue.fail(job.id, str(e), retry=True)
    
    async def _handle_workflow_execution(self, job: Job) -> Dict[str, Any]:
        """
        Execute workflow asynchronously.
        
        Args:
            job: Job with workflow execution parameters
            
        Returns:
            Workflow execution result
        """
        from uuid import UUID
        from ..orchestration.engine import WorkflowEngine
        
        payload = job.payload
        workflow_id = UUID(payload["workflow_id"])
        tenant_id = UUID(payload["tenant_id"])
        input_data = payload.get("input_data", {})
        
        logger.info(
            f"Executing workflow: {workflow_id}",
            extra={
                "job_id": job.id,
                "workflow_id": str(workflow_id),
                "tenant_id": str(tenant_id)
            }
        )
        
        # Get database session
        async for db in get_db():
            try:
                # Create workflow engine
                engine = WorkflowEngine(db)
                
                # Execute workflow
                run = await engine.execute_workflow(
                    workflow_id=workflow_id,
                    tenant_id=tenant_id,
                    input_data=input_data,
                    emit_events=True
                )
                
                # Commit transaction
                await db.commit()
                
                return {
                    "run_id": str(run.id),
                    "status": run.status.value,
                    "execution_time_ms": run.execution_time_ms
                }
                
            except Exception as e:
                await db.rollback()
                raise
    
    async def _handle_email_send(self, job: Job) -> Dict[str, Any]:
        """
        Send email notification.
        
        Args:
            job: Job with email parameters
            
        Returns:
            Email send result
        """
        payload = job.payload
        to_email = payload["to"]
        subject = payload["subject"]
        body = payload.get("body", "")
        html_body = payload.get("html_body")
        
        logger.info(
            f"Sending email to: {to_email}",
            extra={
                "job_id": job.id,
                "to": to_email,
                "subject": subject
            }
        )
        
        # TODO: Integrate with email provider (SendGrid, SES, etc.)
        # For now, just log the email
        logger.info(
            f"Email sent (simulated): {to_email}",
            extra={
                "to": to_email,
                "subject": subject,
                "body_length": len(body)
            }
        )
        
        return {
            "sent": True,
            "to": to_email,
            "message_id": f"sim_{job.id}"
        }
    
    async def _handle_data_cleanup(self, job: Job) -> Dict[str, Any]:
        """
        Perform data cleanup tasks.
        
        Args:
            job: Job with cleanup parameters
            
        Returns:
            Cleanup result
        """
        from uuid import UUID
        from sqlalchemy import delete, select
        from ..models.action_log import ActionLog
        from ..models.workflow import WorkflowRun
        
        payload = job.payload
        cleanup_type = payload.get("type", "old_logs")
        days_old = payload.get("days_old", 90)
        tenant_id = payload.get("tenant_id")
        
        logger.info(
            f"Running data cleanup: {cleanup_type}",
            extra={
                "job_id": job.id,
                "cleanup_type": cleanup_type,
                "days_old": days_old
            }
        )
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        async for db in get_db():
            try:
                if cleanup_type == "old_logs":
                    # Delete old action logs
                    stmt = delete(ActionLog).where(
                        ActionLog.created_at < cutoff_date
                    )
                    if tenant_id:
                        stmt = stmt.where(ActionLog.tenant_id == UUID(tenant_id))
                    
                    result = await db.execute(stmt)
                    deleted_count = result.rowcount
                    
                elif cleanup_type == "old_workflow_runs":
                    # Delete old completed workflow runs
                    stmt = delete(WorkflowRun).where(
                        WorkflowRun.completed_at < cutoff_date
                    )
                    if tenant_id:
                        stmt = stmt.where(WorkflowRun.tenant_id == UUID(tenant_id))
                    
                    result = await db.execute(stmt)
                    deleted_count = result.rowcount
                
                await db.commit()
                
                logger.info(
                    f"Data cleanup completed: {deleted_count} records deleted",
                    extra={
                        "cleanup_type": cleanup_type,
                        "deleted_count": deleted_count
                    }
                )
                
                return {
                    "cleanup_type": cleanup_type,
                    "deleted_count": deleted_count
                }
                
            except Exception as e:
                await db.rollback()
                raise
    
    async def _handle_cache_warm(self, job: Job) -> Dict[str, Any]:
        """
        Warm cache with frequently accessed data.
        
        Args:
            job: Job with cache warming parameters
            
        Returns:
            Cache warming result
        """
        from ..services.cache import get_cache_service
        
        payload = job.payload
        cache_type = payload.get("type", "workflows")
        tenant_id = payload.get("tenant_id")
        
        logger.info(
            f"Warming cache: {cache_type}",
            extra={
                "job_id": job.id,
                "cache_type": cache_type
            }
        )
        
        cache = await get_cache_service()
        warmed_count = 0
        
        # TODO: Implement cache warming logic
        # Example: Pre-load frequently accessed workflows, configs, etc.
        
        logger.info(
            f"Cache warming completed",
            extra={
                "cache_type": cache_type,
                "warmed_count": warmed_count
            }
        )
        
        return {
            "cache_type": cache_type,
            "warmed_count": warmed_count
        }


async def main():
    """Main entry point for worker process."""
    logger.info("Starting Transform Army AI Job Worker")
    
    # Get queue name from environment or default
    queue_name = settings.environment.get("WORKER_QUEUE", "default")
    
    # Create and start worker
    worker = JobWorker(queue_name=queue_name)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await worker.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Job worker shutdown")