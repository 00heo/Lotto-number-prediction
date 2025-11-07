# 🏗 시스템 아키텍처 설계서

## 1. 전체 시스템 구조

### 1.1 레이어드 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│              (Streamlit Dashboard UI)                       │
├─────────────────────────────────────────────────────────────┤
│                    Prediction Layer                         │
│         (Predictor | Probability | Recommender)            │
├─────────────────────────────────────────────────────────────┤
│                     Analysis Layer                          │
│    (Statistics | Feature Engineering | Patterns)           │
├─────────────────────────────────────────────────────────────┤
│                      Model Layer                            │
│  (Statistical | Random Forest | XGBoost | Ensemble)        │
├─────────────────────────────────────────────────────────────┤
│                       Data Layer                            │
│      (Collector | Preprocessor | Storage)                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 데이터 플로우

```
[Web Source]
    ↓ (크롤링)
[Raw Data]
    ↓ (전처리)
[Cleaned Data]
    ↓ (특징 추출)
[Features]
    ↓ (학습)
[Trained Models]
    ↓ (예측)
[Predictions]
    ↓ (시각화)
[Dashboard]
```

## 2. 데이터 계층 (Data Layer)

### 2.1 Data Collector (src/data/collector.py)
**역할**: 웹 크롤링 및 데이터 수집

**기능**:
- 동행복권 페이지 크롤링 (pagination 처리)
- 회차별 데이터 파싱
- 증분 업데이트 (신규 회차만 수집)
- 에러 처리 및 재시도 로직

**데이터 스키마**:
```python
{
    "round": int,           # 회차
    "date": datetime,       # 추첨일
    "numbers": [int, ...],  # 당첨번호 6개
    "bonus": int,           # 보너스 번호
    "sales_amount": int,    # 총 판매금액
    "winner_count_1st": int,# 1등 당첨자 수
    "prize_1st": int        # 1등 상금
}
```

### 2.2 Data Preprocessor (src/data/preprocessor.py)
**역할**: 데이터 정제 및 변환

**기능**:
- 결측값 처리
- 데이터 타입 변환
- 이상치 탐지 및 처리
- 정규화 및 스케일링

### 2.3 Storage Manager (src/data/storage.py)
**역할**: 데이터베이스 관리

**기능**:
- SQLite CRUD 작업
- 데이터 백업 (CSV)
- 버전 관리

**DB 스키마**:
```sql
CREATE TABLE lotto_results (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_round ON lotto_results(round);
CREATE INDEX idx_date ON lotto_results(draw_date);
```

## 3. 분석 계층 (Analysis Layer)

### 3.1 Statistics Module (src/analysis/statistics.py)
**역할**: 기본 통계 분석

**분석 항목**:
1. **출현 빈도 분석**
   - 각 번호(1-45)의 전체 출현 횟수
   - 최근 N회차 출현 빈도
   - 시간대별 트렌드

2. **구간 분석**
   - 1-10, 11-20, 21-30, 31-40, 41-45 구간별 분포
   - 구간별 평균 출현 개수

3. **홀짝 분석**
   - 홀수/짝수 비율
   - 역대 홀짝 패턴 분포

4. **연속성 분석**
   - 연속 번호 출현 빈도
   - 연속 번호 개수 분포

### 3.2 Feature Engineering (src/analysis/feature_engineering.py)
**역할**: ML 모델을 위한 특징 추출

**특징 목록**:

```python
features = {
    # 1. 빈도 기반 특징
    "freq_all": 전체 회차 출현 빈도,
    "freq_recent_5": 최근 5회차 출현 빈도,
    "freq_recent_10": 최근 10회차 출현 빈도,
    "freq_recent_20": 최근 20회차 출현 빈도,
    "freq_recent_50": 최근 50회차 출현 빈도,

    # 2. 시간 기반 특징
    "last_appeared": 마지막 출현 회차,
    "gap_avg": 평균 출현 간격,
    "gap_std": 출현 간격 표준편차,

    # 3. 동반 출현 특징
    "co_occurrence_1": 번호 1과의 동반 출현 빈도,
    # ... (각 번호별)
    "co_occurrence_45": 번호 45와의 동반 출현 빈도,

    # 4. 패턴 특징
    "is_odd": 홀수 여부,
    "is_prime": 소수 여부,
    "range_group": 구간 (0: 1-10, 1: 11-20, ...),
    "consecutive_count": 연속 번호와 함께 나온 횟수,

    # 5. 트렌드 특징
    "trend_score": 최근 상승/하락 트렌드 점수,
    "momentum": 출현 모멘텀 (가속도),
}
```

