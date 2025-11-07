"""앙상블 예측 모델"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from loguru import logger

from .base_model import BaseModel
from .statistical_model import StatisticalModel
from .ml_model import MLModel


class EnsembleModel(BaseModel):
    """앙상블 예측 모델"""

    def __init__(
        self,
        name: str = "EnsembleModel",
        weights: Optional[Dict[str, float]] = None,
    ):
        """초기화

        Args:
            name: 모델 이름
            weights: 모델별 가중치
        """
        super().__init__(name)

        if weights is None:
            self.weights = {
                "statistical": 0.30,
                "random_forest": 0.35,
                "xgboost": 0.35,
            }
        else:
            self.weights = weights

        self.models = {}
        self.model_predictions = {}

        logger.info(f"{self.name} 초기화 완료 (weights: {self.weights})")

    def add_model(self, model: BaseModel, weight: Optional[float] = None) -> None:
        """모델 추가

        Args:
            model: 추가할 모델
            weight: 가중치 (None이면 기존 설정 사용)
        """
        model_key = model.name.lower().replace("model", "").replace(" ", "_")

        self.models[model_key] = model

        if weight is not None:
            self.weights[model_key] = weight

        logger.info(f"모델 추가: {model.name} (weight: {self.weights.get(model_key, 0)})")

    def train(self, X: pd.DataFrame, y: Optional[Any] = None) -> None:
        """앙상블 모델 학습

        Args:
            X: 로또 데이터 DataFrame
            y: 사용하지 않음
        """
        logger.info(f"{self.name} 학습 시작...")

        # 기본 모델들 생성 및 학습
        if not self.models:
            logger.info("기본 모델 생성 중...")

            # 통계 모델
            stat_model = StatisticalModel(name="Statistical Model")
            stat_model.train(X)
            self.models["statistical"] = stat_model

            # Random Forest
            rf_model = MLModel(
                name="Random Forest Model", model_type="random_forest"
            )
            rf_model.train(X)
            self.models["random_forest"] = rf_model

            # XGBoost
            xgb_model = MLModel(name="XGBoost Model", model_type="xgboost")
            xgb_model.train(X)
            self.models["xgboost"] = xgb_model

        else:
            # 기존 모델 재학습
            logger.info(f"{len(self.models)}개 모델 학습 중...")
            for key, model in self.models.items():
                logger.info(f"  {model.name} 학습 중...")
                model.train(X)

        self.is_trained = True
        logger.info(f"{self.name} 학습 완료")

    def predict(self, X: Optional[Any] = None) -> np.ndarray:
        """앙상블 예측 수행

        Args:
            X: 사용하지 않음

        Returns:
            각 번호(1-45)의 출현 확률
        """
        if not self.is_trained:
            raise RuntimeError("모델이 학습되지 않았습니다.")

        logger.info(f"{self.name} 예측 시작...")

        # 각 모델의 예측
        ensemble_proba = np.zeros(45)
        total_weight = 0

        for key, model in self.models.items():
            weight = self.weights.get(key, 0)

            if weight > 0:
                proba = model.predict()
                self.model_predictions[key] = proba

                ensemble_proba += proba * weight
                total_weight += weight

                logger.debug(f"  {model.name}: weight={weight:.3f}")

        # 정규화
        if total_weight > 0:
            ensemble_proba = ensemble_proba / total_weight

        # 재정규화 (합=1)
        ensemble_proba = ensemble_proba / ensemble_proba.sum()

        logger.info(f"{self.name} 예측 완료")
        return ensemble_proba

    def get_model_predictions(self) -> pd.DataFrame:
        """각 모델의 예측 결과 반환

        Returns:
            모델별 예측 DataFrame
        """
        if not self.model_predictions:
            raise RuntimeError("예측이 수행되지 않았습니다.")

        predictions_df = pd.DataFrame({"number": range(1, 46)})

        for key, proba in self.model_predictions.items():
            predictions_df[key] = proba

        return predictions_df

    def get_prediction_variance(self) -> np.ndarray:
        """예측 분산 (모델 간 불일치도)

        Returns:
            각 번호별 예측 분산
        """
        if not self.model_predictions:
            raise RuntimeError("예측이 수행되지 않았습니다.")

        # 모든 예측을 행렬로
        prediction_matrix = np.array(list(self.model_predictions.values()))

        # 번호별 분산
        variance = np.var(prediction_matrix, axis=0)

        return variance

    def get_consensus_numbers(self, threshold: float = 0.6) -> List[int]:
        """합의 번호 (모든 모델이 높은 확률로 예측한 번호)

        Args:
            threshold: 합의 기준 (상위 비율)

        Returns:
            합의 번호 리스트
        """
        if not self.model_predictions:
            raise RuntimeError("예측이 수행되지 않았습니다.")

        # 각 모델의 상위 번호
        consensus_scores = np.zeros(45)

        for proba in self.model_predictions.values():
            # 상위 threshold% 번호
            top_k = int(45 * threshold)
            top_indices = np.argsort(proba)[-top_k:]

            consensus_scores[top_indices] += 1

        # 모든 모델에서 선정된 번호
        n_models = len(self.model_predictions)
        consensus_numbers = (
            np.where(consensus_scores == n_models)[0] + 1
        ).tolist()

        return consensus_numbers

    def get_model_weights(self) -> Dict[str, float]:
        """모델 가중치 반환

        Returns:
            가중치 딕셔너리
        """
        return self.weights.copy()

    def set_model_weights(self, weights: Dict[str, float]) -> None:
        """모델 가중치 설정

        Args:
            weights: 새로운 가중치
        """
        self.weights.update(weights)
        logger.info(f"가중치 업데이트: {self.weights}")

    def get_summary(self) -> Dict[str, Any]:
        """앙상블 요약 정보

        Returns:
            요약 딕셔너리
        """
        summary = {
            "name": self.name,
            "is_trained": self.is_trained,
            "n_models": len(self.models),
            "models": {key: model.name for key, model in self.models.items()},
            "weights": self.weights,
        }

        if self.model_predictions:
            variance = self.get_prediction_variance()
            summary["prediction_variance"] = {
                "mean": variance.mean(),
                "max": variance.max(),
                "min": variance.min(),
            }

            consensus = self.get_consensus_numbers(threshold=0.5)
            summary["consensus_numbers"] = consensus

        return summary
