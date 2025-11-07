"""예측 엔진 모듈"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

from ..data.storage import StorageManager
from ..data.preprocessor import DataPreprocessor
from ..models.ensemble import EnsembleModel


class LottoPredictor:
    """로또 번호 예측 클래스"""

    def __init__(
        self,
        storage: Optional[StorageManager] = None,
        model: Optional[EnsembleModel] = None,
    ):
        """초기화

        Args:
            storage: StorageManager 인스턴스
            model: 예측 모델 (None이면 새로 생성)
        """
        self.storage = storage if storage else StorageManager()
        self.preprocessor = DataPreprocessor(self.storage)

        self.model = model
        self.df = None
        self.latest_prediction = None

        logger.info("LottoPredictor 초기화 완료")

    def load_data(self) -> bool:
        """데이터 로드 및 전처리

        Returns:
            성공 여부
        """
        try:
            logger.info("데이터 로드 중...")

            # 데이터 로드
            df = self.preprocessor.load_data()

            if df.empty:
                logger.error("데이터가 없습니다.")
                return False

            # 데이터 정제
            df_clean = self.preprocessor.clean_data(df)

            # 특징 추가
            self.df = self.preprocessor.add_features(df_clean)

            logger.info(f"데이터 로드 완료: {len(self.df)}개 회차")
            return True

        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            return False

    def train_model(self, force_retrain: bool = False) -> bool:
        """모델 학습

        Args:
            force_retrain: 강제 재학습 여부

        Returns:
            성공 여부
        """
        try:
            if self.df is None or self.df.empty:
                logger.error("데이터를 먼저 로드하세요.")
                return False

            # 모델 초기화
            if self.model is None or force_retrain:
                logger.info("모델 학습 시작...")

                self.model = EnsembleModel()
                self.model.train(self.df)

                logger.info("모델 학습 완료")

            return True

        except Exception as e:
            logger.error(f"모델 학습 실패: {e}")
            return False

    def predict_next_draw(self) -> Dict[str, Any]:
        """다음 회차 예측

        Returns:
            예측 결과 딕셔너리
        """
        try:
            if self.model is None or not self.model.is_trained:
                logger.error("모델을 먼저 학습하세요.")
                return {}

            logger.info("다음 회차 예측 중...")

            # 예측 수행
            probabilities = self.model.predict()

            # 번호별 확률 DataFrame
            prediction_df = pd.DataFrame(
                {"number": range(1, 46), "probability": probabilities}
            )

            prediction_df = prediction_df.sort_values(
                "probability", ascending=False
            ).reset_index(drop=True)

            # 최신 회차 정보
            latest_round = self.df["round"].max()
            next_round = latest_round + 1

            # 예측 결과 저장
            self.latest_prediction = {
                "next_round": next_round,
                "prediction_date": pd.Timestamp.now(),
                "probabilities": prediction_df,
                "top_numbers": prediction_df.head(15)["number"].tolist(),
                "model_info": self.model.get_summary(),
            }

            logger.info(f"다음 회차({next_round}) 예측 완료")

            return self.latest_prediction

        except Exception as e:
            logger.error(f"예측 실패: {e}")
            return {}

    def get_number_probabilities(self) -> pd.DataFrame:
        """번호별 확률 반환

        Returns:
            확률 DataFrame
        """
        if self.latest_prediction is None:
            logger.warning("예측을 먼저 수행하세요.")
            return pd.DataFrame()

        return self.latest_prediction["probabilities"]

    def get_top_numbers(self, n: int = 15) -> List[int]:
        """상위 N개 번호 반환

        Args:
            n: 반환할 개수

        Returns:
            번호 리스트
        """
        if self.latest_prediction is None:
            logger.warning("예측을 먼저 수행하세요.")
            return []

        return self.latest_prediction["probabilities"].head(n)["number"].tolist()

    def predict_with_confidence(
        self, confidence_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """신뢰도 기반 예측

        Args:
            confidence_threshold: 신뢰도 기준

        Returns:
            예측 결과 및 신뢰도
        """
        if self.model is None or not self.model.is_trained:
            logger.error("모델을 먼저 학습하세요.")
            return {}

        # 예측
        probabilities = self.model.predict()

        # 모델 간 분산 (낮을수록 신뢰도 높음)
        variance = self.model.get_prediction_variance()

        # 신뢰도 점수 (확률과 일치도 기반)
        confidence_scores = probabilities * (1 - variance / variance.max())

        # 높은 신뢰도 번호
        high_confidence_mask = confidence_scores >= np.percentile(
            confidence_scores, (1 - confidence_threshold) * 100
        )

        high_confidence_numbers = (np.where(high_confidence_mask)[0] + 1).tolist()

        result = {
            "high_confidence_numbers": high_confidence_numbers,
            "confidence_scores": dict(
                zip(range(1, 46), confidence_scores.tolist())
            ),
            "mean_confidence": confidence_scores.mean(),
            "threshold": confidence_threshold,
        }

        return result

    def analyze_prediction_quality(self) -> Dict[str, Any]:
        """예측 품질 분석

        Returns:
            품질 지표
        """
        if self.latest_prediction is None:
            logger.warning("예측을 먼저 수행하세요.")
            return {}

        # 모델 요약
        model_summary = self.model.get_summary()

        # 예측 분산 (모델 간 불일치도)
        variance = self.model.get_prediction_variance()

        # 엔트로피 (불확실성)
        probabilities = self.latest_prediction["probabilities"]["probability"].values
        entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))

        quality = {
            "model_consensus": model_summary.get("consensus_numbers", []),
            "prediction_variance": {
                "mean": variance.mean(),
                "std": variance.std(),
                "max": variance.max(),
            },
            "entropy": entropy,
            "diversity_score": len(set(self.get_top_numbers(20)))
            / 20,  # 상위 20개 다양성
        }

        return quality

    def save_prediction(self, path: str) -> bool:
        """예측 결과 저장

        Args:
            path: 저장 경로

        Returns:
            성공 여부
        """
        if self.latest_prediction is None:
            logger.warning("예측을 먼저 수행하세요.")
            return False

        try:
            import json
            from pathlib import Path

            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # JSON 직렬화 가능한 형태로 변환
            prediction_data = {
                "next_round": int(self.latest_prediction["next_round"]),
                "prediction_date": self.latest_prediction["prediction_date"].isoformat(),
                "top_numbers": self.latest_prediction["top_numbers"],
                "probabilities": self.latest_prediction["probabilities"]
                .to_dict("records"),
            }

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(prediction_data, f, ensure_ascii=False, indent=2)

            logger.info(f"예측 결과 저장: {save_path}")
            return True

        except Exception as e:
            logger.error(f"예측 저장 실패: {e}")
            return False

    def load_prediction(self, path: str) -> bool:
        """예측 결과 로드

        Args:
            path: 로드 경로

        Returns:
            성공 여부
        """
        try:
            import json
            from pathlib import Path

            load_path = Path(path)

            if not load_path.exists():
                logger.error(f"파일이 없습니다: {load_path}")
                return False

            with open(load_path, "r", encoding="utf-8") as f:
                prediction_data = json.load(f)

            # DataFrame 복원
            probabilities_df = pd.DataFrame(prediction_data["probabilities"])

            self.latest_prediction = {
                "next_round": prediction_data["next_round"],
                "prediction_date": pd.Timestamp(prediction_data["prediction_date"]),
                "probabilities": probabilities_df,
                "top_numbers": prediction_data["top_numbers"],
            }

            logger.info(f"예측 결과 로드: {load_path}")
            return True

        except Exception as e:
            logger.error(f"예측 로드 실패: {e}")
            return False

    def get_prediction_summary(self) -> Dict[str, Any]:
        """예측 요약 정보

        Returns:
            요약 딕셔너리
        """
        if self.latest_prediction is None:
            return {}

        top_10 = self.get_top_numbers(10)

        summary = {
            "next_round": self.latest_prediction["next_round"],
            "prediction_date": self.latest_prediction["prediction_date"],
            "top_10_numbers": top_10,
            "top_probabilities": self.latest_prediction["probabilities"]
            .head(10)[["number", "probability"]]
            .to_dict("records"),
            "model_info": self.latest_prediction.get("model_info", {}),
        }

        return summary
