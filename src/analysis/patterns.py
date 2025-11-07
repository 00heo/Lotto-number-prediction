"""패턴 분석 모듈"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter
from loguru import logger


class PatternAnalyzer:
    """패턴 분석 클래스"""

    def __init__(self, df: pd.DataFrame):
        """초기화

        Args:
            df: 로또 데이터 DataFrame
        """
        self.df = df
        self.number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]
        logger.info("PatternAnalyzer 초기화 완료")

    def analyze_consecutive_patterns(self) -> Dict[str, Any]:
        """연속 번호 패턴 분석

        Returns:
            패턴 분석 결과
        """
        patterns = []

        for _, row in self.df.iterrows():
            numbers = sorted([row[col] for col in self.number_cols])

            # 연속 그룹 찾기
            consecutive_groups = []
            current_group = [numbers[0]]

            for i in range(1, len(numbers)):
                if numbers[i] - numbers[i - 1] == 1:
                    current_group.append(numbers[i])
                else:
                    if len(current_group) >= 2:
                        consecutive_groups.append(current_group.copy())
                    current_group = [numbers[i]]

            if len(current_group) >= 2:
                consecutive_groups.append(current_group)

            patterns.append(
                {
                    "round": row["round"],
                    "consecutive_count": len(
                        [g for g in consecutive_groups if len(g) >= 2]
                    ),
                    "max_consecutive_length": (
                        max(len(g) for g in consecutive_groups)
                        if consecutive_groups
                        else 0
                    ),
                    "groups": consecutive_groups,
                }
            )

        patterns_df = pd.DataFrame(patterns)

        result = {
            "avg_consecutive_count": patterns_df["consecutive_count"].mean(),
            "max_consecutive_length_distribution": patterns_df[
                "max_consecutive_length"
            ]
            .value_counts()
            .to_dict(),
            "rounds_with_consecutive": (patterns_df["consecutive_count"] > 0).sum(),
            "rounds_without_consecutive": (patterns_df["consecutive_count"] == 0).sum(),
        }

        logger.info("연속 번호 패턴 분석 완료")
        return result

    def analyze_arithmetic_patterns(self) -> Dict[str, Any]:
        """등차수열 패턴 분석

        Returns:
            패턴 분석 결과
        """
        arithmetic_patterns = []

        for _, row in self.df.iterrows():
            numbers = sorted([row[col] for col in self.number_cols])

            # 모든 3개 이상 조합에서 등차수열 찾기
            found_arithmetic = []

            for length in range(3, 7):
                for i in range(len(numbers) - length + 1):
                    subset = numbers[i : i + length]
                    diffs = [subset[j + 1] - subset[j] for j in range(len(subset) - 1)]

                    if len(set(diffs)) == 1 and diffs[0] > 1:
                        found_arithmetic.append(
                            {"numbers": subset, "difference": diffs[0]}
                        )

            arithmetic_patterns.append(
                {
                    "round": row["round"],
                    "has_arithmetic": len(found_arithmetic) > 0,
                    "patterns": found_arithmetic,
                }
            )

        patterns_df = pd.DataFrame(arithmetic_patterns)

        result = {
            "total_patterns": sum(len(p["patterns"]) for p in arithmetic_patterns),
            "rounds_with_arithmetic": patterns_df["has_arithmetic"].sum(),
            "arithmetic_ratio": patterns_df["has_arithmetic"].mean(),
        }

        logger.info("등차수열 패턴 분석 완료")
        return result

    def analyze_symmetry_patterns(self) -> Dict[str, Any]:
        """대칭 패턴 분석 (중앙값 기준)

        Returns:
            패턴 분석 결과
        """
        symmetry_scores = []

        for _, row in self.df.iterrows():
            numbers = sorted([row[col] for col in self.number_cols])

            # 중앙값 (23)
            center = 23

            # 각 번호의 중앙으로부터 거리
            distances = [abs(n - center) for n in numbers]

            # 대칭성 점수 (거리의 분산이 낮을수록 대칭적)
            symmetry_score = 1 / (1 + np.std(distances))

            symmetry_scores.append(
                {"round": row["round"], "symmetry_score": symmetry_score}
            )

        symmetry_df = pd.DataFrame(symmetry_scores)

        result = {
            "avg_symmetry_score": symmetry_df["symmetry_score"].mean(),
            "max_symmetry_score": symmetry_df["symmetry_score"].max(),
            "min_symmetry_score": symmetry_df["symmetry_score"].min(),
        }

        logger.info("대칭 패턴 분석 완료")
        return result

    def analyze_range_balance(self) -> Dict[str, Any]:
        """구간별 균형 분석

        Returns:
            균형 분석 결과
        """
        range_distributions = []

        for _, row in self.df.iterrows():
            numbers = [row[col] for col in self.number_cols]

            ranges = {"1-10": 0, "11-20": 0, "21-30": 0, "31-40": 0, "41-45": 0}

            for num in numbers:
                if num <= 10:
                    ranges["1-10"] += 1
                elif num <= 20:
                    ranges["11-20"] += 1
                elif num <= 30:
                    ranges["21-30"] += 1
                elif num <= 40:
                    ranges["31-40"] += 1
                else:
                    ranges["41-45"] += 1

            # 균형 점수 (표준편차가 낮을수록 균형적)
            balance_score = 1 / (1 + np.std(list(ranges.values())))

            range_distributions.append(
                {"round": row["round"], "ranges": ranges, "balance_score": balance_score}
            )

        balance_df = pd.DataFrame(range_distributions)

        result = {
            "avg_balance_score": balance_df["balance_score"].mean(),
            "most_common_distribution": self._find_most_common_distribution(
                range_distributions
            ),
        }

        logger.info("구간별 균형 분석 완료")
        return result

    def analyze_last_digit_patterns(self) -> Dict[str, Any]:
        """끝자리 패턴 분석

        Returns:
            패턴 분석 결과
        """
        last_digit_distributions = []

        for _, row in self.df.iterrows():
            numbers = [row[col] for col in self.number_cols]
            last_digits = [n % 10 for n in numbers]

            last_digit_distributions.append(
                {"round": row["round"], "last_digits": Counter(last_digits)}
            )

        # 전체 끝자리 빈도
        all_last_digits = []
        for dist in last_digit_distributions:
            all_last_digits.extend(dist["last_digits"].elements())

        last_digit_freq = Counter(all_last_digits)

        result = {
            "last_digit_frequency": dict(last_digit_freq),
            "most_common_last_digit": last_digit_freq.most_common(1)[0]
            if last_digit_freq
            else None,
        }

        logger.info("끝자리 패턴 분석 완료")
        return result

    def analyze_sum_patterns(self) -> Dict[str, Any]:
        """합계 패턴 분석

        Returns:
            패턴 분석 결과
        """
        sums = self.df[self.number_cols].sum(axis=1)

        result = {
            "mean": sums.mean(),
            "std": sums.std(),
            "min": sums.min(),
            "max": sums.max(),
            "median": sums.median(),
            "quartiles": {
                "q25": sums.quantile(0.25),
                "q50": sums.quantile(0.50),
                "q75": sums.quantile(0.75),
            },
            "sum_range_distribution": self._categorize_sums(sums),
        }

        logger.info("합계 패턴 분석 완료")
        return result

    def find_repeating_combinations(self, min_size: int = 3) -> List[Dict[str, Any]]:
        """반복되는 번호 조합 찾기

        Args:
            min_size: 최소 조합 크기

        Returns:
            반복 조합 리스트
        """
        from itertools import combinations

        # 모든 조합 수집
        all_combinations = Counter()

        for _, row in self.df.iterrows():
            numbers = tuple(sorted([row[col] for col in self.number_cols]))

            # 모든 부분 조합 생성
            for size in range(min_size, 7):
                for combo in combinations(numbers, size):
                    all_combinations[combo] += 1

        # 2번 이상 나온 조합
        repeating = [
            {"combination": list(combo), "count": count}
            for combo, count in all_combinations.items()
            if count >= 2
        ]

        # 빈도순 정렬
        repeating.sort(key=lambda x: x["count"], reverse=True)

        logger.info(f"반복 조합 발견: {len(repeating)}개")
        return repeating[:50]  # 상위 50개

    def analyze_hot_cold_transitions(self, threshold: int = 20) -> Dict[str, Any]:
        """핫/콜드 번호 전환 분석

        Args:
            threshold: 핫/콜드 판단 기준 (최근 N회차)

        Returns:
            전환 분석 결과
        """
        transitions = []

        # 슬라이딩 윈도우로 핫/콜드 추적
        for i in range(threshold, len(self.df), threshold):
            window1 = self.df.iloc[i - threshold : i]
            window2 = self.df.iloc[i : min(i + threshold, len(self.df))]

            freq1 = self._calculate_frequency(window1)
            freq2 = self._calculate_frequency(window2)

            # 핫/콜드 분류
            mean1 = freq1.mean()
            mean2 = freq2.mean()

            hot1 = set(freq1[freq1 > mean1].index)
            cold1 = set(freq1[freq1 < mean1].index)

            hot2 = set(freq2[freq2 > mean2].index)
            cold2 = set(freq2[freq2 < mean2].index)

            # 전환된 번호
            hot_to_cold = hot1 & cold2
            cold_to_hot = cold1 & hot2

            transitions.append(
                {
                    "window": i,
                    "hot_to_cold": list(hot_to_cold),
                    "cold_to_hot": list(cold_to_hot),
                    "hot_to_cold_count": len(hot_to_cold),
                    "cold_to_hot_count": len(cold_to_hot),
                }
            )

        result = {
            "transitions": transitions,
            "avg_hot_to_cold": np.mean([t["hot_to_cold_count"] for t in transitions]),
            "avg_cold_to_hot": np.mean([t["cold_to_hot_count"] for t in transitions]),
        }

        logger.info("핫/콜드 전환 분석 완료")
        return result

    def _calculate_frequency(self, df: pd.DataFrame) -> pd.Series:
        """번호 빈도 계산 (헬퍼)

        Args:
            df: DataFrame

        Returns:
            빈도 Series
        """
        all_numbers = pd.concat([df[col] for col in self.number_cols])
        freq = all_numbers.value_counts()

        # 1-45 범위 채우기
        full_freq = pd.Series(0, index=range(1, 46))
        full_freq.update(freq)

        return full_freq

    def _find_most_common_distribution(
        self, distributions: List[Dict]
    ) -> Optional[Dict]:
        """가장 흔한 구간 분포 찾기

        Args:
            distributions: 분포 리스트

        Returns:
            가장 흔한 분포
        """
        # 분포를 튜플로 변환하여 카운트
        dist_tuples = [
            tuple(sorted(d["ranges"].values())) for d in distributions
        ]

        counter = Counter(dist_tuples)
        most_common = counter.most_common(1)

        if most_common:
            return {"distribution": most_common[0][0], "count": most_common[0][1]}
        return None

    def _categorize_sums(self, sums: pd.Series) -> Dict[str, int]:
        """합계 범위별 분류

        Args:
            sums: 합계 Series

        Returns:
            범위별 개수
        """
        categories = {
            "very_low (<100)": (sums < 100).sum(),
            "low (100-120)": ((sums >= 100) & (sums < 120)).sum(),
            "medium (120-160)": ((sums >= 120) & (sums < 160)).sum(),
            "high (160-180)": ((sums >= 160) & (sums < 180)).sum(),
            "very_high (>=180)": (sums >= 180).sum(),
        }

        return categories

    def analyze_all_patterns(self) -> Dict[str, Any]:
        """전체 패턴 분석

        Returns:
            전체 분석 결과
        """
        logger.info("전체 패턴 분석 시작...")

        results = {
            "consecutive": self.analyze_consecutive_patterns(),
            "arithmetic": self.analyze_arithmetic_patterns(),
            "symmetry": self.analyze_symmetry_patterns(),
            "range_balance": self.analyze_range_balance(),
            "last_digits": self.analyze_last_digit_patterns(),
            "sums": self.analyze_sum_patterns(),
            "repeating_combinations": self.find_repeating_combinations(),
            "hot_cold_transitions": self.analyze_hot_cold_transitions(),
        }

        logger.info("전체 패턴 분석 완료")
        return results
