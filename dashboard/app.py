"""Streamlit 메인 대시보드"""

import streamlit as st
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage import StorageManager
from src.data.collector import LottoCollector
from src.data.preprocessor import DataPreprocessor
from src.prediction.predictor import LottoPredictor
from src.prediction.recommender import LottoRecommender

from components.visualizations import (
    plot_frequency_chart,
    plot_range_distribution,
    plot_odd_even_ratio,
    plot_trend_chart,
    plot_correlation_heatmap,
)
from components.predictions import display_predictions, display_prediction_quality
from components.statistics import display_statistics_dashboard

# 페이지 설정
st.set_page_config(
    page_title="로또 6/45 예측 시스템",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
    }

    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin: 1rem 0;
    }

    .number-ball {
        display: inline-block;
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        line-height: 45px;
        text-align: center;
        margin: 0.2rem;
    }

    .disclaimer {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 2rem 0;
        border-radius: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# 세션 상태 초기화
def init_session_state():
    """세션 상태 초기화"""
    if "predictor" not in st.session_state:
        st.session_state.predictor = None

    if "recommender" not in st.session_state:
        st.session_state.recommender = None

    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False

    if "model_trained" not in st.session_state:
        st.session_state.model_trained = False

    if "predictions_generated" not in st.session_state:
        st.session_state.predictions_generated = False


init_session_state()


# 사이드바
def render_sidebar():
    """사이드바 렌더링"""
    st.sidebar.title("⚙️ 설정")

    st.sidebar.markdown("---")

    # 데이터 관리
    st.sidebar.subheader("📊 데이터 관리")

    if st.sidebar.button("🔄 데이터 수집", use_container_width=True):
        with st.spinner("데이터 수집 중..."):
            collector = LottoCollector()
            count = collector.update_latest()

            if count > 0:
                st.sidebar.success(f"✅ {count}개 회차 업데이트 완료!")
            else:
                st.sidebar.info("ℹ️ 이미 최신 데이터입니다.")

    if st.sidebar.button("📥 데이터 로드", use_container_width=True):
        with st.spinner("데이터 로드 중..."):
            st.session_state.predictor = LottoPredictor()
            success = st.session_state.predictor.load_data()

            if success:
                st.session_state.data_loaded = True
                st.sidebar.success("✅ 데이터 로드 완료!")
            else:
                st.sidebar.error("❌ 데이터 로드 실패. 먼저 데이터를 수집하세요.")

    st.sidebar.markdown("---")

    # 모델 관리
    st.sidebar.subheader("🤖 모델 관리")

    if st.sidebar.button(
        "🎓 모델 학습",
        use_container_width=True,
        disabled=not st.session_state.data_loaded,
    ):
        with st.spinner("모델 학습 중... (수 분 소요)"):
            success = st.session_state.predictor.train_model()

            if success:
                st.session_state.model_trained = True
                st.sidebar.success("✅ 모델 학습 완료!")
            else:
                st.sidebar.error("❌ 모델 학습 실패")

    if st.sidebar.button(
        "🎯 번호 예측",
        use_container_width=True,
        disabled=not st.session_state.model_trained,
    ):
        with st.spinner("번호 예측 중..."):
            prediction = st.session_state.predictor.predict_next_draw()

            if prediction:
                st.session_state.recommender = LottoRecommender(
                    st.session_state.predictor
                )
                st.session_state.predictions_generated = True
                st.sidebar.success("✅ 예측 완료!")
            else:
                st.sidebar.error("❌ 예측 실패")

    st.sidebar.markdown("---")

    # 정보
    st.sidebar.subheader("ℹ️ 시스템 정보")

    if st.session_state.predictor and st.session_state.data_loaded:
        df = st.session_state.predictor.df
        st.sidebar.metric("총 회차 수", len(df))
        st.sidebar.metric("최신 회차", df["round"].max())

    st.sidebar.markdown("---")
    st.sidebar.caption("Made with ❤️ by Lotto Prediction Team")


# 메인 콘텐츠
def render_main_content():
    """메인 콘텐츠 렌더링"""

    # 헤더
    st.markdown(
        '<h1 class="main-header">🎰 한국 로또 6/45 번호 예측 시스템</h1>',
        unsafe_allow_html=True,
    )

    st.markdown("### 데이터 기반 통계 분석과 머신러닝을 활용한 로또 번호 예측")

    st.markdown("---")

    # 탭 구성
    tabs = st.tabs(
        [
            "🏠 홈",
            "🎯 예측 결과",
            "📊 통계 분석",
            "📈 시각화",
            "ℹ️ 정보",
        ]
    )

    # 홈 탭
    with tabs[0]:
        render_home_tab()

    # 예측 결과 탭
    with tabs[1]:
        render_prediction_tab()

    # 통계 분석 탭
    with tabs[2]:
        render_statistics_tab()

    # 시각화 탭
    with tabs[3]:
        render_visualization_tab()

    # 정보 탭
    with tabs[4]:
        render_info_tab()


def render_home_tab():
    """홈 탭"""
    st.header("🏠 시작하기")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
        ### 1️⃣ 데이터 수집
        좌측 사이드바에서 **'데이터 수집'** 버튼을 클릭하여
        최신 로또 당첨 데이터를 수집합니다.
        """
        )

    with col2:
        st.info(
            """
        ### 2️⃣ 모델 학습
        수집된 데이터로 **'모델 학습'** 버튼을 클릭하여
        예측 모델을 학습시킵니다.
        """
        )

    with col3:
        st.info(
            """
        ### 3️⃣ 번호 예측
        학습된 모델로 **'번호 예측'** 버튼을 클릭하여
        다음 회차 번호를 예측합니다.
        """
        )

    st.markdown("---")

    # 최신 당첨 결과
    if st.session_state.data_loaded and st.session_state.predictor:
        st.subheader("🎲 최신 당첨 결과")

        df = st.session_state.predictor.df
        latest = df.tail(10)[
            ["round", "draw_date", "num1", "num2", "num3", "num4", "num5", "num6", "bonus"]
        ].copy()

        latest["draw_date"] = latest["draw_date"].dt.strftime("%Y-%m-%d")
        latest = latest.sort_values("round", ascending=False)

        st.dataframe(latest, use_container_width=True, hide_index=True)


def render_prediction_tab():
    """예측 결과 탭"""
    st.header("🎯 예측 결과")

    if not st.session_state.predictions_generated:
        st.warning("⚠️ 먼저 사이드바에서 '번호 예측'을 실행하세요.")
        return

    # 조합 생성 방법 선택
    col1, col2 = st.columns([3, 1])

    with col1:
        method = st.selectbox(
            "조합 생성 방법",
            ["probability", "balanced", "diverse"],
            format_func=lambda x: {
                "probability": "확률 기반 (높은 확률 번호 우선)",
                "balanced": "균형 잡힌 (구간별 고른 분포)",
                "diverse": "다양한 (다양성 극대화)",
            }[x],
        )

    with col2:
        n_combos = st.number_input("조합 개수", min_value=1, max_value=10, value=5)

    if st.button("🔄 조합 생성", use_container_width=True):
        with st.spinner("조합 생성 중..."):
            recommendations = st.session_state.recommender.generate_combinations(
                n_combinations=n_combos, method=method
            )

            if recommendations:
                st.success(f"✅ {len(recommendations)}개 조합 생성 완료!")

    # 예측 결과 표시
    if st.session_state.recommender and st.session_state.recommender.recommendations:
        display_predictions(st.session_state.recommender)

        # 예측 품질
        st.markdown("---")
        display_prediction_quality(st.session_state.predictor)


def render_statistics_tab():
    """통계 분석 탭"""
    st.header("📊 통계 분석")

    if not st.session_state.data_loaded:
        st.warning("⚠️ 먼저 데이터를 로드하세요.")
        return

    display_statistics_dashboard(st.session_state.predictor.df)


def render_visualization_tab():
    """시각화 탭"""
    st.header("📈 데이터 시각화")

    if not st.session_state.data_loaded:
        st.warning("⚠️ 먼저 데이터를 로드하세요.")
        return

    df = st.session_state.predictor.df

    # 빈도 차트
    st.subheader("1️⃣ 번호별 출현 빈도")
    plot_frequency_chart(df)

    st.markdown("---")

    # 구간 분포 & 홀짝 비율
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("2️⃣ 구간별 분포")
        plot_range_distribution(df)

    with col2:
        st.subheader("3️⃣ 홀짝 비율")
        plot_odd_even_ratio(df)

    st.markdown("---")

    # 트렌드 차트
    st.subheader("4️⃣ 최근 트렌드")
    plot_trend_chart(df)

    st.markdown("---")

    # 상관관계 히트맵
    st.subheader("5️⃣ 번호 간 상관관계")
    plot_correlation_heatmap(df)


def render_info_tab():
    """정보 탭"""
    st.header("ℹ️ 시스템 정보")

    st.markdown(
        """
    ## 🎯 시스템 개요

    본 시스템은 한국 동행복권의 로또 6/45 과거 당첨 데이터를 분석하여
    다음 회차 번호를 예측하는 데이터 기반 시스템입니다.

    ### 📊 데이터 분석

    - **통계 분석**: 번호별 출현 빈도, 간격, 패턴 등 기초 통계
    - **패턴 분석**: 연속 번호, 홀짝 비율, 구간별 분포 등
    - **트렌드 분석**: 최근 상승/하락 트렌드 파악

    ### 🤖 머신러닝 모델

    - **통계 모델**: 가중 빈도 기반 확률 계산
    - **Random Forest**: 패턴 학습 및 특징 중요도 분석
    - **XGBoost**: 고급 그래디언트 부스팅
    - **앙상블**: 여러 모델의 예측을 가중 평균

    ### 🎲 예측 방법

    1. 각 번호(1-45)의 출현 확률을 예측
    2. 확률 기반으로 6개 번호 조합 생성
    3. 조합의 전체 확률 및 신뢰도 계산
    4. 상위 5개 조합을 확률순으로 추천

    ### 📈 특징

    - **실시간 업데이트**: 최신 당첨 데이터 자동 수집
    - **다양한 조합**: 확률/균형/다양성 기반 조합 생성
    - **예측 근거**: 각 조합의 선정 이유 제공
    - **시각화**: 다양한 차트로 데이터 분석 결과 표시
    """
    )

    st.markdown("---")

    # 면책 조항
    st.markdown(
        """
    <div class="disclaimer">
        <h3>⚠️ 면책 조항</h3>
        <p>
        <strong>본 시스템은 교육 및 연구 목적으로 개발되었습니다.</strong>
        </p>
        <ul>
            <li>로또는 완전한 무작위 추첨이며, 과거 데이터로 미래를 예측할 수 없습니다.</li>
            <li>본 시스템의 예측은 통계적 패턴 분석일 뿐, <strong>실제 당첨을 보장하지 않습니다.</strong></li>
            <li>투자 손실에 대한 책임은 사용자에게 있습니다.</li>
            <li>로또 구매는 개인의 판단 하에 신중히 결정하시기 바랍니다.</li>
        </ul>
        <p style="margin-top: 1rem;">
        <strong>로또는 오락입니다. 즐겁게, 그리고 책임감 있게!</strong> 🎲
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


# 메인 실행
def main():
    """메인 함수"""
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()
