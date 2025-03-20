"""Logging utilities for the MCP server."""

import json
import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast

import structlog
from pythonjsonlogger import jsonlogger

# Type variable for function return types
T = TypeVar("T")

# Create standard logger
stdlogger = logging.getLogger(__name__)


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """Configure logging - standard to console, optional structured JSON to file."""
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up console logging
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(numeric_level)

    # Set up structured JSON logging if file specified
    if log_file:
        # Create directory if needed
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        # Configure JSON file handler
        json_handler = logging.FileHandler(log_file)
        json_formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(module)s %(funcName)s %(message)s",
            timestamp=True,
        )
        json_handler.setFormatter(json_formatter)

        # Create separate logger for structured logs
        struct_root = logging.getLogger("structured")
        struct_root.propagate = False
        struct_root.addHandler(json_handler)
        struct_root.setLevel(numeric_level)

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        stdlogger.info(
            f"Logging initialized: console={log_level}, JSON file={log_file}"
        )
    else:
        stdlogger.info(f"Logging initialized: console={log_level}")


def log_function_call(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to log function calls with parameters, timing, and results."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        func_name = func.__name__
        module_name = func.__module__

        # Prepare parameters for logging
        log_params = {}

        # Handle method calls (skip self/cls)
        if (
            args
            and hasattr(args[0], "__class__")
            and args[0].__class__.__module__ != "builtins"
        ):
            log_params.update(
                {
                    k: v
                    for k, v in zip(func.__code__.co_varnames[1 : len(args)], args[1:])
                }
            )
        else:
            log_params.update(
                {k: v for k, v in zip(func.__code__.co_varnames[: len(args)], args)}
            )

        # Add keyword arguments
        log_params.update(kwargs)

        # Convert Path objects to strings
        for k, v in log_params.items():
            if isinstance(v, Path):
                log_params[k] = str(v)

        # Check if structured logging is enabled
        has_structured = logging.getLogger("structured").handlers

        # Log function call
        if has_structured:
            structlogger = structlog.get_logger(module_name)
            structlogger.debug(
                f"Calling {func_name}", function=func_name, parameters=log_params
            )

        stdlogger.debug(
            f"Calling {func_name} with parameters: {json.dumps(log_params, default=str)}"
        )

        # Execute function and measure time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # Handle large results
            result_for_log = result
            if isinstance(result, (list, dict)) and len(str(result)) > 1000:
                result_for_log = f"<Large result of type {type(result).__name__}, length: {len(str(result))}>"

            # Log completion
            if has_structured:
                structlogger.debug(
                    f"{func_name} completed",
                    function=func_name,
                    execution_time_ms=elapsed_ms,
                    status="success",
                    result=result_for_log,
                )

            stdlogger.debug(
                f"{func_name} completed in {elapsed_ms}ms with result: {result_for_log}"
            )
            return result

        except Exception as e:
            # Log exceptions
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            if has_structured:
                structlogger = structlog.get_logger(module_name)
                structlogger.error(
                    f"{func_name} failed",
                    function=func_name,
                    execution_time_ms=elapsed_ms,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                )

            stdlogger.error(
                f"{func_name} failed after {elapsed_ms}ms with error: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

    return cast(Callable[..., T], wrapper)
