# validators.py
from typing import Any, TypeVar, Optional
from ..core.exceptions import ValidationError

T = TypeVar('T')

class Validators:
    """데이터 유효성 검사 유틸리티"""
    
    @staticmethod
    def validate_not_empty(value: Any, field_name: str):
        """빈 값이 아닌지 확인"""
        if not value:
            raise ValidationError(
                f"{field_name} must not be empty",
                field_name=field_name,
                invalid_value=value,
                validation_rule="non-empty value required"
            )
    
    @staticmethod
    def validate_positive(value: int, field_name: str):
        """양수인지 확인"""
        if value <= 0:
            raise ValidationError(
                f"{field_name} must be a positive integer",
                field_name=field_name,
                invalid_value=value,
                validation_rule="positive integer required"
            )
    
    @staticmethod
    def validate_range(
        value: int,
        field_name: str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ):
        """값이 지정된 범위 내에 있는지 확인"""
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} must be greater than or equal to {min_value}",
                field_name=field_name,
                invalid_value=value,
                validation_rule=f">= {min_value}"
            )
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} must be less than or equal to {max_value}",
                field_name=field_name,
                invalid_value=value,
                validation_rule=f"<= {max_value}"
            )