### 3.3 Pattern Analysis (src/analysis/patterns.py)
**역할**: 패턴 탐지 및 분석

**패턴 유형**:
1. 연속 번호 패턴 (1-2-3, 22-23 등)
2. 등차수열 패턴 (3-6-9, 5-10-15 등)
3. 대칭 패턴
4. 구간별 분포 패턴

## 4. 모델 계층 (Model Layer)

### 4.1 Base Model (src/models/base_model.py)
**역할**: 모든 모델의 기본 클래스

```python
class BaseModel:
    def train(self, X, y):
        pass

    def predict(self, X):
        pass

    def evaluate(self, X, y):
        pass

    def save(self, path):
        pass

    def load(self, path):
        pass
```

### 4.2 Statistical Model (src/models/statistical_model.py)
**접근법**: 순수 통계 기반 예측

**알고리즘**:
1. 가중 빈도 분석
   - 전체 빈도: 30%
   - 최근 50회차 빈도: 40%
   - 최근 20회차 빈도: 30%

2. 베이지안 확률 업데이트

3. 확률 기반 샘플링

### 4.3 ML Models

#### Random Forest (src/models/ml_model.py)
**구조**:
- 입력: 특징 벡터 (각 번호별 특징)
- 출력: 각 번호의 출현 확률

**하이퍼파라미터**:
```yaml
n_estimators: 200
max_depth: 20
min_samples_split: 5
random_state: 42
```

#### XGBoost
**구조**:
- Gradient Boosting 기반
- 불균형 데이터 처리 최적화

**하이퍼파라미터**:
```yaml
n_estimators: 300
max_depth: 10
learning_rate: 0.05
subsample: 0.8
colsample_bytree: 0.8
```

#### Neural Network (Optional)
**구조**:
```
Input (features) → Dense(128) → ReLU → Dropout(0.3)
                → Dense(64) → ReLU → Dropout(0.3)
                → Dense(32) → ReLU
                → Dense(45) → Sigmoid (확률)
```

### 4.4 Ensemble Model (src/models/ensemble.py)
**역할**: 여러 모델의 예측 통합

**앙상블 전략**:
```python
weights = {
    "statistical": 0.30,
    "random_forest": 0.25,
    "xgboost": 0.30,
    "neural_network": 0.15
}

final_probability = sum(
    model.predict(X) * weight
    for model, weight in zip(models, weights)
)
```

## 5. 예측 계층 (Prediction Layer)

### 5.1 Predictor (src/prediction/predictor.py)
**역할**: 실제 번호 예측 수행

**프로세스**:
1. 최신 데이터 로드
2. 특징 추출
3. 모델별 확률 예측
4. 앙상블 통합
5. 상위 N개 조합 생성

### 5.2 Probability Calculator (src/prediction/probability.py)
**역할**: 조합 확률 계산

**계산 방법**:
```python
# 각 번호의 독립 확률
P(num_i) = ensemble_model.predict(num_i)

# 조합 확률 (독립 가정)
P(combination) = ∏ P(num_i) for num_i in combination

# 정규화
P_normalized = P(combination) / sum(all_combinations)
```

### 5.3 Recommender (src/prediction/recommender.py)
**역할**: Top-5 조합 추천

**추천 알고리즘**:
1. 모든 번호의 예측 확률 계산
2. 확률 기반 조합 생성 (최적화)
   - 상위 확률 번호 우선 선택
   - 다양성 보장 (너무 유사한 조합 제외)
3. 각 조합의 전체 확률 계산
4. 상위 5개 선정
5. 예측 근거 생성

**근거 생성**:
```python
reasoning = {
    "high_frequency": [번호 리스트],
    "recent_trend": [번호 리스트],
    "co_occurrence": "num X와 Y가 자주 동반 출현",
    "pattern": "연속 번호 패턴 감지",
    "confidence": 0.75
}
```

## 6. 프레젠테이션 계층 (Presentation Layer)

