"""추천 시스템 모듈"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Any, Tuple
from itertools import combinations
from loguru import logger

from .predictor import LottoPredictor
from ..analysis.patterns import PatternAnalyzer


class LottoRecommender:
    """로또 번호 추천 시스템"""

    def __init__(self, predictor: LottoPredictor):
        """초기화

        Args:
            predictor: LottoPredictor 인스턴스
        """
        self.predictor = predictor
        self.recommendations = []

        logger.info("LottoRecommender 초기화 완료")

    def generate_combinations(
        self, n_combinations: int = 5, method: str = "probability"
    ) -> List[Dict[str, Any]]:
        """번호 조합 생성

        Args:
            n_combinations: 생성할 조합 수
            method: 생성 방법 ("probability", "balanced", "diverse")

        Returns:
            조합 리스트
        """
        if method == "probability":
            combinations_list = self._generate_probability_based(n_combinations)
        elif method == "balanced":
            combinations_list = self._generate_balanced(n_combinations)
        elif method == "diverse":
            combinations_list = self._generate_diverse(n_combinations)
        else:
            raise ValueError(f"지원하지 않는 방법: {method}")

        self.recommendations = combinations_list

        logger.info(f"{n_combinations}개 조합 생성 완료 (method: {method})")
        return combinations_list

    def _generate_probability_based(
        self, n_combinations: int
    ) -> List[Dict[str, Any]]:
        """확률 기반 조합 생성

        Args:
            n_combinations: 생성할 조합 수

        Returns:
            조합 리스트
        """
        # 예측 확률
        proba_df = self.predictor.get_number_probabilities()

        if proba_df.empty:
            logger.error("예측을 먼저 수행하세요.")
            return []

        combinations_list = []

        # 상위 확률 번호 풀
        top_numbers = proba_df.head(20)["number"].tolist()
        probabilities = proba_df.head(20)["probability"].values
        probabilities = probabilities / probabilities.sum()  # 정규화

        for i in range(n_combinations):
            # 확률 기반 샘플링 (중복 없이)
            selected = np.random.choice(
                top_numbers, size=6, replace=False, p=probabilities
            )
            selected = sorted(selected.tolist())

            # 보너스 번호 (상위 20개 중 선택된 번호 제외)
            bonus_pool = [n for n in top_numbers if n not in selected]
            bonus = np.random.choice(bonus_pool) if bonus_pool else top_numbers[-1]

            # 조합 확률 계산
            combo_proba = self._calculate_combination_probability(
                selected, proba_df
            )

            # 근거 생성
            reasoning = self._generate_reasoning(selected, bonus)

            combinations_list.append(
                {
                    "rank": i + 1,
                    "numbers": selected,
                    "bonus": int(bonus),
                    "probability": combo_proba,
                    "confidence": self._calculate_confidence(selected),
                    "reasoning": reasoning,
                }
            )

        # 확률순 정렬
        combinations_list.sort(key=lambda x: x["probability"], reverse=True)

        # 순위 재조정
        for i, combo in enumerate(combinations_list):
            combo["rank"] = i + 1

        return combinations_list

    def _generate_balanced(self, n_combinations: int) -> List[Dict[str, Any]]:
        """균형 잡힌 조합 생성

        Args:
            n_combinations: 생성할 조합 수

        Returns:
            조합 리스트
        """
        proba_df = self.predictor.get_number_probabilities()

        combinations_list = []

        for i in range(n_combinations):
            # 각 구간에서 균형있게 선택
            selected = []

            # 1-10
            range_1_10 = proba_df[
                (proba_df["number"] >= 1) & (proba_df["number"] <= 10)
            ].head(3)
            selected.append(
                np.random.choice(range_1_10["number"].values, size=1)[0]
            )

            # 11-20
            range_11_20 = proba_df[
                (proba_df["number"] >= 11) & (proba_df["number"] <= 20)
            ].head(3)
            selected.append(
                np.random.choice(range_11_20["number"].values, size=1)[0]
            )

            # 21-30
            range_21_30 = proba_df[
                (proba_df["number"] >= 21) & (proba_df["number"] <= 30)
            ].head(3)
            selected.append(
                np.random.choice(range_21_30["number"].values, size=1)[0]
            )

            # 31-40
            range_31_40 = proba_df[
                (proba_df["number"] >= 31) & (proba_df["number"] <= 40)
            ].head(3)
            selected.append(
                np.random.choice(range_31_40["number"].values, size=1)[0]
            )

            # 41-45
            range_41_45 = proba_df[
                (proba_df["number"] >= 41) & (proba_df["number"] <= 45)
            ].head(2)
            if not range_41_45.empty:
                selected.append(
                    np.random.choice(range_41_45["number"].values, size=1)[0]
                )

            # 나머지는 상위 확률에서
            remaining = 6 - len(selected)
            if remaining > 0:
                available = proba_df[
                    ~proba_df["number"].isin(selected)
                ].head(10)
                additional = np.random.choice(
                    available["number"].values, size=remaining, replace=False
                )
                selected.extend(additional.tolist())

            selected = sorted(selected[:6])

            # 보너스
            bonus_pool = proba_df[~proba_df["number"].isin(selected)].head(10)
            bonus = np.random.choice(bonus_pool["number"].values)

            combo_proba = self._calculate_combination_probability(
                selected, proba_df
            )
            reasoning = self._generate_reasoning(selected, bonus)

            combinations_list.append(
                {
                    "rank": i + 1,
                    "numbers": selected,
                    "bonus": int(bonus),
                    "probability": combo_proba,
                    "confidence": self._calculate_confidence(selected),
                    "reasoning": reasoning,
                }
            )

        return combinations_list

    def _generate_diverse(self, n_combinations: int) -> List[Dict[str, Any]]:
        """다양한 조합 생성

        Args:
            n_combinations: 생성할 조합 수

        Returns:
            조합 리스트
        """
        proba_df = self.predictor.get_number_probabilities()

        combinations_list = []
        used_combinations = set()

        attempts = 0
        max_attempts = n_combinations * 100

        while len(combinations_list) < n_combinations and attempts < max_attempts:
            attempts += 1

            # 상위 25개에서 랜덤 선택
            top_25 = proba_df.head(25)["number"].tolist()
            selected = sorted(np.random.choice(top_25, size=6, replace=False).tolist())

            # 중복 체크
            combo_tuple = tuple(selected)
            if combo_tuple in used_combinations:
                continue

            # 기존 조합과 최소 2개 이상 차이나는지 확인
            is_diverse = True
            for existing in combinations_list:
                overlap = len(set(selected) & set(existing["numbers"]))
                if overlap > 4:  # 4개 이상 겹치면 다양성 부족
                    is_diverse = False
                    break

            if not is_diverse:
                continue

            used_combinations.add(combo_tuple)

            # 보너스
            bonus_pool = proba_df[~proba_df["number"].isin(selected)].head(15)
            bonus = np.random.choice(bonus_pool["number"].values)

            combo_proba = self._calculate_combination_probability(
                selected, proba_df
            )
            reasoning = self._generate_reasoning(selected, bonus)

            combinations_list.append(
                {
                    "rank": len(combinations_list) + 1,
                    "numbers": selected,
                    "bonus": int(bonus),
                    "probability": combo_proba,
                    "confidence": self._calculate_confidence(selected),
                    "reasoning": reasoning,
                }
            )

        return combinations_list

    def _calculate_combination_probability(
        self, numbers: List[int], proba_df: pd.DataFrame
    ) -> float:
        """조합 확률 계산

        Args:
            numbers: 번호 리스트
            proba_df: 확률 DataFrame

        Returns:
            조합 확률
        """
        # 각 번호의 확률 곱 (독립 가정)
        prob = 1.0

        for num in numbers:
            num_prob = proba_df[proba_df["number"] == num]["probability"].values
            if len(num_prob) > 0:
                prob *= num_prob[0]

        # 정규화 (너무 작은 값 방지)
        prob = prob ** (1 / 6)  # 기하평균

        return float(prob)

    def _calculate_confidence(self, numbers: List[int]) -> float:
        """조합 신뢰도 계산

        Args:
            numbers: 번호 리스트

        Returns:
            신뢰도 (0-1)
        """
        # 여러 요소 기반 신뢰도
        confidence = 0.5  # 기본값

        # 1. 상위 확률 번호 포함 개수
        top_15 = self.predictor.get_top_numbers(15)
        top_count = len(set(numbers) & set(top_15))
        confidence += (top_count / 6) * 0.3

        # 2. 패턴 분석 (홀짝 균형)
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        balance_score = 1 - abs(odd_count - 3) / 3
        confidence += balance_score * 0.1

        # 3. 구간 다양성
        ranges = [0] * 5
        for num in numbers:
            if num <= 10:
                ranges[0] += 1
            elif num <= 20:
                ranges[1] += 1
            elif num <= 30:
                ranges[2] += 1
            elif num <= 40:
                ranges[3] += 1
            else:
                ranges[4] += 1

        diversity = len([r for r in ranges if r > 0]) / 5
        confidence += diversity * 0.1

        return min(confidence, 1.0)

    def _generate_reasoning(
        self, numbers: List[int], bonus: int
    ) -> Dict[str, Any]:
        """예측 근거 생성

        Args:
            numbers: 번호 리스트
            bonus: 보너스 번호

        Returns:
            근거 딕셔너리
        """
        top_15 = self.predictor.get_top_numbers(15)

        # 고빈도 번호
        high_freq = [n for n in numbers if n in top_15[:10]]

        # 최근 트렌드
        recent_trend = [n for n in numbers if n in top_15[:15]]

        # 홀짝 비율
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        even_count = 6 - odd_count

        # 연속 번호
        consecutive = []
        for i in range(len(numbers) - 1):
            if numbers[i + 1] - numbers[i] == 1:
                consecutive.extend([numbers[i], numbers[i + 1]])
        consecutive = list(set(consecutive))

        reasoning = {
            "high_frequency_numbers": high_freq,
            "trending_numbers": recent_trend,
            "odd_even_ratio": f"{odd_count}홀/{even_count}짝",
            "consecutive_numbers": consecutive if consecutive else None,
            "number_sum": sum(numbers),
            "range_distribution": self._get_range_distribution(numbers),
        }

        return reasoning

    def _get_range_distribution(self, numbers: List[int]) -> Dict[str, int]:
        """구간별 분포

        Args:
            numbers: 번호 리스트

        Returns:
            구간별 개수
        """
        distribution = {
            "1-10": 0,
            "11-20": 0,
            "21-30": 0,
            "31-40": 0,
            "41-45": 0,
        }

        for num in numbers:
            if num <= 10:
                distribution["1-10"] += 1
            elif num <= 20:
                distribution["11-20"] += 1
            elif num <= 30:
                distribution["21-30"] += 1
            elif num <= 40:
                distribution["31-40"] += 1
            else:
                distribution["41-45"] += 1

        return distribution

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """추천 조합 반환

        Returns:
            추천 조합 리스트
        """
        return self.recommendations

    def get_top_recommendation(self) -> Dict[str, Any]:
        """1순위 추천 반환

        Returns:
            1순위 조합
        """
        if not self.recommendations:
            logger.warning("조합을 먼저 생성하세요.")
            return {}

        return self.recommendations[0]

    def format_recommendations(self) -> str:
        """추천 조합 포맷팅

        Returns:
            포맷팅된 문자열
        """
        if not self.recommendations:
            return "추천 조합이 없습니다."

        output = []
        output.append("=" * 60)
        output.append("🎰 로또 6/45 추천 번호 (Top 5)")
        output.append("=" * 60)

        for combo in self.recommendations:
            output.append(f"\n[{combo['rank']}위] 확률: {combo['probability']:.4f} | 신뢰도: {combo['confidence']:.2f}")
            output.append(f"번호: {' - '.join(map(str, combo['numbers']))}  [보너스: {combo['bonus']}]")

            reasoning = combo["reasoning"]
            output.append(f"  ▪ 고빈도: {reasoning['high_frequency_numbers']}")
            output.append(f"  ▪ 홀짝: {reasoning['odd_even_ratio']}")
            output.append(f"  ▪ 합계: {reasoning['number_sum']}")
            output.append(f"  ▪ 구간: {reasoning['range_distribution']}")

        output.append("\n" + "=" * 60)
        output.append("⚠️  본 예측은 통계 분석 기반이며, 실제 당첨을 보장하지 않습니다.")
        output.append("=" * 60)

        return "\n".join(output)

    def save_recommendations(self, path: str) -> bool:
        """추천 조합 저장

        Args:
            path: 저장 경로

        Returns:
            성공 여부
        """
        if not self.recommendations:
            logger.warning("추천 조합이 없습니다.")
            return False

        try:
            import json
            from pathlib import Path

            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.recommendations, f, ensure_ascii=False, indent=2)

            logger.info(f"추천 조합 저장: {save_path}")
            return True

        except Exception as e:
            logger.error(f"추천 저장 실패: {e}")
            return False
