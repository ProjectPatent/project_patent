# packet_parser.py
from typing import Any, Dict, Optional
import logging
from ..core.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class PacketParserError(MonitoringError):
    """패킷 파싱 관련 예외"""
    pass

class PacketParser:
    """패킷 분석 유틸리티 클래스"""

    @staticmethod
    def parse_packet(packet: Any) -> Dict[str, Any]:
        """패킷의 주요 필드를 딕셔너리 형태로 반환"""
        parsed_data = {}
        try:
            parsed_data.update({
                'protocol': packet.highest_layer,
                'src_ip': packet.ip.src,
                'dst_ip': packet.ip.dst,
                'src_port': packet[packet.transport_layer].srcport,
                'dst_port': packet[packet.transport_layer].dstport,
                'length': packet.length
            })
            logger.debug(f"Successfully parsed packet: {parsed_data}")
            return parsed_data
        except AttributeError as e:
            logger.error(f"Failed to parse packet: {str(e)}", exc_info=True)
            raise PacketParserError(
                "Failed to parse packet fields",
                error=str(e)
            ) from e

    @staticmethod
    def parse_http_packet(packet: Any) -> Dict[str, Any]:
        """HTTP 패킷의 주요 필드를 딕셔너리 형태로 반환"""
        if 'HTTP' not in packet:
            logger.warning("Packet does not contain HTTP layer")
            return {}
            
        try:
            return {
                'host': packet.http.host,
                'uri': packet.http.request_uri,
                'method': packet.http.request_method,
                'user_agent': packet.http.user_agent,
                'response_code': packet.http.get('response_code', None)
            }
        except AttributeError as e:
            logger.error(f"Failed to parse HTTP packet: {str(e)}", exc_info=True)
            raise PacketParserError(
                "Failed to parse HTTP packet fields",
                error=str(e)
            ) from e

    @staticmethod
    def parse_tcp_packet(packet: Any) -> Dict[str, Any]:
        """TCP 패킷의 주요 필드를 딕셔너리 형태로 반환"""
        if 'TCP' not in packet:
            logger.warning("Packet does not contain TCP layer")
            return {}
            
        try:
            return {
                'src_port': packet.tcp.srcport,
                'dst_port': packet.tcp.dstport,
                'flags': packet.tcp.flags
            }
        except AttributeError as e:
            logger.error(f"Failed to parse TCP packet: {str(e)}", exc_info=True)
            raise PacketParserError(
                "Failed to parse TCP packet fields",
                error=str(e)
            ) from e
