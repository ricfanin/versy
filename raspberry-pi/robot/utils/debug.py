import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class LogLevel(Enum):
    ERROR = 0
    WARNING = 1
    INFO = 2
    DEBUG = 3
    VERBOSE = 4


class DebugLogger:
    _instance: Optional["DebugLogger"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Read from environment or default to INFO
            level_name = os.getenv("DEBUG_LEVEL", "INFO").upper()
            try:
                self.level = LogLevel[level_name]
            except KeyError:
                self.level = LogLevel.INFO
                print(
                    f"Warning: Invalid DEBUG_LEVEL '{level_name}', defaulting to INFO"
                )

            # Configuration options
            self.show_timestamp = os.getenv("DEBUG_TIMESTAMP", "true").lower() == "true"
            self.show_module = os.getenv("DEBUG_MODULE", "true").lower() == "true"
            self.log_to_file = os.getenv("DEBUG_TO_FILE", "false").lower() == "true"
            self.log_file_path = os.getenv("DEBUG_FILE_PATH", "debug.log")

            # Module-specific levels
            self.module_levels: Dict[str, LogLevel] = {}
            module_config = os.getenv("DEBUG_MODULE_LEVELS", "")
            if module_config:
                # Format: module1:DEBUG,module2:ERROR
                for pair in module_config.split(","):
                    if ":" in pair:
                        module, level_str = pair.split(":", 1)
                        try:
                            self.module_levels[module.strip()] = LogLevel[
                                level_str.strip().upper()
                            ]
                        except KeyError:
                            pass

            self._initialized = True

            # Log initialization
            self.info("debug", f"Debug system initialized with level {self.level.name}")

    def _get_effective_level(self, module: str) -> LogLevel:
        """Get the effective log level for a specific module"""
        for module_pattern, level in self.module_levels.items():
            if module.startswith(module_pattern):
                return level
        return self.level

    def _should_log(self, level: LogLevel, module: str) -> bool:
        """Check if message should be logged based on level and module"""
        effective_level = self._get_effective_level(module)
        return level.value <= effective_level.value

    def _format_message(self, level: LogLevel, module: str, message: str) -> str:
        """Format the log message"""
        parts = []

        if self.show_timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[
                :-3
            ]  # Include milliseconds
            parts.append(f"[{timestamp}]")

        parts.append(f"[{level.name}]")

        if self.show_module:
            parts.append(f"[{module}]")

        parts.append(message)

        return " ".join(parts)

    def _log(self, level: LogLevel, module: str, message: str, **kwargs):
        """Internal logging method"""
        if self._should_log(level, module):
            formatted_message = self._format_message(level, module, message)

            # Console output
            print(formatted_message)

            # File output (if enabled)
            if self.log_to_file:
                try:
                    with open(self.log_file_path, "a", encoding="utf-8") as f:
                        f.write(formatted_message + "\n")
                except IOError:
                    pass  # Silently fail file logging to avoid breaking the program

    def error(self, module: str, message: str, **kwargs):
        """Log error message"""
        self._log(LogLevel.ERROR, module, message, **kwargs)

    def warning(self, module: str, message: str, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, module, message, **kwargs)

    def warn(self, module: str, message: str, **kwargs):
        """Alias for warning"""
        self.warning(module, message, **kwargs)

    def info(self, module: str, message: str, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, module, message, **kwargs)

    def debug(self, module: str, message: str, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, module, message, **kwargs)

    def verbose(self, module: str, message: str, **kwargs):
        """Log verbose message"""
        self._log(LogLevel.VERBOSE, module, message, **kwargs)

    def set_level(self, level: LogLevel):
        """Dynamically change the global log level"""
        self.level = level
        self.info("debug", f"Log level changed to {level.name}")

    def set_module_level(self, module: str, level: LogLevel):
        """Set log level for a specific module"""
        self.module_levels[module] = level
        self.info("debug", f"Module {module} log level set to {level.name}")


# Global instance
debug = DebugLogger()


# Convenience functions for easier usage
def log_error(module: str, message: str, **kwargs):
    """Log error message"""
    debug.error(module, message, **kwargs)


def log_warning(module: str, message: str, **kwargs):
    """Log warning message"""
    debug.warning(module, message, **kwargs)


def log_info(module: str, message: str, **kwargs):
    """Log info message"""
    debug.info(module, message, **kwargs)


def log_debug(module: str, message: str, **kwargs):
    """Log debug message"""
    debug.debug(module, message, **kwargs)


def log_verbose(module: str, message: str, **kwargs):
    """Log verbose message"""
    debug.verbose(module, message, **kwargs)


# Module-specific logger class for cleaner usage
class ModuleLogger:
    """Logger for a specific module"""

    def __init__(self, module_name: str):
        self.module_name = module_name

    def error(self, message: str, **kwargs):
        debug.error(self.module_name, message, **kwargs)

    def warning(self, message: str, **kwargs):
        debug.warning(self.module_name, message, **kwargs)

    def warn(self, message: str, **kwargs):
        debug.warning(self.module_name, message, **kwargs)

    def info(self, message: str, **kwargs):
        debug.info(self.module_name, message, **kwargs)

    def debug(self, message: str, **kwargs):
        debug.debug(self.module_name, message, **kwargs)

    def verbose(self, message: str, **kwargs):
        debug.verbose(self.module_name, message, **kwargs)


def get_logger(module_name: str) -> ModuleLogger:
    """Get a module-specific logger"""
    return ModuleLogger(module_name)
