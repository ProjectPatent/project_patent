import json
from typing import Dict, Any

class MetricFormatter:
    """메트릭 포맷터 클래스: 메트릭 데이터를 다양한 형식으로 변환"""

    @staticmethod
    def to_json(metrics: Dict[str, Any]) -> str:
        """메트릭을 JSON 형식으로 변환"""
        try:
            return json.dumps(metrics, indent=2)
        except TypeError as e:
            raise ValueError("Failed to convert metrics to JSON") from e

    @staticmethod
    def to_text(metrics: Dict[str, Any]) -> str:
        """메트릭을 텍스트 형식으로 변환"""
        lines = []
        for name, value in metrics.items():
            lines.append(f"{name}: {value}")
        return "\n".join(lines)
