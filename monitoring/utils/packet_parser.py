from typing import Any, Dict
import logging

class PacketParser:
    """패킷 분석 유틸리티 클래스"""

    @staticmethod
    def parse_packet(packet: Any) -> Dict[str, Any]:
        """패킷의 주요 필드를 딕셔너리 형태로 반환합니다."""
        parsed_data = {}
        try:
            parsed_data['protocol'] = packet.highest_layer
            parsed_data['src_ip'] = packet.ip.src
            parsed_data['dst_ip'] = packet.ip.dst
            parsed_data['src_port'] = packet[packet.transport_layer].srcport
            parsed_data['dst_port'] = packet[packet.transport_layer].dstport
            parsed_data['length'] = packet.length
        except AttributeError as e:
            logging.warning(f"Could not parse all fields from packet: {e}")
        return parsed_data

    @staticmethod
    def parse_http_packet(packet: Any) -> Dict[str, Any]:
        """HTTP 패킷의 주요 필드를 딕셔너리 형태로 반환합니다."""
        parsed_data = {}
        if 'HTTP' in packet:
            parsed_data['host'] = packet.http.host
            parsed_data['uri'] = packet.http.request_uri
            parsed_data['method'] = packet.http.request_method
            parsed_data['user_agent'] = packet.http.user_agent
            parsed_data['response_code'] = packet.http.get('response_code', None)
        return parsed_data

    @staticmethod
    def parse_tcp_packet(packet: Any) -> Dict[str, Any]:
        """TCP 패킷의 주요 필드를 딕셔너리 형태로 반환합니다."""
        parsed_data = {}
        if 'TCP' in packet:
            parsed_data['src_port'] = packet.tcp.srcport
            parsed_data['dst_port'] = packet.tcp.dstport
            parsed_data['flags'] = packet.tcp.flags
        return parsed_data
