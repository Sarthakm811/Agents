"""
Background Task Manager for Hybrid AI Research System.

This module provides asynchronous background task management for long-running
research operations. It handles task lifecycle, progress tracking, and error handling.

**Feature: ai-research-agents**
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**
"""

import asyncio
import logging
from asyncio import Task
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Status values for background tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(str, Enum):
    """Status values for research stages."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageProgress:
    """Tracks progress of a single research stage."""
    name: str
    status: StageStatus = StageStatus.PENDING
    progress: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


@dataclass
class TaskState:
    """Tracks the state of a background research task."""
    session_id: str
    status: TaskStatus = TaskStatus.PENDING
    stages: Dict[str, StageProgress] = field(default_factory=dict)
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    task: Optional[Task] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Initialize default stages if not provided."""
        if not self.stages:
            stage_names = [
                "literature_review",
                "gap_analysis",
                "hypothesis_generation",
                "methodology",
                "writing"
            ]
            self.stages = {name: StageProgress(name=name) for name in stage_names}


class BackgroundTaskManager:
    """
    Manages background tasks for research sessions.
    
    This class handles:
    - Starting research tasks as asyncio background tasks
    - Tracking progress via callbacks
    - Handling task completion and errors
    - Cancelling running tasks
    
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """
    
    # Valid stage status transitions
    VALID_TRANSITIONS = {
        StageStatus.PENDING: {StageStatus.RUNNING, StageStatus.FAILED},
        StageStatus.RUNNING: {StageStatus.COMPLETED, StageStatus.FAILED},
        StageStatus.COMPLETED: set(),  # Terminal state
        StageStatus.FAILED: set(),  # Terminal state
    }
    
    def __init__(self):
        """Initialize the background task manager."""
        self._tasks: Dict[str, TaskState] = {}
        self._lock = asyncio.Lock()
    
    def _validate_stage_transition(
        self, 
        current: StageStatus, 
        new: StageStatus
    ) -> bool:
        """
        Validate that a stage status transition is allowed.
        
        Status transitions must follow: pending → running → completed|failed
        
        **Validates: Requirements 4.2**
        """
        return new in self.VALID_TRANSITIONS.get(current, set())
    
    def _validate_progress_monotonic(
        self, 
        current_progress: int, 
        new_progress: int
    ) -> bool:
        """
        Validate that progress is monotonically increasing.
        
        Progress values must never decrease.
        
        **Validates: Requirements 4.2**
        """
        return new_progress >= current_progress
    
    async def start_research_task(
        self,
        session_id: str,
        research_swarm: Any,
        topic: Any,
        on_progress: Optional[Callable[[str, str, int], None]] = None,
        on_complete: Optional[Callable[[str, Dict], None]] = None,
        on_error: Optional[Callable[[str, str], None]] = None
    ) -> Task:
        """
        Start a background research task.
        
        Spawns an asyncio task to execute the research pipeline asynchronously.
        Progress, completion, and error callbacks are invoked as the task progresses.
        
        Parameters
        ----------
        session_id : str
            Unique identifier for the research session.
        research_swarm : AgenticResearchSwarm
            The research swarm instance to execute.
        topic : ResearchTopic
            The research topic to investigate.
        on_progress : Optional[Callable[[str, str, int], None]]
            Callback for progress updates (session_id, stage_name, progress).
        on_complete : Optional[Callable[[str, Dict], None]]
            Callback when task completes (session_id, results).
        on_error : Optional[Callable[[str, str], None]]
            Callback when task fails (session_id, error_message).
            
        Returns
        -------
        Task
            The asyncio Task object for the background task.
            
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        """
        async with self._lock:
            # Create task state
            task_state = TaskState(session_id=session_id)
            task_state.status = TaskStatus.RUNNING
            task_state.updated_at = datetime.now()
            
            # Create the async task
            task = asyncio.create_task(
                self._execute_research(
                    session_id,
                    research_swarm,
                    topic,
                    on_progress,
                    on_complete,
                    on_error
                )
            )
            
            task_state.task = task
            self._tasks[session_id] = task_state
            
            logger.info(f"Started background task for session: {session_id}")
            return task
    
    async def _execute_research(
        self,
        session_id: str,
        research_swarm: Any,
        topic: Any,
        on_progress: Optional[Callable[[str, str, int], None]],
        on_complete: Optional[Callable[[str, Dict], None]],
        on_error: Optional[Callable[[str, str], None]]
    ) -> None:
        """
        Execute the research pipeline with progress tracking.
        
        This method wraps the research swarm execution and handles:
        - Progress callback forwarding
        - Error handling and reporting
        - Task state updates
        
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        """
        try:
            # Create progress callback wrapper
            def progress_callback(stage_name: str, progress: int) -> None:
                self._update_stage_progress(session_id, stage_name, progress)
                if on_progress:
                    on_progress(session_id, stage_name, progress)
            
            # Execute the research pipeline
            results = await research_swarm.execute_pipeline(
                topic,
                progress_callback=progress_callback
            )
            
            # Update task state on completion
            async with self._lock:
                if session_id in self._tasks:
                    task_state = self._tasks[session_id]
                    task_state.status = TaskStatus.COMPLETED
                    task_state.result = results
                    task_state.updated_at = datetime.now()
            
            logger.info(f"Research task completed for session: {session_id}")
            
            if on_complete:
                on_complete(session_id, results)
                
        except asyncio.CancelledError:
            # Handle task cancellation
            async with self._lock:
                if session_id in self._tasks:
                    task_state = self._tasks[session_id]
                    task_state.status = TaskStatus.CANCELLED
                    task_state.error_message = "Task was cancelled"
                    task_state.updated_at = datetime.now()
            
            logger.info(f"Research task cancelled for session: {session_id}")
            raise
            
        except Exception as e:
            # Handle task failure
            error_message = str(e) if str(e) else "An unexpected error occurred"
            
            async with self._lock:
                if session_id in self._tasks:
                    task_state = self._tasks[session_id]
                    task_state.status = TaskStatus.FAILED
                    task_state.error_message = error_message
                    task_state.updated_at = datetime.now()
            
            logger.error(f"Research task failed for session {session_id}: {error_message}")
            
            if on_error:
                on_error(session_id, error_message)
    
    def _update_stage_progress(
        self, 
        session_id: str, 
        stage_name: str, 
        progress: int
    ) -> None:
        """
        Update the progress of a research stage.
        
        Ensures progress is monotonically increasing and status transitions
        follow the valid sequence: pending → running → completed|failed.
        
        **Validates: Requirements 4.2, 4.3**
        """
        if session_id not in self._tasks:
            return
        
        task_state = self._tasks[session_id]
        
        if stage_name not in task_state.stages:
            task_state.stages[stage_name] = StageProgress(name=stage_name)
        
        stage = task_state.stages[stage_name]
        
        # Validate monotonic progress
        if not self._validate_progress_monotonic(stage.progress, progress):
            logger.warning(
                f"Non-monotonic progress update ignored: {stage.progress} -> {progress}"
            )
            return
        
        # Update progress
        stage.progress = progress
        task_state.updated_at = datetime.now()
        
        # Update status based on progress
        if progress == 0 and stage.status == StageStatus.PENDING:
            if self._validate_stage_transition(stage.status, StageStatus.RUNNING):
                stage.status = StageStatus.RUNNING
                stage.started_at = datetime.now()
        elif progress == 100 and stage.status == StageStatus.RUNNING:
            if self._validate_stage_transition(stage.status, StageStatus.COMPLETED):
                stage.status = StageStatus.COMPLETED
                stage.completed_at = datetime.now()
    
    def cancel_task(self, session_id: str) -> bool:
        """
        Cancel a running background task.
        
        Parameters
        ----------
        session_id : str
            The session ID of the task to cancel.
            
        Returns
        -------
        bool
            True if the task was cancelled, False if not found or not running.
            
        **Validates: Requirements 4.5**
        """
        if session_id not in self._tasks:
            return False
        
        task_state = self._tasks[session_id]
        
        if task_state.task is None:
            return False
        
        if task_state.task.done():
            return False
        
        task_state.task.cancel()
        logger.info(f"Cancelled task for session: {session_id}")
        return True
    
    def get_running_tasks(self) -> List[str]:
        """
        Get list of currently running task session IDs.
        
        Returns
        -------
        List[str]
            List of session IDs with running tasks.
        """
        return [
            session_id 
            for session_id, state in self._tasks.items()
            if state.status == TaskStatus.RUNNING
        ]
    
    def get_task_state(self, session_id: str) -> Optional[TaskState]:
        """
        Get the current state of a task.
        
        Parameters
        ----------
        session_id : str
            The session ID to look up.
            
        Returns
        -------
        Optional[TaskState]
            The task state if found, None otherwise.
        """
        return self._tasks.get(session_id)
    
    def get_stage_progress(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get progress information for all stages of a task.
        
        Parameters
        ----------
        session_id : str
            The session ID to look up.
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            Dictionary mapping stage names to their progress info.
        """
        if session_id not in self._tasks:
            return {}
        
        task_state = self._tasks[session_id]
        return {
            name: stage.to_dict() 
            for name, stage in task_state.stages.items()
        }
    
    async def mark_interrupted_sessions_failed(self) -> List[str]:
        """
        Mark any interrupted sessions as failed.
        
        This should be called on backend restart to handle sessions
        that were running when the backend stopped.
        
        Returns
        -------
        List[str]
            List of session IDs that were marked as failed.
            
        **Validates: Requirements 4.5**
        """
        marked_sessions = []
        
        async with self._lock:
            for session_id, task_state in self._tasks.items():
                if task_state.status == TaskStatus.RUNNING:
                    task_state.status = TaskStatus.FAILED
                    task_state.error_message = "Session interrupted due to backend restart"
                    task_state.updated_at = datetime.now()
                    marked_sessions.append(session_id)
                    logger.warning(f"Marked interrupted session as failed: {session_id}")
        
        return marked_sessions
