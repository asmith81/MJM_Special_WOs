"""
Thread management utilities for Work Order Matcher
Provides safe thread synchronization for GUI operations
"""

import threading
import queue
import time
from typing import Callable, Any, Optional, Dict
from functools import wraps
from utils.logging_config import get_logger

logger = get_logger('thread_manager')

class ThreadSafeCounter:
    """Thread-safe counter for tracking operations"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value
    
    def decrement(self) -> int:
        with self._lock:
            self._value -= 1
            return self._value
    
    @property
    def value(self) -> int:
        with self._lock:
            return self._value

class WorkerTask:
    """Represents a background task to be executed"""
    
    def __init__(self, task_id: str, func: Callable, args: tuple = (), kwargs: dict = None):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.cancelled = False
    
    def execute(self):
        """Execute the task"""
        if self.cancelled:
            logger.debug(f"Task {self.task_id} was cancelled before execution")
            return
        
        try:
            self.started_at = time.time()
            logger.debug(f"Starting task {self.task_id}")
            
            self.result = self.func(*self.args, **self.kwargs)
            
            self.completed_at = time.time()
            duration = self.completed_at - self.started_at
            logger.debug(f"Task {self.task_id} completed successfully in {duration:.2f}s")
            
        except Exception as e:
            self.error = e
            self.completed_at = time.time()
            duration = self.completed_at - (self.started_at or self.created_at)
            logger.error(f"Task {self.task_id} failed after {duration:.2f}s: {str(e)}")
    
    def cancel(self):
        """Cancel the task if not started"""
        if self.started_at is None:
            self.cancelled = True
            logger.debug(f"Task {self.task_id} cancelled")
            return True
        return False
    
    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None
    
    @property
    def is_successful(self) -> bool:
        return self.is_completed and self.error is None and not self.cancelled
    
    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

class ThreadManager:
    """Manages background threads and GUI synchronization"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self._active_tasks: Dict[str, WorkerTask] = {}
        self._result_queue = queue.Queue()
        self._task_lock = threading.Lock()
        self._active_threads = ThreadSafeCounter()
        self._shutdown = False
        
        logger.info(f"ThreadManager initialized with {max_workers} max workers")
    
    def submit_task(self, 
                   task_id: str, 
                   func: Callable, 
                   args: tuple = (), 
                   kwargs: dict = None,
                   on_success: Optional[Callable] = None,
                   on_error: Optional[Callable] = None,
                   on_complete: Optional[Callable] = None) -> bool:
        """
        Submit a task for background execution
        
        Args:
            task_id: Unique identifier for the task
            func: Function to execute
            args: Arguments for the function
            kwargs: Keyword arguments for the function
            on_success: Callback for successful completion
            on_error: Callback for errors
            on_complete: Callback for completion (success or error)
            
        Returns:
            True if task was submitted, False if rejected
        """
        if self._shutdown:
            logger.warning(f"Cannot submit task {task_id} - ThreadManager is shutting down")
            return False
        
        # Check if we're at capacity
        if self._active_threads.value >= self.max_workers:
            logger.warning(f"Cannot submit task {task_id} - at maximum capacity ({self.max_workers})")
            return False
        
        # Check if task ID already exists
        with self._task_lock:
            if task_id in self._active_tasks:
                existing_task = self._active_tasks[task_id]
                if not existing_task.is_completed:
                    logger.warning(f"Task {task_id} already running")
                    return False
        
        # Create and start task
        task = WorkerTask(task_id, func, args, kwargs)
        
        def worker():
            try:
                self._active_threads.increment()
                
                with self._task_lock:
                    self._active_tasks[task_id] = task
                
                # Execute the task
                task.execute()
                
                # Queue result for main thread processing
                self._result_queue.put({
                    'task_id': task_id,
                    'task': task,
                    'on_success': on_success,
                    'on_error': on_error,
                    'on_complete': on_complete
                })
                
            finally:
                self._active_threads.decrement()
        
        thread = threading.Thread(target=worker, name=f"WorkerTask-{task_id}", daemon=True)
        thread.start()
        
        logger.info(f"Submitted task {task_id} for background execution")
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        with self._task_lock:
            if task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                return task.cancel()
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        with self._task_lock:
            if task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                return {
                    'task_id': task_id,
                    'is_completed': task.is_completed,
                    'is_successful': task.is_successful,
                    'cancelled': task.cancelled,
                    'duration': task.duration,
                    'error': str(task.error) if task.error else None
                }
        return None
    
    def process_completed_tasks(self) -> int:
        """
        Process completed tasks and execute callbacks
        Should be called from the main GUI thread
        
        Returns:
            Number of tasks processed
        """
        processed = 0
        
        try:
            while True:
                try:
                    result = self._result_queue.get_nowait()
                    task = result['task']
                    
                    logger.debug(f"Processing completed task {result['task_id']}")
                    
                    try:
                        if task.is_successful and result['on_success']:
                            result['on_success'](task.result)
                        elif task.error and result['on_error']:
                            result['on_error'](task.error)
                        
                        if result['on_complete']:
                            result['on_complete'](task)
                    
                    except Exception as e:
                        logger.error(f"Error in callback for task {result['task_id']}: {str(e)}")
                    
                    processed += 1
                    
                except queue.Empty:
                    break
                    
        except Exception as e:
            logger.error(f"Error processing completed tasks: {str(e)}")
        
        return processed
    
    def get_stats(self) -> Dict[str, Any]:
        """Get thread manager statistics"""
        with self._task_lock:
            active_count = len([t for t in self._active_tasks.values() if not t.is_completed])
            completed_count = len([t for t in self._active_tasks.values() if t.is_completed])
            successful_count = len([t for t in self._active_tasks.values() if t.is_successful])
            failed_count = len([t for t in self._active_tasks.values() if t.error is not None])
        
        return {
            'max_workers': self.max_workers,
            'active_threads': self._active_threads.value,
            'active_tasks': active_count,
            'completed_tasks': completed_count,
            'successful_tasks': successful_count,
            'failed_tasks': failed_count,
            'pending_results': self._result_queue.qsize(),
            'shutdown': self._shutdown
        }
    
    def shutdown(self, timeout: float = 5.0):
        """Shutdown the thread manager"""
        logger.info("Shutting down ThreadManager...")
        self._shutdown = True
        
        # Wait for active threads to complete
        start_time = time.time()
        while self._active_threads.value > 0 and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if self._active_threads.value > 0:
            logger.warning(f"ThreadManager shutdown with {self._active_threads.value} active threads still running")
        else:
            logger.info("ThreadManager shutdown completed successfully")

# Decorator for GUI-safe operations
def gui_safe(func):
    """Decorator to ensure function runs on main GUI thread"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # In a real implementation, you'd check if we're on the main thread
        # and use root.after() to schedule the call if not
        return func(*args, **kwargs)
    return wrapper

# Global thread manager instance
_thread_manager: Optional[ThreadManager] = None

def get_thread_manager() -> ThreadManager:
    """Get the global thread manager instance"""
    global _thread_manager
    if _thread_manager is None:
        try:
            from utils.config import Config
            max_workers = getattr(Config, 'MAX_CONCURRENT_OPERATIONS', 3)
        except (ImportError, AttributeError):
            # Fallback if config can't be loaded
            max_workers = 3
        
        _thread_manager = ThreadManager(max_workers=max_workers)
    return _thread_manager

def shutdown_thread_manager():
    """Shutdown the global thread manager"""
    global _thread_manager
    if _thread_manager:
        _thread_manager.shutdown()
        _thread_manager = None 