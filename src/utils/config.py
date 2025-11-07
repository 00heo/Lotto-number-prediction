"""설정 관리 모듈"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger


class Config:
    """설정 파일 관리 클래스"""

    _instance: Optional["Config"] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self.load()

    def load(self, config_path: Optional[str] = None) -> None:
        """설정 파일 로드

        Args:
            config_path: 설정 파일 경로 (기본: config.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        else:
            config_path = Path(config_path)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
            logger.info(f"설정 파일 로드 완료: {config_path}")
        except FileNotFoundError:
            logger.warning(f"설정 파일을 찾을 수 없음: {config_path}. 기본값 사용.")
            self._load_defaults()
        except yaml.YAMLError as e:
            logger.error(f"설정 파일 파싱 오류: {e}. 기본값 사용.")
            self._load_defaults()

    def _load_defaults(self) -> None:
        """기본 설정 로드"""
        self._config = {
            "data_collection": {
                "source_url": "https://data.soledot.com/lottowinnumber/fo/lottowinnumberlist.sd",
                "start_round": 1,
                "max_retries": 3,
                "timeout": 30,
            },
            "storage": {
                "database_path": "data/lotto.db",
                "raw_data_path": "data/raw/",
                "processed_data_path": "data/processed/",
            },
            "logging": {
                "level": "INFO",
                "file": "logs/lotto_prediction.log",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """설정값 가져오기

        Args:
            key: 설정 키 (점으로 구분된 경로, 예: 'data_collection.timeout')
            default: 기본값

        Returns:
            설정값
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """설정값 설정

        Args:
            key: 설정 키
            value: 설정값
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """전체 설정 반환

        Returns:
            전체 설정 딕셔너리
        """
        return self._config.copy()


# 싱글톤 인스턴스
config = Config()
