"""머신러닝 기반 예측 모델"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Any, List
from loguru import logger

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler

from .base_model import BaseModel
from ..analysis.feature_engineering import FeatureEngineer


class MLModel(BaseModel):
    """머신러닝 기반 예측 모델"""

    def __init__(
        self,
        name: str = "MLModel",
        model_type: str = "random_forest",
        params: Optional[Dict] = None,
    ):
        """초기화

        Args:
            name: 모델 이름
            model_type: 모델 타입 ("random_forest" or "xgboost")
            params: 모델 파라미터
        """
        super().__init__(name)

        self.model_type = model_type
        self.params = params or {}
        self.scaler = StandardScaler()
        self.feature_engineer = None
        self.models = {}  # 각 번호별 모델

        self._initialize_model()

        logger.info(f"{self.name} 초기화 완료 (type: {model_type})")

    def _initialize_model(self) -> None:
        """모델 초기화"""
        if self.model_type == "random_forest":
            default_params = {
                "n_estimators": 200,
                "max_depth": 20,
                "min_samples_split": 5,
                "random_state": 42,
                "n_jobs": -1,
            }
        elif self.model_type == "xgboost":
            default_params = {
                "n_estimators": 300,
                "max_depth": 10,
                "learning_rate": 0.05,
                "random_state": 42,
                "n_jobs": -1,
            }
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {self.model_type}")

        # 파라미터 병합
        default_params.update(self.params)
        self.params = default_params

    def _create_training_data(
        self, df: pd.DataFrame
    ) -> tuple[np.ndarray, List[np.ndarray]]:
        """학습 데이터 생성

        Args:
            df: 로또 데이터 DataFrame

        Returns:
            (특징 행렬, 타겟 배열 리스트)
        """
        # 특징 추출
        self.feature_engineer = FeatureEngineer(df)
        feature_matrix = self.feature_engineer.create_feature_matrix()

        # 특징 (번호 컬럼 제외)
        X = feature_matrix.drop(columns=["number"]).values

        # 스케일링
        X_scaled = self.scaler.fit_transform(X)

        # 타겟: 각 회차의 당첨 여부 (45개 번호별)
        number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]
        y_list = []

        for number in range(1, 46):
            # 각 회차에서 해당 번호가 나왔는지
            y = []
            for _, row in df.iterrows():
                numbers = [row[col] for col in number_cols]
                y.append(1 if number in numbers else 0)

            y_list.append(np.array(y))

        return X_scaled, y_list

    def train(self, X: pd.DataFrame, y: Optional[Any] = None) -> None:
        """모델 학습

        Args:
            X: 로또 데이터 DataFrame
            y: 사용하지 않음 (자동 생성)
        """
        logger.info(f"{self.name} 학습 시작...")

        # 학습 데이터 생성
        X_train, y_train_list = self._create_training_data(X)

        # 각 번호별로 모델 학습
        logger.info("번호별 모델 학습 중...")

        for number in range(1, 46):
            y_train = y_train_list[number - 1]

            # 모델 생성
            if self.model_type == "random_forest":
                model = RandomForestClassifier(**self.params)
            elif self.model_type == "xgboost":
                model = XGBClassifier(**self.params, eval_metric="logloss")

            # 학습
            # 최근 데이터에 더 높은 가중치 부여
            sample_weight = np.linspace(0.5, 1.0, len(y_train))

            model.fit(X_train, y_train, sample_weight=sample_weight)

            self.models[number] = model

            if number % 10 == 0:
                logger.debug(f"  {number}/45 완료")

        self.is_trained = True
        logger.info(f"{self.name} 학습 완료 (45개 모델)")

    def predict(self, X: Optional[Any] = None) -> np.ndarray:
        """예측 수행

        Args:
            X: 사용하지 않음 (최신 특징 사용)

        Returns:
            각 번호(1-45)의 출현 확률
        """
        if not self.is_trained:
            raise RuntimeError("모델이 학습되지 않았습니다.")

        # 최신 특징 행렬 사용
        feature_matrix = self.feature_engineer.create_feature_matrix()
        X_features = feature_matrix.drop(columns=["number"]).values

        # 스케일링
        X_scaled = self.scaler.transform(X_features)

        # 각 번호별 예측 확률
        probabilities = np.zeros(45)

        for number in range(1, 46):
            model = self.models[number]
            X_number = X_scaled[number - 1].reshape(1, -1)

            # 클래스 1(출현)의 확률
            proba = model.predict_proba(X_number)[0, 1]
            probabilities[number - 1] = proba

        # 정규화
        probabilities = probabilities / probabilities.sum()

        logger.debug(f"{self.name} 예측 완료")
        return probabilities

    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """특징 중요도 반환

        Args:
            top_n: 상위 N개

        Returns:
            특징 중요도 DataFrame
        """
        if not self.is_trained:
            raise RuntimeError("모델이 학습되지 않았습니다.")

        # 모든 모델의 특징 중요도 평균
        feature_names = self.feature_engineer.get_feature_importance_names()
        importance_sum = np.zeros(len(feature_names))

        for model in self.models.values():
            if hasattr(model, "feature_importances_"):
                importance_sum += model.feature_importances_

        importance_avg = importance_sum / len(self.models)

        # DataFrame 생성
        importance_df = pd.DataFrame(
            {"feature": feature_names, "importance": importance_avg}
        )

        importance_df = importance_df.sort_values("importance", ascending=False).head(
            top_n
        )

        return importance_df

    def evaluate_model(self, X: pd.DataFrame) -> Dict[str, Any]:
        """모델 평가

        Args:
            X: 평가 데이터

        Returns:
            평가 지표
        """
        if not self.is_trained:
            raise RuntimeError("모델이 학습되지 않았습니다.")

        X_test, y_test_list = self._create_training_data(X)

        # 정확도 계산
        accuracies = []

        for number in range(1, 46):
            model = self.models[number]
            y_test = y_test_list[number - 1]

            accuracy = model.score(X_test, y_test)
            accuracies.append(accuracy)

        return {
            "mean_accuracy": np.mean(accuracies),
            "std_accuracy": np.std(accuracies),
            "min_accuracy": np.min(accuracies),
            "max_accuracy": np.max(accuracies),
        }
