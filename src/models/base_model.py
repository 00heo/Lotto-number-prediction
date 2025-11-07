"""기본 모델 클래스"""

from abc import ABC, abstractmethod
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
from loguru import logger


class BaseModel(ABC):
    """모든 예측 모델의 기본 클래스"""

    def __init__(self, name: str = "BaseModel"):
        """초기화

        Args:
            name: 모델 이름
        """
        self.name = name
        self.is_trained = False
        self.model = None
        logger.info(f"{self.name} 초기화")

    @abstractmethod
    def train(self, X: Any, y: Optional[Any] = None) -> None:
        """모델 학습

        Args:
            X: 학습 데이터
            y: 타겟 데이터 (선택)
        """
        pass

    @abstractmethod
    def predict(self, X: Optional[Any] = None) -> np.ndarray:
        """예측 수행

        Args:
            X: 입력 데이터

        Returns:
            예측 결과 (각 번호의 확률)
        """
        pass

    def predict_proba(self, X: Optional[Any] = None) -> np.ndarray:
        """확률 예측 (predict와 동일)

        Args:
            X: 입력 데이터

        Returns:
            각 번호의 출현 확률
        """
        return self.predict(X)

    def save(self, path: str) -> bool:
        """모델 저장

        Args:
            path: 저장 경로

        Returns:
            성공 여부
        """
        try:
            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            model_data = {
                "name": self.name,
                "is_trained": self.is_trained,
                "model": self.model,
            }

            with open(save_path, "wb") as f:
                pickle.dump(model_data, f)

            logger.info(f"{self.name} 저장 완료: {save_path}")
            return True

        except Exception as e:
            logger.error(f"모델 저장 실패: {e}")
            return False

    def load(self, path: str) -> bool:
        """모델 로드

        Args:
            path: 로드 경로

        Returns:
            성공 여부
        """
        try:
            load_path = Path(path)

            if not load_path.exists():
                logger.error(f"모델 파일이 없습니다: {load_path}")
                return False

            with open(load_path, "rb") as f:
                model_data = pickle.load(f)

            self.name = model_data["name"]
            self.is_trained = model_data["is_trained"]
            self.model = model_data["model"]

            logger.info(f"{self.name} 로드 완료: {load_path}")
            return True

        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """모델 정보 반환

        Returns:
            모델 정보 딕셔너리
        """
        return {
            "name": self.name,
            "is_trained": self.is_trained,
            "type": self.__class__.__name__,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', trained={self.is_trained})"
