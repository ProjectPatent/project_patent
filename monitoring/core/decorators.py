# core/decorators.py
import functools
from typing import Callable, Any
from .metrics import IPRMetrics

def monitor_api_call(metrics: IPRMetrics):
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            endpoint = func.__name__
            method = kwargs.get('method', 'GET')
            
            with metrics.api_latency.labels(
                endpoint=endpoint,
                method=method
            ).time():
                try:
                    result = await func(*args, **kwargs)
                    metrics.api_requests.labels(
                        endpoint=endpoint,
                        method=method,
                        status='success'
                    ).inc()
                    return result
                except Exception as e:
                    metrics.api_requests.labels(
                        endpoint=endpoint,
                        method=method,
                        status='error'
                    ).inc()
                    metrics.errors.labels(
                        type=type(e).__name__,
                        endpoint=endpoint
                    ).inc()
                    raise
        return wrapper
    return decorator