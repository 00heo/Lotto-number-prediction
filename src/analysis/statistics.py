"""통계 분석 모듈"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from scipy import stats
from loguru import logger


class StatisticalAnalyzer:
    """통계 분석 클래스"""

    def __init__(self, df: pd.DataFrame):
        """초기화

        Args:
            df: 로또 데이터 DataFrame
        """
        self.df = df
        self.number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]
        logger.info("StatisticalAnalyzer 초기화 완료")

    def calculate_frequency(self, recent_n: Optional[int] = None) -> pd.Series:
        """번호별 출현 빈도 계산

        Args:
            recent_n: 최근 N회차만 분석 (None이면 전체)

        Returns:
            번호별 빈도 Series
        """
        df = self.df.tail(recent_n) if recent_n else self.df

        all_numbers = pd.concat([df[col] for col in self.number_cols])
        frequency = all_numbers.value_counts().sort_index()

        # 1-45 범위로 채우기
        full_freq = pd.Series(0, index=range(1, 46))
        full_freq.update(frequency)

        return full_freq

    def calculate_bonus_frequency(
        self, recent_n: Optional[int] = None
    ) -> pd.Series:
        """보너스 번호 빈도 계산

        Args:
            recent_n: 최근 N회차만 분석

        Returns:
            보너스 번호 빈도 Series
        """
        df = self.df.tail(recent_n) if recent_n else self.df

        bonus_freq = df["bonus"].value_counts().sort_index()

        full_freq = pd.Series(0, index=range(1, 46))
        full_freq.update(bonus_freq)

        return full_freq

    def calculate_weighted_frequency(
        self, weights: Optional[Dict[str, float]] = None
    ) -> pd.Series:
        """가중 빈도 계산

        Args:
            weights: 기간별 가중치 딕셔너리
                예: {"all": 0.3, "recent_50": 0.4, "recent_20": 0.3}

        Returns:
            가중 빈도 Series
        """
        if weights is None:
            weights = {"all": 0.3, "recent_50": 0.4, "recent_20": 0.3}

        weighted_freq = pd.Series(0.0, index=range(1, 46))

        for period, weight in weights.items():
            if period == "all":
                freq = self.calculate_frequency()
            else:
                n = int(period.split("_")[1])
                freq = self.calculate_frequency(recent_n=n)

            # 정규화 후 가중치 적용
            freq_norm = freq / freq.sum() if freq.sum() > 0 else freq
            weighted_freq += freq_norm * weight

        return weighted_freq

    def calculate_gap_statistics(self) -> pd.DataFrame:
        """번호별 출현 간격 통계

        Returns:
            번호별 간격 통계 DataFrame
        """
        gap_stats = []

        for number in range(1, 46):
            # 해당 번호가 출현한 회차
            appeared_rounds = []

            for idx, row in self.df.iterrows():
                numbers = [row[col] for col in self.number_cols]
                if number in numbers:
                    appeared_rounds.append(row["round"])

            if len(appeared_rounds) > 1:
                # 간격 계산
                gaps = np.diff(appeared_rounds)

                gap_stats.append(
                    {
                        "number": number,
                        "appearances": len(appeared_rounds),
                        "last_round": appeared_rounds[-1],
                        "gap_mean": gaps.mean(),
                        "gap_std": gaps.std(),
                        "gap_min": gaps.min(),
                        "gap_max": gaps.max(),
                        "current_gap": (
                            self.df["round"].max() - appeared_rounds[-1]
                        ),
                    }
                )
            else:
                gap_stats.append(
                    {
                        "number": number,
                        "appearances": len(appeared_rounds),
                        "last_round": appeared_rounds[0] if appeared_rounds else None,
                        "gap_mean": None,
                        "gap_std": None,
                        "gap_min": None,
                        "gap_max": None,
                        "current_gap": (
                            self.df["round"].max() - appeared_rounds[0]
                            if appeared_rounds
                            else None
                        ),
                    }
                )

        return pd.DataFrame(gap_stats)

    def calculate_hot_cold_numbers(
        self, recent_n: int = 20, threshold: float = 1.2
    ) -> Dict[str, List[int]]:
        """핫/콜드 번호 분석

        Args:
            recent_n: 최근 N회차
            threshold: 평균 대비 기준값

        Returns:
            핫/콜드 번호 딕셔너리
        """
        recent_freq = self.calculate_frequency(recent_n)
        mean_freq = recent_freq.mean()

        hot_numbers = recent_freq[recent_freq >= mean_freq * threshold].index.tolist()
        cold_numbers = recent_freq[
            recent_freq <= mean_freq / threshold
        ].index.tolist()

        return {"hot": hot_numbers, "cold": cold_numbers, "neutral": []}

    def calculate_odd_even_ratio(self) -> pd.Series:
        """홀짝 비율 분석

        Returns:
            회차별 홀수 개수 Series
        """
        odd_counts = (self.df[self.number_cols] % 2 == 1).sum(axis=1)
        return odd_counts

    def calculate_range_distribution(self) -> pd.DataFrame:
        """구간별 분포 분석

        Returns:
            구간별 분포 DataFrame
        """
        ranges = {
            "1-10": (1, 10),
            "11-20": (11, 20),
            "21-30": (21, 30),
            "31-40": (31, 40),
            "41-45": (41, 45),
        }

        range_counts = []

        for range_name, (start, end) in ranges.items():
            count = 0
            for col in self.number_cols:
                count += ((self.df[col] >= start) & (self.df[col] <= end)).sum()

            range_counts.append(
                {
                    "range": range_name,
                    "count": count,
                    "ratio": count / (len(self.df) * 6),
                }
            )

        return pd.DataFrame(range_counts)

    def calculate_consecutive_patterns(self) -> Dict[str, Any]:
        """연속 번호 패턴 분석

        Returns:
            연속 패턴 통계
        """
        consecutive_counts = []

        for _, row in self.df.iterrows():
            numbers = sorted([row[col] for col in self.number_cols])
            count = 0

            for i in range(len(numbers) - 1):
                if numbers[i + 1] - numbers[i] == 1:
                    count += 1

            consecutive_counts.append(count)

        return {
            "mean": np.mean(consecutive_counts),
            "std": np.std(consecutive_counts),
            "distribution": pd.Series(consecutive_counts).value_counts().to_dict(),
        }

    def calculate_sum_statistics(self) -> Dict[str, float]:
        """번호 합계 통계

        Returns:
            합계 통계
        """
        sums = self.df[self.number_cols].sum(axis=1)

        return {
            "mean": sums.mean(),
            "std": sums.std(),
            "min": sums.min(),
            "max": sums.max(),
            "median": sums.median(),
            "q25": sums.quantile(0.25),
            "q75": sums.quantile(0.75),
        }

    def test_randomness(self) -> Dict[str, Any]:
        """무작위성 검정

        Returns:
            검정 결과
        """
        results = {}

        # 1. 카이제곱 검정 (균등 분포 검정)
        freq = self.calculate_frequency()
        expected = len(self.df) * 6 / 45

        chi2, p_value = stats.chisquare(freq, f_exp=expected)

        results["chi_square"] = {
            "statistic": chi2,
            "p_value": p_value,
            "is_uniform": p_value > 0.05,
        }

        # 2. 런 테스트 (연속성 검정) - 첫 번째 번호만
        first_numbers = self.df["num1"].values
        median = np.median(first_numbers)
        runs = np.diff(first_numbers > median).sum() + 1

        expected_runs = (2 * len(first_numbers) - 1) / 3
        std_runs = np.sqrt((16 * len(first_numbers) - 29) / 90)

        z_score = (runs - expected_runs) / std_runs

        results["runs_test"] = {
            "runs": runs,
            "expected_runs": expected_runs,
            "z_score": z_score,
            "is_random": abs(z_score) < 1.96,
        }

        return results

    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """번호 간 상관관계 행렬

        Returns:
            상관관계 DataFrame
        """
        # 각 번호의 출현 여부를 이진 벡터로 변환
        number_presence = pd.DataFrame()

        for number in range(1, 46):
            presence = []
            for _, row in self.df.iterrows():
                numbers = [row[col] for col in self.number_cols]
                presence.append(1 if number in numbers else 0)

            number_presence[number] = presence

        # 상관관계 계산
        corr_matrix = number_presence.corr()

        return corr_matrix

    def get_trending_numbers(self, lookback: int = 10) -> Dict[str, List[int]]:
        """트렌드 번호 분석 (상승/하락)

        Args:
            lookback: 비교 기간

        Returns:
            트렌드 번호 딕셔너리
        """
        recent_freq = self.calculate_frequency(lookback)
        older_freq = self.calculate_frequency(lookback * 2)

        # 정규화
        recent_norm = recent_freq / recent_freq.sum()
        older_norm = older_freq / older_freq.sum()

        # 변화율
        change = recent_norm - older_norm

        # 상위/하위 번호
        trending_up = change.nlargest(10).index.tolist()
        trending_down = change.nsmallest(10).index.tolist()

        return {"up": trending_up, "down": trending_down}

    def analyze_all(self) -> Dict[str, Any]:
        """전체 통계 분석

        Returns:
            전체 분석 결과
        """
        logger.info("전체 통계 분석 시작...")

        results = {
            "total_rounds": len(self.df),
            "frequency": self.calculate_frequency().to_dict(),
            "weighted_frequency": self.calculate_weighted_frequency().to_dict(),
            "gap_statistics": self.calculate_gap_statistics().to_dict("records"),
            "hot_cold": self.calculate_hot_cold_numbers(),
            "range_distribution": self.calculate_range_distribution().to_dict(
                "records"
            ),
            "consecutive_patterns": self.calculate_consecutive_patterns(),
            "sum_statistics": self.calculate_sum_statistics(),
            "randomness_tests": self.test_randomness(),
            "trending_numbers": self.get_trending_numbers(),
        }

        logger.info("전체 통계 분석 완료")

        return results
