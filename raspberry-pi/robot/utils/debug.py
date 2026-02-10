from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


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
            self.level = LogLevel.INFO  # Default level
            self._load_config()
            self._initialized = True

    def _load_config(self):
        """Load global log level from first line of .env file"""
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            with open(env_file, "r") as f:
                first_line = f.readline().strip()
                if "=" in first_line:
                    key, value = first_line.split("=", 1)
                    if key.strip() == "DEBUG_LEVEL":
                        try:
                            self.level = LogLevel[value.strip().upper()]
                        except KeyError:
                            pass

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged"""
        return level.value <= self.level.value

    def _log(self, level: LogLevel, module: str, message: str):
        """Internal logging method"""
        if self._should_log(level):
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] [{level.name}] [{module}] {message}")

    def error(self, module: str, message: str):
        self._log(LogLevel.ERROR, module, message)

    def warning(self, module: str, message: str):
        self._log(LogLevel.WARNING, module, message)

    def warn(self, module: str, message: str):
        self.warning(module, message)

    def info(self, module: str, message: str):
        self._log(LogLevel.INFO, module, message)

    def debug(self, module: str, message: str):
        self._log(LogLevel.DEBUG, module, message)

    def verbose(self, module: str, message: str):
        self._log(LogLevel.VERBOSE, module, message)


# Global instance
debug = DebugLogger()


# Module-specific logger class
class ModuleLogger:
    def __init__(self, module_name: str):
        self.module_name = module_name

    def error(self, message: str):
        debug.error(self.module_name, message)

    def warning(self, message: str):
        debug.warning(self.module_name, message)

    def warn(self, message: str):
        debug.warning(self.module_name, message)

    def info(self, message: str):
        debug.info(self.module_name, message)

    def debug(self, message: str):
        debug.debug(self.module_name, message)

    def verbose(self, message: str):
        debug.verbose(self.module_name, message)


def get_logger(module_name: str) -> ModuleLogger:
    """Get a module-specific logger"""
    return ModuleLogger(module_name)
