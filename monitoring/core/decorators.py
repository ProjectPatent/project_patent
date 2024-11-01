# monitoring/core/decorators.py

import functools
import time
from typing import Callable, Any, TypeVar, Optional
import logging
from .metrics import IPRMetrics
from .exceptions import MonitoringError

logger = logging.getLogger(__name__)
T = TypeVar('T')

def monitor_api_call(metrics: IPRMetrics, endpoint: Optional[str] = None):
    """
    API 호출 모니터링 데코레이터.
    
    이 데코레이터는 지정된 API 함수 호출의 성공 및 실패 요청 수, 
    응답 시간을 IPRMetrics 객체를 통해 기록하고, 오류가 발생한 경우 로깅합니다.
    
    Args:
        metrics (IPRMetrics): 메트릭 기록을 위한 IPRMetrics 객체.
        endpoint (Optional[str]): 엔드포인트 이름. 기본값은 함수 이름을 사용합니다.
    
    Returns:
        Callable[..., T]: API 함수를 래핑한 함수.
    """
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            """API 호출을 래핑하여 메트릭 기록 및 오류 처리를 수행하는 함수."""
            method = kwargs.get('method', 'GET')  # 기본 요청 메서드는 GET
            ep = endpoint or func.__name__  # 엔드포인트 이름을 함수 이름 또는 지정된 값으로 설정
            
            start_time = time.time()  # 호출 시작 시간 기록
            try:
                # 실제 API 함수 호출
                result = await func(*args, **kwargs)
                duration = time.time() - start_time  # 응답 시간 계산
                
                # 성공적인 요청 메트릭 기록
                metrics.increment_requests(ep, method, 'success')
                metrics.record_latency(ep, method, duration)
                
                return result
                
            except Exception as e:
                # 실패한 요청 메트릭 기록
                metrics.increment_requests(ep, method, 'error')
                metrics.record_error(type(e).__name__, ep)
                
                # 오류 로그 기록
                logger.error(
                    f"API call failed: {str(e)}",
                    extra={
                        "endpoint": ep,
                        "method": method,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise  # 예외 재발생
            
        return wrapper
    return decorator
