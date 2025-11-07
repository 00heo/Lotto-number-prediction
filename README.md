# 🎰 한국 로또 6/45 번호 예측 시스템

데이터 기반 통계 분석과 머신러닝을 활용한 로또 번호 예측 및 추천 시스템

## 📊 프로젝트 개요

동행복권의 과거 당첨 데이터를 분석하여 다음 회차의 번호를 예측하고, 상위 5개의 유력 조합을 확률순으로 추천하는 시스템입니다.

## 🏗 시스템 아키텍처

```
├── src/
│   ├── data/
│   │   ├── collector.py          # 데이터 수집 (웹 크롤링)
│   │   ├── preprocessor.py       # 데이터 전처리
│   │   └── storage.py            # 데이터 저장 관리
│   │
│   ├── analysis/
│   │   ├── statistics.py         # 통계 분석
│   │   ├── feature_engineering.py # 특징 추출
│   │   └── patterns.py           # 패턴 분석
│   │
│   ├── models/
│   │   ├── base_model.py         # 기본 모델 클래스
│   │   ├── statistical_model.py  # 통계 기반 모델
│   │   ├── ml_model.py           # 머신러닝 모델
│   │   └── ensemble.py           # 앙상블 예측
│   │
│   ├── prediction/
│   │   ├── predictor.py          # 예측 엔진
│   │   ├── probability.py        # 확률 계산
│   │   └── recommender.py        # 추천 시스템
│   │
│   └── utils/
│       ├── config.py             # 설정
│       ├── logger.py             # 로깅
│       └── validators.py         # 데이터 검증
│
├── dashboard/
│   ├── app.py                    # Streamlit 메인 앱
│   ├── components/
│   │   ├── visualizations.py    # 시각화 컴포넌트
│   │   ├── predictions.py       # 예측 결과 표시
│   │   └── statistics.py        # 통계 대시보드
│   └── styles/
│       └── custom.css            # 커스텀 스타일
│
├── data/
│   ├── raw/                      # 원본 데이터
│   ├── processed/                # 전처리 데이터
│   └── lotto.db                  # SQLite 데이터베이스
│
├── models/
│   └── trained/                  # 학습된 모델 저장
│
├── tests/
│   ├── test_collector.py
│   ├── test_models.py
│   └── test_predictor.py
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_statistical_analysis.ipynb
│   └── 03_model_development.ipynb
│
├── requirements.txt
├── setup.py
└── config.yaml
```

## 🔧 기술 스택

### Core
- **Python 3.10+**: 메인 프로그래밍 언어
- **Streamlit**: 대시보드 UI 프레임워크
- **SQLite**: 로컬 데이터베이스

### 데이터 수집 & 처리
- **requests**: HTTP 요청
- **BeautifulSoup4**: HTML 파싱
- **pandas**: 데이터 처리 및 분석
- **numpy**: 수치 연산

### 머신러닝 & 분석
- **scikit-learn**: 기본 ML 알고리즘
- **XGBoost**: 그래디언트 부스팅
- **scipy**: 통계 분석
- **statsmodels**: 고급 통계 모델

### 시각화
- **plotly**: 인터랙티브 차트
- **matplotlib**: 기본 시각화
- **seaborn**: 통계 시각화

### 유틸리티
- **APScheduler**: 자동 스케줄링
- **python-dotenv**: 환경 변수 관리
- **loguru**: 로깅

## 📈 주요 기능

### 1. 데이터 수집
- 동행복권 공식 사이트 크롤링 (1~최신 회차)
- 회차별 정보: 날짜, 당첨번호(6개), 보너스 번호, 판매금액, 당첨 정보
- 자동 업데이트 스케줄링

### 2. 통계 분석
- 번호별 출현 빈도 분석
- 연속 번호 패턴 분석
- 홀/짝 비율 분석
- 구간별(1-10, 11-20...) 분포 분석
- 번호 간 상관관계 분석
- 최근 트렌드 분석

### 3. 머신러닝 모델
- **Random Forest**: 패턴 학습 및 특징 중요도 분석
- **XGBoost**: 고급 그래디언트 부스팅
- **Neural Network**: 비선형 패턴 학습
- **앙상블 모델**: 여러 모델의 예측 결합

### 4. 예측 시스템
- 다음 회차 번호 예측
- 상위 5개 조합 추천 (확률순)
- 각 조합의 예측 근거 제공
- 신뢰도 점수 계산

### 5. 대시보드
- 최신 당첨 결과 표시
- 번호별 출현 빈도 차트
- 패턴 분석 시각화
- 예측 결과 및 추천 조합
- 모델 성능 지표
- "예상번호 새로고침" 인터랙션

## 🚀 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터 수집
```bash
# 전체 데이터 수집
python -m src.data.collector

# 최신 데이터만 업데이트
python -m src.data.collector --update
```

### 3. 모델 학습
```bash
# 모델 학습
python -m src.models.train

# 특정 모델만 학습
python -m src.models.train --model xgboost
```

### 4. 대시보드 실행
```bash
streamlit run dashboard/app.py
```

## 📊 모델 설명

### 통계 기반 접근
1. **빈도 분석**: 과거 출현 빈도 기반 가중치
2. **패턴 인식**: 연속 번호, 홀짝 패턴 등
3. **시계열 분석**: 최근 트렌드 반영

### 머신러닝 접근
1. **특징 추출**:
   - 각 번호의 최근 N회차 출현 여부
   - 번호 간 동반 출현 빈도
   - 구간별 분포
   - 홀짝/고저 비율
   - 연속성 지표

2. **모델 앙상블**:
   - 여러 모델의 예측을 가중 평균
   - 각 모델의 성능에 따른 가중치 부여

3. **확률 계산**:
   - 각 번호의 출현 확률 산출
   - 조합의 전체 확률 계산
   - 상위 5개 조합 선정

## ⚠️ 면책 조항

**본 시스템은 교육 및 연구 목적으로 개발되었습니다.**

- 로또는 완전한 무작위 추첨이며, 과거 데이터로 미래를 예측할 수 없습니다.
- 본 시스템의 예측은 통계적 패턴 분석일 뿐, 실제 당첨을 보장하지 않습니다.
- 투자 손실에 대한 책임은 사용자에게 있습니다.
- 로또 구매는 개인의 판단 하에 신중히 결정하시기 바랍니다.

## 📝 모델 한계점

1. **무작위성**: 로또는 완전한 무작위 추첨으로 패턴이 없음
2. **과적합 위험**: 과거 데이터에 과도하게 맞춰질 수 있음
3. **독립 사건**: 각 회차는 독립적이며 이전 결과가 영향을 주지 않음
4. **샘플 크기**: 1,000여 회차는 통계적으로 제한적인 샘플
5. **확률의 함정**: 모든 조합이 동일한 확률 (1/8,145,060)

## 🎯 향후 개선 방향

1. **고급 모델**: Transformer, LSTM 등 시계열 모델 적용
2. **외부 데이터**: 요일, 계절성 등 추가 변수 고려
3. **실시간 업데이트**: 자동 크롤링 및 모델 재학습
4. **성능 평가**: 백테스팅 및 예측 정확도 추적
5. **사용자 기능**: 사용자 번호 분석, 당첨 확률 계산

## 📄 라이선스

MIT License

## 👤 개발자

Korean Lotto Prediction System - Data Science Project

---

**Remember: 로또는 오락입니다. 즐겁게, 그리고 책임감 있게!** 🎲
