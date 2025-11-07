"""데이터 검증 모듈"""

from typing import List, Optional
from loguru import logger


def validate_numbers(numbers: List[int], bonus: Optional[int] = None) -> bool:
    """로또 번호 유효성 검증

    Args:
        numbers: 로또 번호 리스트 (6개)
        bonus: 보너스 번호 (선택)

    Returns:
        유효 여부

    Raises:
        ValueError: 유효하지 않은 번호
    """
    # 개수 확인
    if len(numbers) != 6:
        raise ValueError(f"번호는 6개여야 합니다. (현재: {len(numbers)}개)")

    # 범위 확인 (1-45)
    if not all(1 <= num <= 45 for num in numbers):
        raise ValueError("모든 번호는 1-45 범위여야 합니다.")

    # 중복 확인
    if len(set(numbers)) != 6:
        raise ValueError("중복된 번호가 있습니다.")

    # 보너스 번호 확인
    if bonus is not None:
        if not 1 <= bonus <= 45:
            raise ValueError(f"보너스 번호는 1-45 범위여야 합니다. (현재: {bonus})")

        if bonus in numbers:
            raise ValueError("보너스 번호가 메인 번호와 중복됩니다.")

    return True


def validate_round(round_num: int, max_round: Optional[int] = None) -> bool:
    """회차 유효성 검증

    Args:
        round_num: 회차 번호
        max_round: 최대 회차 (선택)

    Returns:
        유효 여부

    Raises:
        ValueError: 유효하지 않은 회차
    """
    if round_num < 1:
        raise ValueError(f"회차는 1 이상이어야 합니다. (현재: {round_num})")

    if max_round is not None and round_num > max_round:
        raise ValueError(f"회차는 {max_round} 이하여야 합니다. (현재: {round_num})")

    return True


def validate_dataframe(df, required_columns: List[str]) -> bool:
    """DataFrame 유효성 검증

    Args:
        df: pandas DataFrame
        required_columns: 필수 컬럼 리스트

    Returns:
        유효 여부

    Raises:
        ValueError: 유효하지 않은 DataFrame
    """
    # None 확인
    if df is None:
        raise ValueError("DataFrame이 None입니다.")

    # 빈 DataFrame 확인
    if df.empty:
        raise ValueError("DataFrame이 비어있습니다.")

    # 필수 컬럼 확인
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")

    logger.info("DataFrame 검증 완료")
    return True


def sanitize_input(text: str) -> str:
    """입력 텍스트 정제

    Args:
        text: 입력 텍스트

    Returns:
        정제된 텍스트
    """
    if not isinstance(text, str):
        return str(text)

    # 공백 제거
    text = text.strip()

    # 특수 문자 제거 (필요시)
    # text = re.sub(r'[^\w\s-]', '', text)

    return text
