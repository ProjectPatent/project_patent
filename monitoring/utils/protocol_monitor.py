import pyshark
import logging

class ProtocolMonitor:
    """특정 프로토콜 모니터링 클래스"""

    def __init__(self, protocol: str, interface: str):
        """
        :param protocol: 모니터링할 프로토콜 (e.g., 'http', 'tcp')
        :param interface: 네트워크 인터페이스 이름 (e.g., 'eth0')
        """
        self.protocol = protocol
        self.interface = interface
        self.capture = None

    def monitor_protocol(self):
        """지정된 프로토콜에 대한 패킷을 실시간으로 모니터링합니다."""
        display_filter = self.protocol
        self.capture = pyshark.LiveCapture(interface=self.interface, display_filter=display_filter)
        logging.info(f"Started monitoring protocol {self.protocol} on interface {self.interface}")

        for packet in self.capture.sniff_continuously():
            self._process_packet(packet)

    def stop_monitoring(self):
        """프로토콜 모니터링을 중지합니다."""
        if self.capture:
            self.capture.close()
            logging.info("Protocol monitoring stopped.")

    def _process_packet(self, packet):
        """프로토콜 패킷을 처리합니다."""
        logging.info(f"Captured {self.protocol} packet: {packet}")
        # 프로토콜별 패킷을 분석하는 추가 로직을 여기에 작성할 수 있습니다.
