import pyshark
import logging
from typing import Optional

class TrafficCapture:
    """트래픽 캡처 및 필터링 클래스"""

    def __init__(self, interface: str, bpf_filter: Optional[str] = None):
        """
        :param interface: 네트워크 인터페이스 이름 (e.g., 'eth0')
        :param bpf_filter: Berkeley Packet Filter (BPF) 문자열 필터 (옵션)
        """
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.capture = None

    def start_capture(self):
        """캡처를 시작하고 실시간으로 패킷을 처리합니다."""
        self.capture = pyshark.LiveCapture(interface=self.interface, bpf_filter=self.bpf_filter)
        logging.info(f"Started traffic capture on interface {self.interface} with filter: {self.bpf_filter}")
        
        for packet in self.capture.sniff_continuously():
            self._process_packet(packet)

    def stop_capture(self):
        """캡처를 중지합니다."""
        if self.capture:
            self.capture.close()
            logging.info("Traffic capture stopped.")

    def _process_packet(self, packet):
        """패킷을 처리합니다 (필요 시 오버라이드 가능)."""
        logging.info(f"Captured packet: {packet}")
        # 여기에서 추가적인 처리 또는 분석을 수행할 수 있습니다.
