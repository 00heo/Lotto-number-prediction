"""통계 대시보드 컴포넌트"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.statistics import StatisticalAnalyzer
from src.analysis.patterns import PatternAnalyzer


def display_statistics_dashboard(df: pd.DataFrame):
    """통계 대시보드 표시

    Args:
        df: 로또 데이터 DataFrame
    """
    analyzer = StatisticalAnalyzer(df)
    pattern_analyzer = PatternAnalyzer(df)

    # 기본 통계
    st.subheader("📊 기본 통계")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 회차 수", len(df))

    with col2:
        st.metric("최신 회차", df["round"].max())

    with col3:
        latest_date = df["draw_date"].max().strftime("%Y-%m-%d")
        st.metric("최신 추첨일", latest_date)

    with col4:
        sum_mean = df[["num1", "num2", "num3", "num4", "num5", "num6"]].sum(axis=1).mean()
        st.metric("평균 번호 합계", f"{sum_mean:.1f}")

    st.markdown("---")

    # 핫/콜드 번호
    st.subheader("🔥 핫/콜드 번호")

    col1, col2 = st.columns(2)

    hot_cold = analyzer.calculate_hot_cold_numbers(recent_n=20)

    with col1:
        st.success(
            f"""
        **🔥 핫 번호 (최근 20회차 고빈도)**
        {', '.join(map(str, hot_cold['hot']))}
        """
        )

    with col2:
        st.info(
            f"""
        **❄️ 콜드 번호 (최근 20회차 저빈도)**
        {', '.join(map(str, hot_cold['cold']))}
        """
        )

    st.markdown("---")

    # 번호 합계 통계
    st.subheader("🔢 번호 합계 통계")

    sum_stats = analyzer.calculate_sum_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("평균", f"{sum_stats['mean']:.1f}")

    with col2:
        st.metric("중앙값", f"{sum_stats['median']:.1f}")

    with col3:
        st.metric("최소값", sum_stats['min'])

    with col4:
        st.metric("최대값", sum_stats['max'])

    st.markdown("---")

    # 패턴 통계
    st.subheader("🎨 패턴 분석")

    consecutive_pattern = pattern_analyzer.analyze_consecutive_patterns()
    sum_pattern = pattern_analyzer.analyze_sum_patterns()

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            f"""
        **연속 번호 패턴**
        - 연속 번호 포함 회차: {consecutive_pattern['rounds_with_consecutive']}회
        - 연속 번호 없는 회차: {consecutive_pattern['rounds_without_consecutive']}회
        - 평균 연속 그룹 수: {consecutive_pattern['avg_consecutive_count']:.2f}개
        """
        )

    with col2:
        quartiles = sum_pattern['quartiles']
        st.info(
            f"""
        **합계 분포**
        - 25% 분위수: {quartiles['q25']:.0f}
        - 50% 분위수: {quartiles['q50']:.0f}
        - 75% 분위수: {quartiles['q75']:.0f}
        - 표준편차: {sum_pattern['std']:.1f}
        """
        )

    st.markdown("---")

    # 간격 통계
    st.subheader("📏 번호별 출현 간격")

    gap_stats = analyzer.calculate_gap_statistics()

    # 현재 간격이 큰 순서대로 정렬
    gap_stats_sorted = gap_stats.sort_values("current_gap", ascending=False).head(10)

    st.dataframe(
        gap_stats_sorted[
            [
                "number",
                "appearances",
                "gap_mean",
                "gap_std",
                "last_round",
                "current_gap",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "number": "번호",
            "appearances": "출현 횟수",
            "gap_mean": st.column_config.NumberColumn("평균 간격", format="%.1f"),
            "gap_std": st.column_config.NumberColumn("간격 표준편차", format="%.1f"),
            "last_round": "마지막 출현 회차",
            "current_gap": "현재 간격",
        },
    )

    st.caption("※ 현재 간격이 큰 상위 10개 번호 (오랫동안 나오지 않은 번호)")

    st.markdown("---")

    # 무작위성 검정
    st.subheader("🎲 무작위성 검정")

    randomness = analyzer.test_randomness()

    col1, col2 = st.columns(2)

    with col1:
        chi_square = randomness['chi_square']
        is_uniform = "✅ 균등 분포" if chi_square['is_uniform'] else "❌ 불균등 분포"

        st.info(
            f"""
        **카이제곱 검정 (균등 분포 검정)**
        - χ² 통계량: {chi_square['statistic']:.2f}
        - p-value: {chi_square['p_value']:.4f}
        - 결과: {is_uniform}
        """
        )

    with col2:
        runs_test = randomness['runs_test']
        is_random = "✅ 무작위" if runs_test['is_random'] else "❌ 패턴 존재"

        st.info(
            f"""
        **런 테스트 (무작위성 검정)**
        - 런 수: {runs_test['runs']}
        - Z-점수: {runs_test['z_score']:.2f}
        - 결과: {is_random}
        """
        )

    st.caption(
        """
    ※ 카이제곱 검정: 번호별 출현 빈도가 균등한지 검정 (p > 0.05: 균등)
    ※ 런 테스트: 연속성이 무작위인지 검정 (|Z| < 1.96: 무작위)
    """
    )
