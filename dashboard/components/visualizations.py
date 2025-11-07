"""시각화 컴포넌트"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.statistics import StatisticalAnalyzer


def plot_frequency_chart(df: pd.DataFrame, recent_n: int = None):
    """번호별 출현 빈도 차트

    Args:
        df: 로또 데이터 DataFrame
        recent_n: 최근 N회차 (None이면 전체)
    """
    analyzer = StatisticalAnalyzer(df)
    frequency = analyzer.calculate_frequency(recent_n)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=list(range(1, 46)),
            y=frequency.values,
            marker=dict(
                color=frequency.values,
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="출현 횟수"),
            ),
            text=frequency.values,
            textposition="outside",
            hovertemplate="번호: %{x}<br>출현 횟수: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        title=f"번호별 출현 빈도 ({'전체' if recent_n is None else f'최근 {recent_n}회차'})",
        xaxis_title="번호",
        yaxis_title="출현 횟수",
        template="plotly_white",
        height=500,
        xaxis=dict(tickmode="linear", tick0=1, dtick=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_range_distribution(df: pd.DataFrame):
    """구간별 분포 파이 차트

    Args:
        df: 로또 데이터 DataFrame
    """
    number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]

    ranges = {
        "1-10": 0,
        "11-20": 0,
        "21-30": 0,
        "31-40": 0,
        "41-45": 0,
    }

    for col in number_cols:
        for num in df[col]:
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

    fig = go.Figure(
        data=[
            go.Pie(
                labels=list(ranges.keys()),
                values=list(ranges.values()),
                hole=0.4,
                marker=dict(colors=px.colors.sequential.Viridis),
            )
        ]
    )

    fig.update_layout(
        title="구간별 번호 분포",
        template="plotly_white",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_odd_even_ratio(df: pd.DataFrame):
    """홀짝 비율 차트

    Args:
        df: 로또 데이터 DataFrame
    """
    number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]

    odd_counts = (df[number_cols] % 2 == 1).sum(axis=1)
    odd_count_dist = odd_counts.value_counts().sort_index()

    fig = go.Figure(
        data=[
            go.Bar(
                x=odd_count_dist.index,
                y=odd_count_dist.values,
                marker=dict(
                    color=["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5f27cd", "#00d2d3", "#c8d6e5"],
                ),
                text=odd_count_dist.values,
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="회차별 홀수 개수 분포",
        xaxis_title="홀수 개수",
        yaxis_title="회차 수",
        template="plotly_white",
        height=400,
        xaxis=dict(tickmode="linear", tick0=0, dtick=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_trend_chart(df: pd.DataFrame, top_n: int = 10):
    """최근 트렌드 차트

    Args:
        df: 로또 데이터 DataFrame
        top_n: 표시할 번호 개수
    """
    analyzer = StatisticalAnalyzer(df)

    # 최근 20회차 트렌드
    trends = analyzer.get_trending_numbers(lookback=20)

    up_numbers = trends["up"][:top_n]
    down_numbers = trends["down"][:top_n]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("상승 트렌드 Top 10", "하락 트렌드 Top 10"),
    )

    # 상승 트렌드
    freq_recent = analyzer.calculate_frequency(20)
    up_freq = [freq_recent[num] for num in up_numbers]

    fig.add_trace(
        go.Bar(
            x=up_numbers,
            y=up_freq,
            name="상승",
            marker=dict(color="#1dd1a1"),
            text=up_freq,
            textposition="outside",
        ),
        row=1,
        col=1,
    )

    # 하락 트렌드
    down_freq = [freq_recent[num] for num in down_numbers]

    fig.add_trace(
        go.Bar(
            x=down_numbers,
            y=down_freq,
            name="하락",
            marker=dict(color="#ff6b6b"),
            text=down_freq,
            textposition="outside",
        ),
        row=1,
        col=2,
    )

    fig.update_layout(
        title="최근 20회차 트렌드 분석",
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    fig.update_xaxes(title_text="번호", row=1, col=1)
    fig.update_xaxes(title_text="번호", row=1, col=2)
    fig.update_yaxes(title_text="출현 횟수", row=1, col=1)
    fig.update_yaxes(title_text="출현 횟수", row=1, col=2)

    st.plotly_chart(fig, use_container_width=True)


def plot_correlation_heatmap(df: pd.DataFrame, top_n: int = 20):
    """번호 간 상관관계 히트맵

    Args:
        df: 로또 데이터 DataFrame
        top_n: 표시할 번호 개수
    """
    analyzer = StatisticalAnalyzer(df)
    corr_matrix = analyzer.calculate_correlation_matrix()

    # 상위 빈도 번호만 표시
    freq = analyzer.calculate_frequency()
    top_numbers = freq.nlargest(top_n).index.tolist()

    corr_subset = corr_matrix.loc[top_numbers, top_numbers]

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_subset.values,
            x=corr_subset.columns,
            y=corr_subset.index,
            colorscale="RdBu",
            zmid=0,
            text=corr_subset.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 8},
            colorbar=dict(title="상관계수"),
        )
    )

    fig.update_layout(
        title=f"번호 간 상관관계 (상위 {top_n}개 번호)",
        template="plotly_white",
        height=600,
        xaxis=dict(side="bottom"),
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_number_timeline(df: pd.DataFrame, number: int):
    """특정 번호의 시계열 출현 차트

    Args:
        df: 로또 데이터 DataFrame
        number: 번호
    """
    number_cols = ["num1", "num2", "num3", "num4", "num5", "num6"]

    # 해당 번호의 출현 여부
    appeared = []

    for _, row in df.iterrows():
        numbers = [row[col] for col in number_cols]
        appeared.append(1 if number in numbers else 0)

    df_timeline = df[["round", "draw_date"]].copy()
    df_timeline["appeared"] = appeared

    # 누적 출현 횟수
    df_timeline["cumulative"] = df_timeline["appeared"].cumsum()

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=(f"번호 {number} 출현 여부", f"번호 {number} 누적 출현 횟수"),
        vertical_spacing=0.15,
    )

    # 출현 여부
    fig.add_trace(
        go.Scatter(
            x=df_timeline["round"],
            y=df_timeline["appeared"],
            mode="markers",
            marker=dict(size=5, color="#667eea"),
            name="출현",
        ),
        row=1,
        col=1,
    )

    # 누적 출현
    fig.add_trace(
        go.Scatter(
            x=df_timeline["round"],
            y=df_timeline["cumulative"],
            mode="lines",
            line=dict(color="#764ba2", width=2),
            name="누적",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title=f"번호 {number} 시계열 분석",
        template="plotly_white",
        height=600,
        showlegend=False,
    )

    fig.update_xaxes(title_text="회차", row=1, col=1)
    fig.update_xaxes(title_text="회차", row=2, col=1)
    fig.update_yaxes(title_text="출현 (1: 출현, 0: 미출현)", row=1, col=1)
    fig.update_yaxes(title_text="누적 출현 횟수", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)
