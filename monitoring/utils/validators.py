from typing import Any, Dict

class ValidationError(Exception):
    """유효성 검사 실패 예외"""
    def __init__(self, message: str, field_name: str, invalid_value: Any, validation_rule: str):
        super().__init__(message)
        self.field_name = field_name
        self.invalid_value = invalid_value
        self.validation_rule = validation_rule

class Validators:
    """데이터 유효성 검사 유틸리티 클래스"""
    
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
