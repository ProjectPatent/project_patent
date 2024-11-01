# decorators.py
import functools
import time
from typing import Callable, Any, TypeVar, Optional
import logging
from .metrics import IPRMetrics
from .exceptions import MonitoringError

logger = logging.getLogger(__name__)
T = TypeVar('T')

def monitor_api_call(metrics: IPRMetrics, endpoint: Optional[str] = None):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            method = kwargs.get('method', 'GET')
            ep = endpoint or func.__name__
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics.increment_requests(ep, method, 'success')
                metrics.record_latency(ep, method, duration)
                
                return result
                
            except Exception as e:
                metrics.increment_requests(ep, method, 'error')
                metrics.record_error(type(e).__name__, ep)
                
                logger.error(
                    f"API call failed: {str(e)}",
                    extra={
                        "endpoint": ep,
                        "method": method,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator
