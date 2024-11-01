# traffic_capture.py
import pyshark
import logging
import asyncio
from typing import Optional, Callable, Any
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class TrafficCaptureError(MonitoringError):
    """트래픽 캡처 관련 예외"""
    pass

class TrafficCapture:
    """트래픽 캡처 및 필터링"""

    def __init__(
        self,
        interface: str,
        bpf_filter: Optional[str] = None,
        packet_handler: Optional[Callable[[Any], None]] = None
    ):
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.packet_handler = packet_handler
        self.capture = None
        self._running = False
        self._capture_task: Optional[asyncio.Task] = None

    async def start(self):
        """캡처 시작"""
        if self._running:
            raise TrafficCaptureError("Capture is already running")
            
        try:
            self.capture = pyshark.LiveCapture(
                interface=self.interface,
                bpf_filter=self.bpf_filter
            )
            self._running = True
            self._capture_task = asyncio.create_task(self._capture_loop())
            logger.info(
                f"Started traffic capture on interface {self.interface} "
                f"with filter: {self.bpf_filter}"
            )
        except Exception as e:
            logger.error(f"Failed to start traffic capture: {str(e)}", exc_info=True)
            raise TrafficCaptureError("Failed to start traffic capture") from e

    async def stop(self):
        """캡처 중지"""
        if not self._running:
            return
            
        self._running = False
        if self._capture_task:
            self._capture_task.cancel()
            try:
                await self._capture_task
            except asyncio.CancelledError:
                pass
            
        if self.capture:
            self.capture.close()
            
        logger.info("Traffic capture stopped")

    async def _capture_loop(self):
        """캡처 메인 루프"""
        while self._running:
            try:
                for packet in self.capture.sniff_continuously():
                    if not self._running:
                        break
                    await self._process_packet(packet)
            except Exception as e:
                if self._running:
                    logger.error(f"Capture error: {str(e)}", exc_info=True)
                    await asyncio.sleep(1)

    async def _process_packet(self, packet):
        """패킷 처리"""
        try:
            if self.packet_handler:
                await self.packet_handler(packet)
            else:
                logger.debug(f"Captured packet: {packet}")
        except Exception as e:
            logger.error(f"Failed to process packet: {str(e)}", exc_info=True)