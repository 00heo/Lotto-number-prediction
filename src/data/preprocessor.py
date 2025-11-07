"""데이터 전처리 모듈"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from ..utils.validators import validate_dataframe
from .storage import StorageManager


class DataPreprocessor:
    """데이터 전처리 클래스"""

    def __init__(self, storage: Optional[StorageManager] = None):
        """초기화

        Args:
            storage: StorageManager 인스턴스
        """
        self.storage = storage if storage else StorageManager()
        logger.info("DataPreprocessor 초기화 완료")

    def load_data(self) -> pd.DataFrame:
        """데이터 로드

        Returns:
            pandas DataFrame
        """
        df = self.storage.get_all_results(order_by="round ASC")
        logger.info(f"데이터 로드: {len(df)}개 회차")
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 정제

        Args:
            df: 원본 DataFrame

        Returns:
            정제된 DataFrame
        """
        logger.info("데이터 정제 시작...")

        df_clean = df.copy()

        # 1. 중복 제거
        before_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=["round"], keep="last")
        after_count = len(df_clean)

        if before_count != after_count:
            logger.info(f"중복 제거: {before_count - after_count}개")

        # 2. 결측값 처리
        missing_counts = df_clean.isnull().sum()
        if missing_counts.any():
            logger.info(f"결측값 발견:\n{missing_counts[missing_counts > 0]}")

            # draw_date가 없으면 제거
            df_clean = df_clean.dropna(subset=["draw_date"])

            # 번호가 없으면 제거
            number_cols = ["num1", "num2", "num3", "num4", "num5", "num6", "bonus"]
            df_clean = df_clean.dropna(subset=number_cols)

            # 판매금액 등은 0으로 채우기
            df_clean["sales_amount"] = df_clean["sales_amount"].fillna(0)
            df_clean["winner_count_1st"] = df_clean["winner_count_1st"].fillna(0)
            df_clean["prize_1st"] = df_clean["prize_1st"].fillna(0)

        # 3. 데이터 타입 변환
        df_clean["round"] = df_clean["round"].astype(int)

        number_cols = ["num1", "num2", "num3", "num4", "num5", "num6", "bonus"]
        for col in number_cols:
            df_clean[col] = df_clean[col].astype(int)

        # 날짜 변환
        df_clean["draw_date"] = pd.to_datetime(df_clean["draw_date"])

        # 금액 변환
        df_clean["sales_amount"] = df_clean["sales_amount"].astype("int64")
        df_clean["winner_count_1st"] = df_clean["winner_count_1st"].astype(int)
        df_clean["prize_1st"] = df_clean["prize_1st"].astype("int64")

        # 4. 이상치 탐지
        # 번호 범위 확인 (1-45)
        for col in number_cols:
            invalid_mask = (df_clean[col] < 1) | (df_clean[col] > 45)
            if invalid_mask.any():
                logger.warning(f"{col}: {invalid_mask.sum()}개 이상치 발견")
                df_clean = df_clean[~invalid_mask]

        # 5. 정렬
        df_clean = df_clean.sort_values("round").reset_index(drop=True)

        logger.info(f"데이터 정제 완료: {len(df_clean)}개 회차")

        return df_clean

    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """파생 특징 추가

        Args:
            df: 원본 DataFrame

        Returns:
            특징이 추가된 DataFrame
        """
        logger.info("파생 특징 추가...")

        df_feat = df.copy()

        # 1. 번호 배열 생성
        df_feat["numbers"] = df_feat[
            ["num1", "num2", "num3", "num4", "num5", "num6"]
        ].values.tolist()

        # 2. 날짜 관련 특징
        df_feat["year"] = df_feat["draw_date"].dt.year
        df_feat["month"] = df_feat["draw_date"].dt.month
        df_feat["day"] = df_feat["draw_date"].dt.day
        df_feat["day_of_week"] = df_feat["draw_date"].dt.dayofweek
        df_feat["quarter"] = df_feat["draw_date"].dt.quarter

        # 3. 번호 통계 특징
        df_feat["sum"] = df_feat[
            ["num1", "num2", "num3", "num4", "num5", "num6"]
        ].sum(axis=1)
        df_feat["mean"] = df_feat[
            ["num1", "num2", "num3", "num4", "num5", "num6"]
        ].mean(axis=1)
        df_feat["std"] = df_feat[
            ["num1", "num2", "num3", "num4", "num5", "num6"]
        ].std(axis=1)
        df_feat["min"] = df_feat[
            ["num1", "num2", "num3", "num4", "num5", "num6"]
        ].min(axis=1)
        df_feat["max"] = df_feat[
            ["num1", "num2", "num3", "num4", "num5", "num6"]
        ].max(axis=1)
        df_feat["range"] = df_feat["max"] - df_feat["min"]

        # 4. 홀짝 분석
        number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]
        df_feat["odd_count"] = (df_feat[number_cols] % 2 == 1).sum(axis=1)
        df_feat["even_count"] = 6 - df_feat["odd_count"]
        df_feat["odd_ratio"] = df_feat["odd_count"] / 6

        # 5. 소수 개수
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

        primes = {
            2,
            3,
            5,
            7,
            11,
            13,
            17,
            19,
            23,
            29,
            31,
            37,
            41,
            43,
        }  # 1-45 범위 소수
        df_feat["prime_count"] = df_feat[number_cols].apply(
            lambda row: sum(1 for x in row if x in primes), axis=1
        )

        # 6. 연속 번호 개수
        def count_consecutive(numbers):
            count = 0
            for i in range(len(numbers) - 1):
                if numbers[i + 1] - numbers[i] == 1:
                    count += 1
            return count

        df_feat["consecutive_count"] = df_feat["numbers"].apply(count_consecutive)

        # 7. 구간별 분포 (1-10, 11-20, 21-30, 31-40, 41-45)
        def get_range_distribution(numbers):
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
            return ranges

        range_dist = df_feat["numbers"].apply(get_range_distribution)
        df_feat["range_1_10"] = range_dist.apply(lambda x: x[0])
        df_feat["range_11_20"] = range_dist.apply(lambda x: x[1])
        df_feat["range_21_30"] = range_dist.apply(lambda x: x[2])
        df_feat["range_31_40"] = range_dist.apply(lambda x: x[3])
        df_feat["range_41_45"] = range_dist.apply(lambda x: x[4])

        # 8. 끝자리 분석
        def get_last_digits(numbers):
            return [n % 10 for n in numbers]

        df_feat["last_digits"] = df_feat["numbers"].apply(get_last_digits)

        # 9. AC값 (번호 간 차이의 개수)
        def calculate_ac(numbers):
            diffs = set()
            for i in range(len(numbers)):
                for j in range(i + 1, len(numbers)):
                    diffs.add(abs(numbers[i] - numbers[j]))
            return len(diffs)

        df_feat["ac_value"] = df_feat["numbers"].apply(calculate_ac)

        logger.info(f"파생 특징 추가 완료: {len(df_feat.columns)}개 컬럼")

        return df_feat

    def create_number_frequency_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """번호별 출현 빈도 테이블 생성

        Args:
            df: 원본 DataFrame

        Returns:
            번호별 빈도 DataFrame
        """
        number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]

        # 모든 번호를 하나의 시리즈로 합치기
        all_numbers = pd.concat([df[col] for col in number_cols])

        # 빈도 계산
        freq = all_numbers.value_counts().sort_index()

        # DataFrame 생성
        freq_df = pd.DataFrame(
            {
                "number": range(1, 46),
                "frequency": [freq.get(i, 0) for i in range(1, 46)],
            }
        )

        # 비율 계산
        total = freq_df["frequency"].sum()
        freq_df["ratio"] = freq_df["frequency"] / total

        logger.info("번호 빈도 테이블 생성 완료")

        return freq_df

    def create_bonus_frequency_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """보너스 번호 빈도 테이블 생성

        Args:
            df: 원본 DataFrame

        Returns:
            보너스 번호 빈도 DataFrame
        """
        bonus_freq = df["bonus"].value_counts().sort_index()

        freq_df = pd.DataFrame(
            {
                "number": range(1, 46),
                "frequency": [bonus_freq.get(i, 0) for i in range(1, 46)],
            }
        )

        total = freq_df["frequency"].sum()
        freq_df["ratio"] = freq_df["frequency"] / total

        logger.info("보너스 번호 빈도 테이블 생성 완료")

        return freq_df

    def create_co_occurrence_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """번호 간 동반 출현 행렬 생성

        Args:
            df: 원본 DataFrame

        Returns:
            동반 출현 행렬 (45x45)
        """
        # 초기화
        co_matrix = np.zeros((45, 45), dtype=int)

        number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]

        # 각 회차별로 동반 출현 카운트
        for _, row in df.iterrows():
            numbers = sorted([row[col] for col in number_cols])

            for i in range(len(numbers)):
                for j in range(i + 1, len(numbers)):
                    num1, num2 = numbers[i] - 1, numbers[j] - 1
                    co_matrix[num1][num2] += 1
                    co_matrix[num2][num1] += 1

        # DataFrame 변환
        co_df = pd.DataFrame(
            co_matrix, index=range(1, 46), columns=range(1, 46)
        )

        logger.info("동반 출현 행렬 생성 완료")

        return co_df

    def get_recent_trends(
        self, df: pd.DataFrame, n_rounds: int = 20
    ) -> Dict[int, float]:
        """최근 N회차 트렌드 분석

        Args:
            df: 원본 DataFrame
            n_rounds: 분석할 최근 회차 수

        Returns:
            번호별 트렌드 점수 (높을수록 최근에 자주 출현)
        """
        # 최근 N회차
        recent_df = df.tail(n_rounds)

        number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]

        # 번호별 출현 횟수
        all_numbers = pd.concat([recent_df[col] for col in number_cols])
        freq = all_numbers.value_counts().to_dict()

        # 트렌드 점수 (최근 회차일수록 가중치 부여)
        trend_scores = {}

        for number in range(1, 46):
            score = 0
            for idx, (_, row) in enumerate(recent_df.iterrows()):
                numbers = [row[col] for col in number_cols]
                if number in numbers:
                    # 최근일수록 높은 가중치
                    weight = (idx + 1) / n_rounds
                    score += weight

            trend_scores[number] = score

        logger.info(f"최근 {n_rounds}회차 트렌드 분석 완료")

        return trend_scores

    def normalize_data(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """데이터 정규화 (0-1 스케일링)

        Args:
            df: 원본 DataFrame
            columns: 정규화할 컬럼 리스트

        Returns:
            정규화된 DataFrame
        """
        df_norm = df.copy()

        for col in columns:
            if col in df_norm.columns:
                min_val = df_norm[col].min()
                max_val = df_norm[col].max()

                if max_val > min_val:
                    df_norm[f"{col}_norm"] = (df_norm[col] - min_val) / (
                        max_val - min_val
                    )
                else:
                    df_norm[f"{col}_norm"] = 0

        logger.info(f"{len(columns)}개 컬럼 정규화 완료")

        return df_norm

    def export_processed_data(self, df: pd.DataFrame, filename: str) -> bool:
        """전처리된 데이터 내보내기

        Args:
            df: DataFrame
            filename: 파일명

        Returns:
            성공 여부
        """
        try:
            from pathlib import Path
            from ..utils.config import config

            output_path = config.get(
                "storage.processed_data_path", "data/processed/"
            )
            output_path = Path(output_path) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            logger.info(f"전처리 데이터 내보내기 완료: {output_path}")
            return True

        except Exception as e:
            logger.error(f"데이터 내보내기 오류: {e}")
            return False

    def get_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """요약 통계 생성

        Args:
            df: DataFrame

        Returns:
            통계 딕셔너리
        """
        stats = {
            "total_rounds": len(df),
            "date_range": {
                "start": df["draw_date"].min().strftime("%Y-%m-%d"),
                "end": df["draw_date"].max().strftime("%Y-%m-%d"),
            },
            "number_stats": {
                "sum_mean": df["sum"].mean(),
                "sum_std": df["sum"].std(),
                "range_mean": df["range"].mean(),
            },
            "pattern_stats": {
                "avg_odd_count": df["odd_count"].mean(),
                "avg_consecutive": df["consecutive_count"].mean(),
                "avg_prime_count": df["prime_count"].mean(),
            },
        }

        return stats


def main():
    """메인 함수"""
    preprocessor = DataPreprocessor()

    # 데이터 로드
    df = preprocessor.load_data()

    if df.empty:
        print("데이터가 없습니다. 먼저 데이터를 수집하세요.")
        return

    # 데이터 정제
    df_clean = preprocessor.clean_data(df)

    # 특징 추가
    df_feat = preprocessor.add_features(df_clean)

    # 통계 생성
    stats = preprocessor.get_summary_statistics(df_feat)
    print("\n요약 통계:")
    print(f"  총 회차: {stats['total_rounds']}")
    print(f"  기간: {stats['date_range']['start']} ~ {stats['date_range']['end']}")
    print(f"  평균 합계: {stats['number_stats']['sum_mean']:.2f}")
    print(f"  평균 홀수 개수: {stats['pattern_stats']['avg_odd_count']:.2f}")

    # 저장
    preprocessor.export_processed_data(df_feat, "lotto_processed.csv")

    # 번호 빈도 테이블
    freq_df = preprocessor.create_number_frequency_table(df_clean)
    preprocessor.export_processed_data(freq_df, "number_frequency.csv")

    print("\n전처리 완료!")


if __name__ == "__main__":
    main()
