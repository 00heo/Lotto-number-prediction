"""로깅 설정 모듈"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    log_file: Optional[str] = None,
    level: str = "INFO",
    rotation: str = "1 week",
    retention: str = "1 month",
) -> None:
    """로거 설정

    Args:
        log_file: 로그 파일 경로
        level: 로그 레벨
        rotation: 로그 로테이션 주기
        retention: 로그 보관 기간
    """
    # 기본 핸들러 제거
    logger.remove()

    # 콘솔 핸들러 추가
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # 파일 핸들러 추가
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )

    logger.info("로거 설정 완료")


# 기본 로거 설정
setup_logger(
    log_file="logs/lotto_prediction.log",
    level="INFO",
)
