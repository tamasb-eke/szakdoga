import functools
from typing import Any, Callable, Union, Type, Tuple, TypeVar, ParamSpec
P = ParamSpec("P")
R = TypeVar("R")

def safe_operation(
      default_return: Any = None, 
      exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception, 
      log_error: bool = True
   ):
   """
   Decorator to handle errors automatically with logging.

   Args:
      default_return: Value to return when error occurs (default: None)
      exceptions: Exception type(s) to catch (default: Exception)
      log_error: Whether to log error (default: True)
   """
   from scripts.logger.logger import get_logger
   logger = get_logger(__name__)
   
   def decorator(func: Callable[P, R]) -> Callable[P, Union[R, Any]]:
      @functools.wraps(func)
      def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[R, Any]:
         try:
            return func(*args, **kwargs)
         except exceptions as e:
            error_msg = f"Error in {func.__name__}: {e}"
            if log_error:
               logger.error(error_msg)
            return default_return 
      return wrapper
   return decorator