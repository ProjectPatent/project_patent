# protocol_monitor.py
import pyshark
import logging
import asyncio
from typing import Optional, Callable, Any
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class ProtocolMonitorError(MonitoringError):
    """프로토콜 모니터링 관련 예외"""
    pass

class ProtocolMonitor:
    """특정 프로토콜 모니터링 클래스"""

    def __init__(
        self, 
        protocol: str, 
        interface: str,
        packet_handler: Optional[Callable[[Any], None]] = None
    ):
        self.protocol = protocol
        self.interface = interface
        self.packet_handler = packet_handler
        self.capture = None
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """프로토콜 모니터링 시작"""
        if self._running:
            raise ProtocolMonitorError("Monitor is already running")
            
        try:
            display_filter = self.protocol
            self.capture = pyshark.LiveCapture(
                interface=self.interface, 
                display_filter=display_filter
            )
            self._running = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info(
                f"Started monitoring protocol {self.protocol} "
                f"on interface {self.interface}"
            )
        except Exception as e:
            logger.error(f"Failed to start protocol monitor: {str(e)}", exc_info=True)
            raise ProtocolMonitorError("Failed to start protocol monitor") from e

    async def stop(self):
        """프로토콜 모니터링 중지"""
        if not self._running:
            return
            
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            
        if self.capture:
            self.capture.close()
            
        logger.info("Protocol monitoring stopped")

    async def _monitor_loop(self):
        """모니터링 메인 루프"""
        while self._running:
            try:
                for packet in self.capture.sniff_continuously():
                    if not self._running:
                        break
                    await self._process_packet(packet)
            except Exception as e:
                if self._running:
                    logger.error(f"Monitoring error: {str(e)}", exc_info=True)
                    await asyncio.sleep(1)  # 재시도 전 딜레이

    async def _process_packet(self, packet):
        """패킷 처리"""
        try:
            if self.packet_handler:
                await self.packet_handler(packet)
            else:
                logger.debug(f"Captured {self.protocol} packet: {packet}")
        except Exception as e:
            logger.error(f"Failed to process packet: {str(e)}", exc_info=True)