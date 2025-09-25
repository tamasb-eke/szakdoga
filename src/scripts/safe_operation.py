import functools
from typing import Any, Callable, Union, Type, Tuple


def safe_operation(default_return: Any = None, exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception, log_error: bool = True):
   """
   Decorator to handle errors automatically with logging.

   Args:
      default_return: Value to return when error occurs (default: None)
      exceptions: Exception type(s) to catch (default: Exception)
      log_error: Whether to log error (default: True)
   """

   def decorator(func: Callable) -> Callable:
      @functools.wraps(func)
      def wrapper(*args, **kwargs):
         try:
            return func(*args, **kwargs)
         except exceptions as e:
            error_msg = f"Error in {func.__name__}: {e}"
            if log_error:
               from scripts.logger.logger import get_logger
               logger = get_logger(__name__)
               logger.error(error_msg)
            return default_return
      return wrapper
   return decorator