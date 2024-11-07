# monitoring/core/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from .metrics import IPRMetrics
from .config import MonitoringConfig
from .exceptions import MonitoringError

# 로거 설정 
logger = logging.getLogger(__name__)

class BaseMonitor(ABC):
    """
    모니터링 기본 클래스
    
    어떤 클래스든 기본적으로 이 클래스를 상속받게 될 예정이며, start, stop, check_health 메서드를 구현해야 합니다.
    모니터의 관리와 상태 조회 기능을 제공하는 기본 클래스입니다.
    """
    
    def __init__(
        self,
        metrics: IPRMetrics,
        config: MonitoringConfig
    ):
        """
        BaseMonitor 초기화 메서드

        Parameters:
            metrics (IPRMetrics): 모니터링할 메트릭 객체.
            config (MonitoringConfig): 모니터링 설정 객체.
        """
        self.metrics = metrics                # 메트릭 객체를 통해 모니터링 데이터를 기록 및 관리
        self.config = config                  # 모니터 설정을 저장
        self._running = False                 # 모니터가 실행 중인지 여부를 나타내는 플래그
        self._start_time: Optional[datetime] = None  # 모니터 시작 시간
        logger.info(f"Initializing {self.__class__.__name__}")  # 초기화 로그
        
    @abstractmethod
    async def start(self):
        """
        모니터링 시작 메서드
        
        모니터링을 시작하고 _running 플래그를 True로 설정합니다.
        이미 실행 중일 경우 MonitoringError 예외를 발생시킵니다.
        """
        if self._running:
            raise MonitoringError("Monitor is already running")  # 실행 중인 경우 에러 발생
        self._running = True
        self._start_time = datetime.now(timezone.utc)  # 현재 시간을 시작 시간으로 설정 (timezone-aware)
        logger.info(f"{self.__class__.__name__} started")  # 시작 로그
        
    @abstractmethod
    async def stop(self):
        """
        모니터링 중지 메서드
        
        모니터링을 중지하고 _running 플래그를 False로 설정합니다.
        실행 중이지 않다면 MonitoringError 예외를 발생시킵니다.
        """
        if not self._running:
            raise MonitoringError("Monitor is not running")  # 실행 중이 아닌 경우 에러 발생
        self._running = False
        logger.info(f"{self.__class__.__name__} stopped")  # 중지 로그
        
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """
        상태 체크 메서드.
        
        모니터링 시스템의 현재 상태 정보를 딕셔너리 형태로 반환합니다.
        이 메서드는 각 모니터링 클래스에서 구체적으로 구현해야 합니다.
        
        Returns:
            Dict[str, Any]: 모니터링 상태 정보.
        """
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """
        모니터 상태 정보 반환 메서드.
        
        현재 모니터의 실행 상태, 시작 시간, 실행 시간을 포함한 상태 정보를 반환합니다.
        
        Returns:
            Dict[str, Any]: 모니터 상태 정보 딕셔너리.
        """
        uptime = (
            (datetime.now(timezone.utc) - self._start_time).total_seconds()
            if self._start_time else 0
        )
        return {
            "running": self._running,                                     # 모니터 실행 중 여부
            "start_time": self._start_time.isoformat() if self._start_time else None,  # 모니터 시작 시간
            "uptime_seconds": uptime                                      # 모니터가 실행된 총 시간(초)
        }