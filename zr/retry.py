from __future__ import annotations
import time
import random
from typing import Callable, TypeVar, Optional
from functools import wraps

T = TypeVar('T')


def exponential_backoff_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for exponential backoff retry with jitter.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Final attempt failed, raise
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    # Log retry attempt (if logger available in args/kwargs)
                    log = kwargs.get('log') or (args[0].log if hasattr(args[0], 'log') else None)
                    if log:
                        log.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator


def smart_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    log = None,
    error_msg: str = "Operation failed"
) -> Optional[T]:
    """
    Smart retry wrapper for functions without decorator.

    Returns None on final failure instead of raising exception.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if log:
                log.warning(f"{error_msg} (attempt {attempt + 1}/{max_retries}): {e}")

            if attempt == max_retries - 1:
                if log:
                    log.error(f"{error_msg} after {max_retries} attempts")
                return None

            # Exponential backoff
            delay = min(2 ** attempt, 30)
            time.sleep(delay)

    return None
