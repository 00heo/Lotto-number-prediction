"""로또 데이터 수집 모듈"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import re
from loguru import logger
from tqdm import tqdm

from ..utils.config import config
from .storage import StorageManager


class LottoCollector:
    """로또 데이터 수집 클래스"""

    def __init__(self, storage: Optional[StorageManager] = None):
        """초기화

        Args:
            storage: StorageManager 인스턴스
        """
        self.base_url = config.get(
            "data_collection.source_url",
            "https://data.soledot.com/lottowinnumber/fo/lottowinnumberlist.sd",
        )
        self.timeout = config.get("data_collection.timeout", 30)
        self.max_retries = config.get("data_collection.max_retries", 3)

        self.storage = storage if storage else StorageManager()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            }
        )

        logger.info("LottoCollector 초기화 완료")

    def _fetch_page(self, page: int = 1) -> Optional[str]:
        """페이지 HTML 가져오기

        Args:
            page: 페이지 번호

        Returns:
            HTML 문자열
        """
        url = f"{self.base_url}?page={page}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = "utf-8"

                logger.debug(f"페이지 {page} 요청 성공")
                return response.text

            except requests.exceptions.RequestException as e:
                logger.warning(f"페이지 {page} 요청 실패 ({attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    logger.error(f"페이지 {page} 요청 최종 실패")
                    return None

        return None

    def _parse_number(self, text: str) -> Optional[int]:
        """텍스트에서 숫자 파싱

        Args:
            text: 텍스트

        Returns:
            숫자 또는 None
        """
        try:
            # 숫자만 추출
            number = re.sub(r"[^\d]", "", text)
            return int(number) if number else None
        except:
            return None

    def _parse_date(self, text: str) -> Optional[str]:
        """날짜 파싱

        Args:
            text: 날짜 텍스트

        Returns:
            YYYY-MM-DD 형식 날짜
        """
        try:
            # 다양한 날짜 형식 처리
            text = text.strip()

            # YYYY-MM-DD 또는 YYYY.MM.DD 또는 YYYY/MM/DD
            date_match = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", text)
            if date_match:
                year, month, day = date_match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            return None

        except Exception as e:
            logger.warning(f"날짜 파싱 오류: {text} - {e}")
            return None

    def _parse_result_row(self, row) -> Optional[Dict[str, Any]]:
        """결과 행 파싱

        Args:
            row: BeautifulSoup 테이블 행

        Returns:
            파싱된 데이터 딕셔너리
        """
        try:
            cells = row.find_all("td")
            if len(cells) < 7:
                return None

            # 회차 번호
            round_num = self._parse_number(cells[0].get_text(strip=True))
            if not round_num:
                return None

            # 추첨일
            draw_date = self._parse_date(cells[1].get_text(strip=True))

            # 당첨 번호 6개
            numbers = []
            for i in range(2, 8):  # 2-7번째 셀
                num = self._parse_number(cells[i].get_text(strip=True))
                if num:
                    numbers.append(num)

            if len(numbers) != 6:
                logger.warning(f"회차 {round_num}: 당첨 번호가 6개가 아님")
                return None

            # 번호 정렬
            numbers.sort()

            # 보너스 번호
            bonus = None
            if len(cells) > 8:
                bonus = self._parse_number(cells[8].get_text(strip=True))

            # 추가 정보 (판매금액, 당첨자수, 상금 등)
            sales_amount = None
            winner_count_1st = None
            prize_1st = None

            if len(cells) > 9:
                sales_amount = self._parse_number(cells[9].get_text(strip=True))

            if len(cells) > 10:
                winner_count_1st = self._parse_number(cells[10].get_text(strip=True))

            if len(cells) > 11:
                prize_1st = self._parse_number(cells[11].get_text(strip=True))

            data = {
                "round": round_num,
                "draw_date": draw_date,
                "num1": numbers[0],
                "num2": numbers[1],
                "num3": numbers[2],
                "num4": numbers[3],
                "num5": numbers[4],
                "num6": numbers[5],
                "bonus": bonus,
                "sales_amount": sales_amount,
                "winner_count_1st": winner_count_1st,
                "prize_1st": prize_1st,
            }

            return data

        except Exception as e:
            logger.warning(f"행 파싱 오류: {e}")
            return None

    def _parse_page(self, html: str) -> List[Dict[str, Any]]:
        """페이지 파싱

        Args:
            html: HTML 문자열

        Returns:
            파싱된 데이터 리스트
        """
        results = []

        try:
            soup = BeautifulSoup(html, "lxml")

            # 테이블 찾기
            tables = soup.find_all("table")

            for table in tables:
                rows = table.find_all("tr")

                for row in rows:
                    # 헤더 행 스킵
                    if row.find("th"):
                        continue

                    data = self._parse_result_row(row)
                    if data:
                        results.append(data)

        except Exception as e:
            logger.error(f"페이지 파싱 오류: {e}")

        return results

    def collect_page(self, page: int = 1) -> List[Dict[str, Any]]:
        """단일 페이지 수집

        Args:
            page: 페이지 번호

        Returns:
            수집된 데이터 리스트
        """
        html = self._fetch_page(page)
        if not html:
            return []

        results = self._parse_page(html)
        logger.info(f"페이지 {page}: {len(results)}개 수집")

        return results

    def collect_all(
        self, start_page: int = 1, max_pages: Optional[int] = None, save: bool = True
    ) -> List[Dict[str, Any]]:
        """전체 데이터 수집

        Args:
            start_page: 시작 페이지
            max_pages: 최대 페이지 수 (None이면 전체)
            save: 데이터베이스 저장 여부

        Returns:
            수집된 전체 데이터 리스트
        """
        all_results = []
        page = start_page
        consecutive_empty = 0

        logger.info("전체 데이터 수집 시작...")

        # 진행바 (최대 페이지 추정: 1200회차 / 10개 = 120페이지)
        estimated_pages = max_pages if max_pages else 120

        with tqdm(total=estimated_pages, desc="데이터 수집") as pbar:
            while True:
                # 최대 페이지 체크
                if max_pages and page > start_page + max_pages - 1:
                    break

                # 페이지 수집
                results = self.collect_page(page)

                if not results:
                    consecutive_empty += 1
                    if consecutive_empty >= 3:
                        logger.info(f"3개 연속 빈 페이지 감지. 수집 종료.")
                        break
                else:
                    consecutive_empty = 0
                    all_results.extend(results)

                pbar.update(1)
                page += 1

                # 요청 간 딜레이 (서버 부하 방지)
                time.sleep(0.5)

        logger.info(f"전체 수집 완료: {len(all_results)}개")

        # 데이터베이스 저장
        if save and all_results:
            saved_count = self.storage.insert_batch(all_results)
            logger.info(f"데이터베이스 저장: {saved_count}개")

        return all_results

    def update_latest(self) -> int:
        """최신 데이터 업데이트 (증분 수집)

        Returns:
            업데이트된 개수
        """
        logger.info("최신 데이터 업데이트 시작...")

        # 현재 최신 회차 확인
        latest_round = self.storage.get_latest_round()
        if latest_round:
            logger.info(f"현재 최신 회차: {latest_round}")
        else:
            logger.info("저장된 데이터 없음. 전체 수집 수행.")
            results = self.collect_all()
            return len(results)

        # 첫 페이지만 수집하여 최신 데이터 확인
        new_results = []
        page = 1

        while True:
            results = self.collect_page(page)
            if not results:
                break

            # 새로운 데이터만 필터링
            for result in results:
                if result["round"] > latest_round:
                    new_results.append(result)
                else:
                    # 이미 있는 데이터 도달 -> 종료
                    break

            # 이미 있는 데이터에 도달했으면 종료
            if any(r["round"] <= latest_round for r in results):
                break

            page += 1
            time.sleep(0.5)

        # 저장
        if new_results:
            saved_count = self.storage.insert_batch(new_results)
            logger.info(f"최신 데이터 업데이트 완료: {saved_count}개")
            return saved_count
        else:
            logger.info("업데이트할 새로운 데이터 없음")
            return 0

    def collect_round(self, round_num: int) -> Optional[Dict[str, Any]]:
        """특정 회차 수집

        Args:
            round_num: 회차 번호

        Returns:
            수집된 데이터
        """
        # 이미 DB에 있는지 확인
        existing = self.storage.get_result_by_round(round_num)
        if existing:
            logger.info(f"회차 {round_num}: 이미 존재함")
            return existing

        # 페이지 추정 (역순 정렬 가정, 10개/페이지)
        latest_round = self.get_latest_round_from_web()
        if not latest_round:
            logger.warning("최신 회차 확인 실패")
            return None

        estimated_page = (latest_round - round_num) // 10 + 1

        # 해당 페이지 수집
        for page in range(max(1, estimated_page - 1), estimated_page + 2):
            results = self.collect_page(page)

            for result in results:
                if result["round"] == round_num:
                    self.storage.insert_result(result)
                    logger.info(f"회차 {round_num} 수집 완료")
                    return result

        logger.warning(f"회차 {round_num}을 찾을 수 없음")
        return None

    def get_latest_round_from_web(self) -> Optional[int]:
        """웹에서 최신 회차 번호 확인

        Returns:
            최신 회차 번호
        """
        results = self.collect_page(1)
        if results:
            return max(r["round"] for r in results)
        return None


def main():
    """메인 함수 (CLI 실행용)"""
    import argparse

    parser = argparse.ArgumentParser(description="로또 데이터 수집")
    parser.add_argument(
        "--update", action="store_true", help="최신 데이터만 업데이트"
    )
    parser.add_argument("--pages", type=int, help="수집할 최대 페이지 수")
    parser.add_argument("--round", type=int, help="특정 회차 수집")

    args = parser.parse_args()

    collector = LottoCollector()

    if args.round:
        # 특정 회차 수집
        result = collector.collect_round(args.round)
        if result:
            print(f"회차 {args.round} 수집 완료: {result}")
        else:
            print(f"회차 {args.round} 수집 실패")

    elif args.update:
        # 최신 데이터만 업데이트
        count = collector.update_latest()
        print(f"최신 데이터 {count}개 업데이트 완료")

    else:
        # 전체 수집
        results = collector.collect_all(max_pages=args.pages)
        print(f"전체 {len(results)}개 수집 완료")

        # 통계 출력
        stats = collector.storage.get_statistics()
        print(f"\n데이터베이스 통계:")
        print(f"  총 회차: {stats.get('total_rounds', 0)}개")
        print(f"  회차 범위: {stats.get('min_round', 0)} ~ {stats.get('max_round', 0)}")


if __name__ == "__main__":
    main()
