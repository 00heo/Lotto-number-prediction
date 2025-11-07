"""특징 추출 모듈"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from loguru import logger


class FeatureEngineer:
    """특징 추출 클래스"""

    def __init__(self, df: pd.DataFrame):
        """초기화

        Args:
            df: 로또 데이터 DataFrame
        """
        self.df = df
        self.number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]
        logger.info("FeatureEngineer 초기화 완료")

    def extract_frequency_features(
        self, lookback_periods: List[int] = [5, 10, 20, 50]
    ) -> pd.DataFrame:
        """빈도 기반 특징 추출

        Args:
            lookback_periods: 과거 회차 리스트

        Returns:
            특징 DataFrame (45 x features)
        """
        features = pd.DataFrame({"number": range(1, 46)})

        # 전체 빈도
        all_freq = self._calculate_number_frequency(self.df)
        features["freq_all"] = features["number"].map(all_freq)

        # 기간별 빈도
        for period in lookback_periods:
            recent_df = self.df.tail(period)
            freq = self._calculate_number_frequency(recent_df)
            features[f"freq_last_{period}"] = features["number"].map(freq)

        # 정규화
        for col in features.columns:
            if col.startswith("freq_"):
                total = features[col].sum()
                if total > 0:
                    features[f"{col}_norm"] = features[col] / total

        logger.info(f"빈도 특징 추출 완료: {len(features.columns)}개")
        return features

    def extract_gap_features(self) -> pd.DataFrame:
        """출현 간격 특징 추출

        Returns:
            특징 DataFrame
        """
        features = pd.DataFrame({"number": range(1, 46)})

        gap_data = []

        for number in range(1, 46):
            # 출현 회차 찾기
            appeared_rounds = []

            for _, row in self.df.iterrows():
                numbers = [row[col] for col in self.number_cols]
                if number in numbers:
                    appeared_rounds.append(row["round"])

            if len(appeared_rounds) >= 2:
                gaps = np.diff(appeared_rounds)
                gap_data.append(
                    {
                        "number": number,
                        "gap_mean": gaps.mean(),
                        "gap_std": gaps.std(),
                        "gap_min": gaps.min(),
                        "gap_max": gaps.max(),
                        "last_appearance": appeared_rounds[-1],
                        "current_gap": self.df["round"].max() - appeared_rounds[-1],
                        "appearances": len(appeared_rounds),
                    }
                )
            else:
                gap_data.append(
                    {
                        "number": number,
                        "gap_mean": 0,
                        "gap_std": 0,
                        "gap_min": 0,
                        "gap_max": 0,
                        "last_appearance": (
                            appeared_rounds[0] if appeared_rounds else 0
                        ),
                        "current_gap": (
                            self.df["round"].max() - appeared_rounds[0]
                            if appeared_rounds
                            else self.df["round"].max()
                        ),
                        "appearances": len(appeared_rounds),
                    }
                )

        gap_df = pd.DataFrame(gap_data)

        # Merge
        features = features.merge(gap_df, on="number", how="left")

        logger.info(f"간격 특징 추출 완료")
        return features

    def extract_co_occurrence_features(self) -> pd.DataFrame:
        """동반 출현 특징 추출

        Returns:
            동반 출현 행렬 (45 x 45)
        """
        # 초기화
        co_matrix = np.zeros((45, 45), dtype=int)

        # 동반 출현 카운트
        for _, row in self.df.iterrows():
            numbers = [row[col] for col in self.number_cols]

            for i in range(len(numbers)):
                for j in range(i + 1, len(numbers)):
                    n1, n2 = numbers[i] - 1, numbers[j] - 1
                    co_matrix[n1][n2] += 1
                    co_matrix[n2][n1] += 1

        # DataFrame 변환
        co_df = pd.DataFrame(co_matrix, index=range(1, 46), columns=range(1, 46))

        # 각 번호별 통계 추가
        features = pd.DataFrame({"number": range(1, 46)})

        features["co_occurrence_sum"] = [co_df.loc[i].sum() for i in range(1, 46)]
        features["co_occurrence_mean"] = [co_df.loc[i].mean() for i in range(1, 46)]
        features["co_occurrence_max"] = [co_df.loc[i].max() for i in range(1, 46)]

        logger.info("동반 출현 특징 추출 완료")
        return features

    def extract_pattern_features(self) -> pd.DataFrame:
        """패턴 특징 추출

        Returns:
            특징 DataFrame
        """
        features = pd.DataFrame({"number": range(1, 46)})

        # 홀짝
        features["is_odd"] = features["number"] % 2

        # 소수
        def is_prime(n):
            if n < 2:
                return False
            if n == 2:
                return True
            if n % 2 == 0:
                return False
            for i in range(3, int(n**0.5) + 1, 2):
                if n % i == 0:
                    return False
            return True

        features["is_prime"] = features["number"].apply(lambda x: int(is_prime(x)))

        # 구간
        def get_range_group(n):
            if n <= 10:
                return 0
            elif n <= 20:
                return 1
            elif n <= 30:
                return 2
            elif n <= 40:
                return 3
            else:
                return 4

        features["range_group"] = features["number"].apply(get_range_group)

        # 끝자리
        features["last_digit"] = features["number"] % 10

        # 자릿수
        features["digit_count"] = features["number"].apply(lambda x: len(str(x)))

        # 연속 번호와 함께 나온 횟수
        consecutive_counts = self._count_consecutive_appearances()
        features["consecutive_count"] = features["number"].map(consecutive_counts)

        logger.info("패턴 특징 추출 완료")
        return features

    def extract_trend_features(
        self, lookback_periods: List[int] = [5, 10, 20]
    ) -> pd.DataFrame:
        """트렌드 특징 추출

        Args:
            lookback_periods: 분석 기간 리스트

        Returns:
            특징 DataFrame
        """
        features = pd.DataFrame({"number": range(1, 46)})

        for period in lookback_periods:
            # 최근 기간과 이전 기간 비교
            recent_freq = self._calculate_number_frequency(self.df.tail(period))
            older_freq = self._calculate_number_frequency(
                self.df.tail(period * 2).head(period)
            )

            # 정규화
            recent_norm = (
                recent_freq / recent_freq.sum() if recent_freq.sum() > 0 else recent_freq
            )
            older_norm = (
                older_freq / older_freq.sum() if older_freq.sum() > 0 else older_freq
            )

            # 트렌드 (변화율)
            trend = recent_norm - older_norm

            features[f"trend_{period}"] = features["number"].map(trend)

            # 모멘텀 (가속도)
            if period >= 10:
                very_old_freq = self._calculate_number_frequency(
                    self.df.tail(period * 3).head(period)
                )
                very_old_norm = (
                    very_old_freq / very_old_freq.sum()
                    if very_old_freq.sum() > 0
                    else very_old_freq
                )

                momentum = (recent_norm - older_norm) - (older_norm - very_old_norm)
                features[f"momentum_{period}"] = features["number"].map(momentum)

        logger.info("트렌드 특징 추출 완료")
        return features

    def extract_positional_features(self) -> pd.DataFrame:
        """위치별 출현 특징 (1번째, 2번째 ... 번호)

        Returns:
            특징 DataFrame
        """
        features = pd.DataFrame({"number": range(1, 46)})

        for idx, col in enumerate(self.number_cols, 1):
            freq = self.df[col].value_counts()
            features[f"pos_{idx}_freq"] = features["number"].map(freq).fillna(0)

        logger.info("위치별 특징 추출 완료")
        return features

    def extract_bonus_correlation(self) -> pd.DataFrame:
        """보너스 번호와의 상관관계

        Returns:
            특징 DataFrame
        """
        features = pd.DataFrame({"number": range(1, 46)})

        # 각 번호가 나왔을 때 보너스 번호 분포
        bonus_correlations = []

        for number in range(1, 46):
            # 해당 번호가 나온 회차의 보너스 번호
            bonus_when_appeared = []

            for _, row in self.df.iterrows():
                numbers = [row[col] for col in self.number_cols]
                if number in numbers:
                    bonus_when_appeared.append(row["bonus"])

            if bonus_when_appeared:
                # 보너스가 해당 번호 ±5 범위에 있는 비율
                close_bonus = sum(
                    1 for b in bonus_when_appeared if abs(b - number) <= 5
                )
                correlation_score = (
                    close_bonus / len(bonus_when_appeared)
                    if bonus_when_appeared
                    else 0
                )
            else:
                correlation_score = 0

            bonus_correlations.append(correlation_score)

        features["bonus_correlation"] = bonus_correlations

        logger.info("보너스 상관관계 특징 추출 완료")
        return features

    def create_feature_matrix(self) -> pd.DataFrame:
        """전체 특징 행렬 생성

        Returns:
            전체 특징 DataFrame (45 x features)
        """
        logger.info("전체 특징 행렬 생성 시작...")

        # 각 특징 추출
        freq_features = self.extract_frequency_features()
        gap_features = self.extract_gap_features()
        co_occurrence_features = self.extract_co_occurrence_features()
        pattern_features = self.extract_pattern_features()
        trend_features = self.extract_trend_features()
        positional_features = self.extract_positional_features()
        bonus_features = self.extract_bonus_correlation()

        # 병합
        feature_matrix = freq_features
        feature_matrix = feature_matrix.merge(gap_features, on="number", how="left")
        feature_matrix = feature_matrix.merge(
            co_occurrence_features, on="number", how="left"
        )
        feature_matrix = feature_matrix.merge(pattern_features, on="number", how="left")
        feature_matrix = feature_matrix.merge(trend_features, on="number", how="left")
        feature_matrix = feature_matrix.merge(
            positional_features, on="number", how="left"
        )
        feature_matrix = feature_matrix.merge(bonus_features, on="number", how="left")

        # 결측값 처리
        feature_matrix = feature_matrix.fillna(0)

        logger.info(
            f"전체 특징 행렬 생성 완료: {feature_matrix.shape[0]} x {feature_matrix.shape[1]}"
        )

        return feature_matrix

    def _calculate_number_frequency(self, df: pd.DataFrame) -> Dict[int, int]:
        """번호 빈도 계산 (헬퍼 함수)

        Args:
            df: DataFrame

        Returns:
            번호별 빈도 딕셔너리
        """
        all_numbers = pd.concat([df[col] for col in self.number_cols])
        freq = all_numbers.value_counts().to_dict()

        # 1-45 범위 채우기
        for i in range(1, 46):
            if i not in freq:
                freq[i] = 0

        return freq

    def _count_consecutive_appearances(self) -> Dict[int, int]:
        """연속 번호 출현 횟수 카운트

        Returns:
            번호별 연속 출현 횟수
        """
        consecutive_counts = {i: 0 for i in range(1, 46)}

        for _, row in self.df.iterrows():
            numbers = sorted([row[col] for col in self.number_cols])

            # 연속 번호 찾기
            for i in range(len(numbers) - 1):
                if numbers[i + 1] - numbers[i] == 1:
                    consecutive_counts[numbers[i]] += 1
                    consecutive_counts[numbers[i + 1]] += 1

        return consecutive_counts

    def get_feature_importance_names(self) -> List[str]:
        """특징 이름 리스트 반환

        Returns:
            특징 이름 리스트
        """
        feature_matrix = self.create_feature_matrix()
        return [col for col in feature_matrix.columns if col != "number"]
