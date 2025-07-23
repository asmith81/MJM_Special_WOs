"""
Structured logging configuration for Work Order Matcher
Provides consistent logging across all modules with proper formatting and handlers
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

# Get project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

class ColoredFormatter(logging.Formatter):
    """Custom formatter with color coding for console output"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color for console output
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        return super().format(record)

class WorkOrderMatcherLogger:
    """Centralized logging configuration for Work Order Matcher"""
    
    _initialized = False
    _loggers = {}
    
    @classmethod
    def setup_logging(cls, 
                     log_level: str = 'INFO',
                     enable_file_logging: bool = True,
                     enable_console_logging: bool = True,
                     max_file_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5) -> None:
        """
        Set up structured logging for the entire application
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_file_logging: Whether to log to files
            enable_console_logging: Whether to log to console
            max_file_size: Maximum size of log files before rotation
            backup_count: Number of backup log files to keep
        """
        if cls._initialized:
            return
        
        # Create logs directory if it doesn't exist
        if enable_file_logging:
            try:
                os.makedirs(LOGS_DIR, exist_ok=True)
            except OSError as e:
                print(f"Warning: Could not create logs directory {LOGS_DIR}: {e}")
                print("File logging will be disabled")
                enable_file_logging = False
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handlers
        if enable_file_logging:
            # Main application log
            main_log_file = os.path.join(LOGS_DIR, 'wo_matcher.log')
            file_handler = logging.handlers.RotatingFileHandler(
                main_log_file, 
                maxBytes=max_file_size, 
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
            
            # Error-only log
            error_log_file = os.path.join(LOGS_DIR, 'wo_matcher_errors.log')
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setFormatter(file_formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
        
        # Console handler
        if enable_console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            root_logger.addHandler(console_handler)
        
        # Log startup message
        startup_logger = cls.get_logger('system')
        startup_logger.info(f"Logging system initialized - Level: {log_level}, File: {enable_file_logging}, Console: {enable_console_logging}")
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for a specific module
        
        Args:
            name: Logger name (usually module name)
            
        Returns:
            Logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(f'wo_matcher.{name}')
        
        return cls._loggers[name]
    
    @classmethod
    def log_api_call(cls, api_name: str, endpoint: str, duration: float, success: bool, details: Optional[str] = None):
        """Log API calls with consistent format"""
        logger = cls.get_logger('api')
        status = "SUCCESS" if success else "FAILED"
        message = f"{api_name} | {endpoint} | {duration:.2f}s | {status}"
        if details:
            message += f" | {details}"
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
    
    @classmethod
    def log_user_action(cls, action: str, details: Optional[str] = None, user_id: Optional[str] = None):
        """Log user actions for audit trail"""
        logger = cls.get_logger('user_actions')
        message = f"ACTION: {action}"
        if user_id:
            message += f" | USER: {user_id}"
        if details:
            message += f" | {details}"
        
        logger.info(message)
    
    @classmethod 
    def log_data_processing(cls, operation: str, count: int, duration: float, success: bool):
        """Log data processing operations"""
        logger = cls.get_logger('data')
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation} | {count} items | {duration:.2f}s | {status}"
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
    
    @classmethod
    def get_log_summary(cls) -> dict:
        """Get summary of log files and sizes with error handling"""
        try:
            if not os.path.exists(LOGS_DIR):
                return {"status": "No logs directory", "logs_directory": LOGS_DIR, "initialized": cls._initialized}
            
            log_files = {}
            try:
                for filename in os.listdir(LOGS_DIR):
                    if filename.endswith('.log'):
                        try:
                            filepath = os.path.join(LOGS_DIR, filename)
                            size = os.path.getsize(filepath)
                            modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                            log_files[filename] = {
                                "size_bytes": size,
                                "size_mb": round(size / (1024 * 1024), 2),
                                "last_modified": modified.strftime("%Y-%m-%d %H:%M:%S")
                            }
                        except (OSError, ValueError) as e:
                            # Skip files we can't read
                            log_files[filename] = {"error": f"Could not read file: {str(e)}"}
            except OSError as e:
                return {"status": f"Could not list directory: {str(e)}", "logs_directory": LOGS_DIR, "initialized": cls._initialized}
            
            return {
                "logs_directory": LOGS_DIR,
                "log_files": log_files,
                "initialized": cls._initialized
            }
        except Exception as e:
            return {"status": f"Error getting log summary: {str(e)}", "initialized": cls._initialized}

# Convenience function for quick setup
def setup_logging(log_level: str = 'INFO'):
    """Quick setup function for logging"""
    WorkOrderMatcherLogger.setup_logging(log_level=log_level)

# Convenience function to get logger
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return WorkOrderMatcherLogger.get_logger(name) 