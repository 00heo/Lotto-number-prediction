"""통계 기반 예측 모델"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Any
from loguru import logger

from .base_model import BaseModel
from ..analysis.statistics import StatisticalAnalyzer


class StatisticalModel(BaseModel):
    """통계 기반 예측 모델"""

    def __init__(
        self,
        name: str = "StatisticalModel",
        weights: Optional[Dict[str, float]] = None,
    ):
        """초기화

        Args:
            name: 모델 이름
            weights: 기간별 가중치
        """
        super().__init__(name)

        if weights is None:
            self.weights = {"all": 0.3, "recent_50": 0.4, "recent_20": 0.3}
        else:
            self.weights = weights

        self.analyzer = None
        self.probabilities = None

        logger.info(f"{self.name} 초기화 완료 (weights: {self.weights})")

    def train(self, X: pd.DataFrame, y: Optional[Any] = None) -> None:
        """모델 학습

        Args:
            X: 로또 데이터 DataFrame
            y: 사용하지 않음
        """
        logger.info(f"{self.name} 학습 시작...")

        self.analyzer = StatisticalAnalyzer(X)

        # 가중 빈도 계산
        weighted_freq = self.analyzer.calculate_weighted_frequency(self.weights)

        # 확률로 변환 (정규화)
        total = weighted_freq.sum()
        if total > 0:
            self.probabilities = weighted_freq / total
        else:
            # 균등 분포
            self.probabilities = pd.Series(1.0 / 45, index=range(1, 46))

        self.is_trained = True
        logger.info(f"{self.name} 학습 완료")

    def predict(self, X: Optional[Any] = None) -> np.ndarray:
        """예측 수행

        Args:
            X: 사용하지 않음

        Returns:
            각 번호(1-45)의 출현 확률
        """
        if not self.is_trained:
            raise RuntimeError("모델이 학습되지 않았습니다. train()을 먼저 호출하세요.")

        # 확률 배열 반환 (1-45)
        proba = self.probabilities.values

        logger.debug(f"{self.name} 예측 완료")
        return proba

    def get_top_numbers(self, n: int = 10) -> pd.DataFrame:
        """상위 N개 번호 반환

        Args:
            n: 반환할 개수

        Returns:
            상위 번호 DataFrame
        """
        if not self.is_trained:
            raise RuntimeError("모델이 학습되지 않았습니다.")

        top_numbers = self.probabilities.nlargest(n)

        result = pd.DataFrame(
            {
                "number": top_numbers.index,
                "probability": top_numbers.values,
                "rank": range(1, n + 1),
            }
        )

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환

        Returns:
            통계 딕셔너리
        """
        if not self.is_trained or self.analyzer is None:
            return {}

        return {
            "model": self.name,
            "weights": self.weights,
            "hot_cold": self.analyzer.calculate_hot_cold_numbers(),
            "sum_stats": self.analyzer.calculate_sum_statistics(),
        }