### 6.1 Streamlit Dashboard (dashboard/app.py)
**구조**:
```python
# 메인 페이지
├── 헤더 & 타이틀
├── 사이드바
│   ├── 설정
│   ├── 필터
│   └── 새로고침 버튼
│
├── 메인 컨텐츠
│   ├── 최신 당첨 결과
│   ├── 예측 조합 (Top 5)
│   ├── 통계 대시보드
│   │   ├── 출현 빈도 차트
│   │   ├── 구간별 분포
│   │   ├── 홀짝 비율
│   │   └── 연속 번호 패턴
│   │
│   └── 고급 분석
│       ├── 히트맵 (번호 간 상관관계)
│       ├── 트렌드 분석
│       └── 모델 성능 지표
│
└── 푸터
    ├── 면책 조항
    └── 정보
```

### 6.2 Components

#### Visualizations (dashboard/components/visualizations.py)
**차트 종류**:
1. 번호별 출현 빈도 - Bar Chart
2. 시계열 트렌드 - Line Chart
3. 구간별 분포 - Pie Chart
4. 상관관계 히트맵 - Heatmap
5. 홀짝 비율 - Donut Chart

#### Predictions Display (dashboard/components/predictions.py)
**UI 요소**:
```
┌─────────────────────────────────────────┐
│  🎯 예측 조합 Top 5                      │
├─────────────────────────────────────────┤
│  1위 (확률 15.2%)                        │
│  ●  3  12  23  28  35  41  [+7]        │
│  근거: 고빈도(3,12), 최근트렌드(23,28)   │
├─────────────────────────────────────────┤
│  2위 (확률 14.8%)                        │
│  ●  5  14  21  29  37  42  [+11]       │
│  근거: 동반출현(5-37), 패턴(연속없음)    │
└─────────────────────────────────────────┘
```

## 7. 유틸리티 (Utils)

### 7.1 Config (src/utils/config.py)
**역할**: 설정 관리
```python
class Config:
    @staticmethod
    def load():
        # YAML 로드
        pass

    @staticmethod
    def get(key):
        pass
```

### 7.2 Logger (src/utils/logger.py)
**역할**: 로깅 시스템
```python
from loguru import logger

logger.add(
    "logs/lotto_{time}.log",
    rotation="1 week",
    retention="1 month"
)
```

### 7.3 Validators (src/utils/validators.py)
**역할**: 데이터 검증
```python
def validate_numbers(numbers):
    # 1-45 범위 확인
    # 중복 확인
    # 개수 확인
    pass
```

## 8. 배포 및 스케줄링

### 8.1 자동 업데이트
```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    collect_latest_data,
    'cron',
    day_of_week='sat',
    hour=22,
    minute=0
)
scheduler.start()
```

### 8.2 배포 옵션
1. **로컬 실행**: `streamlit run dashboard/app.py`
2. **Streamlit Cloud**: GitHub 연동 배포
3. **Docker**: 컨테이너화 배포

## 9. 성능 최적화

### 9.1 캐싱
```python
@st.cache_data(ttl=3600)
def load_data():
    pass

@st.cache_resource
def load_model():
    pass
```

### 9.2 데이터베이스 인덱싱
- round, draw_date 컬럼 인덱스
- 쿼리 최적화

### 9.3 비동기 처리
- 데이터 수집 시 비동기 요청
- 모델 예측 병렬 처리

## 10. 보안 및 에러 처리

### 10.1 에러 처리
```python
try:
    data = collect_data()
except RequestException as e:
    logger.error(f"수집 실패: {e}")
    # 재시도 로직
except Exception as e:
    logger.critical(f"치명적 오류: {e}")
    # 알림
```

### 10.2 데이터 무결성
- 트랜잭션 사용
- 백업 자동화
- 버전 관리

---

## 부록: 기술 스택 선정 이유

| 기술 | 선정 이유 |
|------|----------|
| **Python** | 데이터 분석 생태계, ML 라이브러리 풍부 |
| **Streamlit** | 빠른 대시보드 개발, 파이썬 네이티브 |
| **SQLite** | 경량, 설정 불필요, 충분한 성능 |
| **XGBoost** | 테이블 데이터 최적 성능 |
| **Plotly** | 인터랙티브 차트, 모던 UI |
| **BeautifulSoup4** | HTML 파싱 표준 |
| **APScheduler** | 파이썬 기반 스케줄링 |

---

**작성일**: 2025-11-07
**버전**: 1.0.0
