"""예측 결과 표시 컴포넌트"""

import streamlit as st
import pandas as pd
from typing import Dict, Any


def display_number_balls(numbers: list, bonus: int = None):
    """번호 공 표시

    Args:
        numbers: 번호 리스트
        bonus: 보너스 번호
    """
    html = '<div style="text-align: center; margin: 1rem 0;">'

    for num in numbers:
        html += f'<span class="number-ball">{num}</span>'

    if bonus:
        html += f'<span style="margin: 0 1rem; font-size: 1.5rem;">+</span>'
        html += f'<span class="number-ball" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">{bonus}</span>'

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def display_predictions(recommender):
    """예측 조합 표시

    Args:
        recommender: LottoRecommender 인스턴스
    """
    recommendations = recommender.get_recommendations()

    if not recommendations:
        st.warning("추천 조합이 없습니다.")
        return

    st.subheader(f"🎯 추천 조합 Top {len(recommendations)}")

    for combo in recommendations:
        with st.expander(
            f"**[{combo['rank']}위]** 확률: {combo['probability']:.4f} | 신뢰도: {combo['confidence']:.2%}",
            expanded=(combo["rank"] <= 2),
        ):
            # 번호 표시
            display_number_balls(combo["numbers"], combo["bonus"])

            # 상세 정보
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("조합 확률", f"{combo['probability']:.4f}")

            with col2:
                st.metric("신뢰도", f"{combo['confidence']:.2%}")

            with col3:
                st.metric("번호 합계", combo["reasoning"]["number_sum"])

            # 근거
            st.markdown("**📋 예측 근거**")

            reasoning = combo["reasoning"]

            col1, col2 = st.columns(2)

            with col1:
                st.info(
                    f"""
                **🔥 고빈도 번호**
                {', '.join(map(str, reasoning['high_frequency_numbers'])) if reasoning['high_frequency_numbers'] else '없음'}

                **📈 트렌드 번호**
                {', '.join(map(str, reasoning['trending_numbers'][:5])) if reasoning['trending_numbers'] else '없음'}
                """
                )

            with col2:
                st.info(
                    f"""
                **⚖️ 홀짝 비율**
                {reasoning['odd_even_ratio']}

                **🔢 연속 번호**
                {', '.join(map(str, reasoning['consecutive_numbers'])) if reasoning['consecutive_numbers'] else '없음'}
                """
                )

            # 구간 분포
            st.markdown("**📊 구간별 분포**")

            dist_df = pd.DataFrame(
                [reasoning["range_distribution"]],
                columns=["1-10", "11-20", "21-30", "31-40", "41-45"],
            )

            st.dataframe(dist_df, use_container_width=True, hide_index=True)


def display_prediction_quality(predictor):
    """예측 품질 표시

    Args:
        predictor: LottoPredictor 인스턴스
    """
    st.subheader("📊 예측 품질 분석")

    quality = predictor.analyze_prediction_quality()

    if not quality:
        st.warning("예측 품질 정보가 없습니다.")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "예측 엔트로피",
            f"{quality['entropy']:.2f}",
            help="낮을수록 확신이 높음",
        )

    with col2:
        st.metric(
            "평균 분산",
            f"{quality['prediction_variance']['mean']:.4f}",
            help="모델 간 불일치도 (낮을수록 일치)",
        )

    with col3:
        st.metric(
            "다양성 점수",
            f"{quality['diversity_score']:.2%}",
            help="상위 20개 번호 다양성",
        )

    # 모델 합의 번호
    if quality["model_consensus"]:
        st.info(
            f"""
        **🤝 모델 합의 번호 (모든 모델이 높게 평가)**
        {', '.join(map(str, quality['model_consensus']))}
        """
        )


def display_number_probabilities(predictor):
    """번호별 확률 표시

    Args:
        predictor: LottoPredictor 인스턴스
    """
    proba_df = predictor.get_number_probabilities()

    if proba_df.empty:
        st.warning("확률 정보가 없습니다.")
        return

    st.subheader("📈 번호별 출현 확률")

    # 상위 20개
    top_20 = proba_df.head(20).copy()
    top_20["probability_pct"] = (top_20["probability"] * 100).round(2)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**상위 1-10위**")
        st.dataframe(
            top_20.head(10)[["number", "probability_pct"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "number": "번호",
                "probability_pct": st.column_config.NumberColumn(
                    "확률 (%)", format="%.2f%%"
                ),
            },
        )

    with col2:
        st.markdown("**상위 11-20위**")
        st.dataframe(
            top_20.tail(10)[["number", "probability_pct"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "number": "번호",
                "probability_pct": st.column_config.NumberColumn(
                    "확률 (%)", format="%.2f%%"
                ),
            },
        )


def display_model_info(predictor):
    """모델 정보 표시

    Args:
        predictor: LottoPredictor 인스턴스
    """
    if not predictor.model:
        st.warning("모델 정보가 없습니다.")
        return

    st.subheader("🤖 모델 정보")

    model_summary = predictor.model.get_summary()

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            f"""
        **모델 이름**
        {model_summary['name']}

        **학습 상태**
        {'✅ 학습 완료' if model_summary['is_trained'] else '❌ 미학습'}

        **사용 모델 수**
        {model_summary['n_models']}개
        """
        )

    with col2:
        st.info(
            f"""
        **모델 구성**
        {', '.join(model_summary['models'].values())}

        **가중치**
        {' | '.join([f'{k}: {v:.2f}' for k, v in model_summary['weights'].items()])}
        """
        )
