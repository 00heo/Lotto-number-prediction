"""데이터 저장 관리 모듈"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from ..utils.config import config
from ..utils.validators import validate_numbers, validate_round


class StorageManager:
    """데이터베이스 관리 클래스"""

    def __init__(self, db_path: Optional[str] = None):
        """초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        if db_path is None:
            db_path = config.get("storage.database_path", "data/lotto.db")

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._create_tables()
        logger.info(f"데이터베이스 초기화 완료: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환

        Returns:
            sqlite3 연결 객체
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self) -> None:
        """테이블 생성"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 로또 결과 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lotto_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round INTEGER UNIQUE NOT NULL,
                    draw_date DATE NOT NULL,
                    num1 INTEGER NOT NULL,
                    num2 INTEGER NOT NULL,
                    num3 INTEGER NOT NULL,
                    num4 INTEGER NOT NULL,
                    num5 INTEGER NOT NULL,
                    num6 INTEGER NOT NULL,
                    bonus INTEGER NOT NULL,
                    sales_amount BIGINT,
                    winner_count_1st INTEGER,
                    prize_1st BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스 생성
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_round ON lotto_results(round)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_date ON lotto_results(draw_date)"
            )

            conn.commit()
            logger.info("데이터베이스 테이블 생성 완료")

    def insert_result(self, data: Dict[str, Any]) -> bool:
        """로또 결과 삽입

        Args:
            data: 로또 결과 데이터

        Returns:
            성공 여부
        """
        try:
            # 데이터 검증
            numbers = [
                data["num1"],
                data["num2"],
                data["num3"],
                data["num4"],
                data["num5"],
                data["num6"],
            ]
            validate_numbers(numbers, data["bonus"])
            validate_round(data["round"])

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO lotto_results
                    (round, draw_date, num1, num2, num3, num4, num5, num6, bonus,
                     sales_amount, winner_count_1st, prize_1st, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data["round"],
                        data["draw_date"],
                        data["num1"],
                        data["num2"],
                        data["num3"],
                        data["num4"],
                        data["num5"],
                        data["num6"],
                        data["bonus"],
                        data.get("sales_amount"),
                        data.get("winner_count_1st"),
                        data.get("prize_1st"),
                        datetime.now(),
                    ),
                )
                conn.commit()

            logger.info(f"회차 {data['round']} 데이터 저장 완료")
            return True

        except Exception as e:
            logger.error(f"데이터 삽입 오류: {e}")
            return False

    def insert_batch(self, data_list: List[Dict[str, Any]]) -> int:
        """로또 결과 일괄 삽입

        Args:
            data_list: 로또 결과 리스트

        Returns:
            삽입된 개수
        """
        success_count = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for data in data_list:
                try:
                    # 데이터 검증
                    numbers = [
                        data["num1"],
                        data["num2"],
                        data["num3"],
                        data["num4"],
                        data["num5"],
                        data["num6"],
                    ]
                    validate_numbers(numbers, data["bonus"])

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO lotto_results
                        (round, draw_date, num1, num2, num3, num4, num5, num6, bonus,
                         sales_amount, winner_count_1st, prize_1st, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            data["round"],
                            data["draw_date"],
                            data["num1"],
                            data["num2"],
                            data["num3"],
                            data["num4"],
                            data["num5"],
                            data["num6"],
                            data["bonus"],
                            data.get("sales_amount"),
                            data.get("winner_count_1st"),
                            data.get("prize_1st"),
                            datetime.now(),
                        ),
                    )
                    success_count += 1

                except Exception as e:
                    logger.warning(f"회차 {data.get('round')} 삽입 실패: {e}")

            conn.commit()

        logger.info(f"일괄 삽입 완료: {success_count}/{len(data_list)}개")
        return success_count

    def get_result_by_round(self, round_num: int) -> Optional[Dict[str, Any]]:
        """회차별 결과 조회

        Args:
            round_num: 회차 번호

        Returns:
            로또 결과 딕셔너리
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM lotto_results WHERE round = ?
                """,
                    (round_num,),
                )

                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None

        except Exception as e:
            logger.error(f"회차 조회 오류: {e}")
            return None

    def get_all_results(self, order_by: str = "round DESC") -> pd.DataFrame:
        """전체 결과 조회

        Args:
            order_by: 정렬 기준

        Returns:
            pandas DataFrame
        """
        try:
            query = f"SELECT * FROM lotto_results ORDER BY {order_by}"

            with self._get_connection() as conn:
                df = pd.read_sql_query(query, conn)

            logger.info(f"전체 데이터 조회 완료: {len(df)}개")
            return df

        except Exception as e:
            logger.error(f"전체 데이터 조회 오류: {e}")
            return pd.DataFrame()

    def get_latest_round(self) -> Optional[int]:
        """최신 회차 번호 반환

        Returns:
            최신 회차 번호
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(round) as max_round FROM lotto_results")
                row = cursor.fetchone()

                if row and row["max_round"]:
                    return row["max_round"]
                return None

        except Exception as e:
            logger.error(f"최신 회차 조회 오류: {e}")
            return None

    def get_results_range(
        self, start_round: int, end_round: Optional[int] = None
    ) -> pd.DataFrame:
        """회차 범위 조회

        Args:
            start_round: 시작 회차
            end_round: 종료 회차 (None이면 최신까지)

        Returns:
            pandas DataFrame
        """
        try:
            if end_round is None:
                query = "SELECT * FROM lotto_results WHERE round >= ? ORDER BY round"
                params = (start_round,)
            else:
                query = "SELECT * FROM lotto_results WHERE round BETWEEN ? AND ? ORDER BY round"
                params = (start_round, end_round)

            with self._get_connection() as conn:
                df = pd.read_sql_query(query, conn, params=params)

            logger.info(f"범위 조회 완료: {len(df)}개")
            return df

        except Exception as e:
            logger.error(f"범위 조회 오류: {e}")
            return pd.DataFrame()

    def export_to_csv(self, output_path: Optional[str] = None) -> bool:
        """CSV로 내보내기

        Args:
            output_path: 출력 파일 경로

        Returns:
            성공 여부
        """
        try:
            if output_path is None:
                output_path = config.get(
                    "storage.processed_data_path", "data/processed/"
                )
                output_path = Path(output_path) / "lotto_results.csv"
            else:
                output_path = Path(output_path)

            output_path.parent.mkdir(parents=True, exist_ok=True)

            df = self.get_all_results()
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            logger.info(f"CSV 내보내기 완료: {output_path}")
            return True

        except Exception as e:
            logger.error(f"CSV 내보내기 오류: {e}")
            return False

    def import_from_csv(self, csv_path: str) -> int:
        """CSV에서 가져오기

        Args:
            csv_path: CSV 파일 경로

        Returns:
            가져온 개수
        """
        try:
            df = pd.read_csv(csv_path)

            # DataFrame을 딕셔너리 리스트로 변환
            data_list = df.to_dict("records")

            # 일괄 삽입
            count = self.insert_batch(data_list)

            logger.info(f"CSV 가져오기 완료: {count}개")
            return count

        except Exception as e:
            logger.error(f"CSV 가져오기 오류: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """데이터베이스 통계 반환

        Returns:
            통계 정보 딕셔너리
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # 전체 회차 수
                cursor.execute("SELECT COUNT(*) as total FROM lotto_results")
                total = cursor.fetchone()["total"]

                # 최신/최초 회차
                cursor.execute(
                    "SELECT MIN(round) as min_round, MAX(round) as max_round FROM lotto_results"
                )
                rounds = cursor.fetchone()

                # 최신 업데이트 시간
                cursor.execute("SELECT MAX(updated_at) as last_update FROM lotto_results")
                last_update = cursor.fetchone()["last_update"]

                stats = {
                    "total_rounds": total,
                    "min_round": rounds["min_round"],
                    "max_round": rounds["max_round"],
                    "last_update": last_update,
                }

                return stats

        except Exception as e:
            logger.error(f"통계 조회 오류: {e}")
            return {}

    def delete_round(self, round_num: int) -> bool:
        """회차 삭제

        Args:
            round_num: 삭제할 회차

        Returns:
            성공 여부
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM lotto_results WHERE round = ?", (round_num,))
                conn.commit()

            logger.info(f"회차 {round_num} 삭제 완료")
            return True

        except Exception as e:
            logger.error(f"회차 삭제 오류: {e}")
            return False

    def clear_all(self) -> bool:
        """전체 데이터 삭제

        Returns:
            성공 여부
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM lotto_results")
                conn.commit()

            logger.warning("전체 데이터 삭제 완료")
            return True

        except Exception as e:
            logger.error(f"전체 삭제 오류: {e}")
            return False
