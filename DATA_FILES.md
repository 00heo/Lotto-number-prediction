# 📊 데이터 파일 설명

## 개요

이 프로젝트는 다양한 형태의 로또 데이터를 CSV 및 데이터베이스 형식으로 저장합니다.

---

## 🗂 파일 구조

```
data/
├── raw/                        # 원본 데이터
│   ├── lotto_raw_data.csv     # 크롤링한 원본 데이터
│   └── lotto_sample_data.csv  # 샘플 데이터 (100회차)
│
├── processed/                  # 전처리 데이터
│   ├── lotto_processed.csv    # 전처리 + 파생 특징
│   ├── number_frequency.csv   # 번호별 출현 빈도
│   ├── bonus_frequency.csv    # 보너스 번호 빈도
│   ├── co_occurrence_matrix.csv # 번호 간 동반 출현 행렬
│   └── trends.csv             # 최근 트렌드 점수
│
└── lotto.db                    # SQLite 데이터베이스
```

---

## 📄 파일 상세 설명

### 1. `raw/lotto_sample_data.csv` (원본 데이터)

**설명**: 로또 회차별 기본 정보

**컬럼**:
- `round`: 회차 번호 (정수)
- `draw_date`: 추첨일 (YYYY-MM-DD)
- `num1` ~ `num6`: 당첨 번호 6개 (1-45, 오름차순)
- `bonus`: 보너스 번호 (1-45)
- `sales_amount`: 총 판매금액 (원)
- `winner_count_1st`: 1등 당첨자 수
- `prize_1st`: 1등 상금 (원)

**샘플**:
```csv
round,draw_date,num1,num2,num3,num4,num5,num6,bonus,sales_amount,winner_count_1st,prize_1st
1097,2023-01-07,6,10,15,17,23,44,39,107067768764,5,10706776876
1098,2023-01-14,14,19,28,40,41,45,44,115497905071,4,14437238133
```

**크기**: 약 6-7KB (100회차)

---

### 2. `processed/lotto_processed.csv` (전처리 데이터)

**설명**: 원본 데이터 + 파생 특징 (39개 컬럼)

**추가 컬럼**:

#### 기본 정보
- `id`: 레코드 ID
- `numbers`: 당첨 번호 리스트
- `year`, `month`, `day`, `day_of_week`, `quarter`: 날짜 분해

#### 번호 통계
- `sum`: 6개 번호의 합계
- `mean`: 평균
- `std`: 표준편차
- `min`, `max`: 최소/최대값
- `range`: 범위 (최대 - 최소)

#### 패턴 분석
- `odd_count`: 홀수 개수 (0-6)
- `even_count`: 짝수 개수 (0-6)
- `odd_ratio`: 홀수 비율 (0-1)
- `prime_count`: 소수 개수
- `consecutive_count`: 연속 번호 개수

#### 구간별 분포
- `range_1_10`: 1-10 구간 번호 개수
- `range_11_20`: 11-20 구간 번호 개수
- `range_21_30`: 21-30 구간 번호 개수
- `range_31_40`: 31-40 구간 번호 개수
- `range_41_45`: 41-45 구간 번호 개수

#### 고급 특징
- `last_digits`: 끝자리 리스트
- `ac_value`: AC값 (번호 간 차이의 개수)

**크기**: 약 25KB (100회차)

---

### 3. `processed/number_frequency.csv` (번호 빈도)

**설명**: 각 번호(1-45)의 전체 출현 빈도

**컬럼**:
- `number`: 번호 (1-45)
- `frequency`: 출현 횟수
- `ratio`: 출현 비율 (0-1)

**샘플**:
```csv
number,frequency,ratio
1,13,0.0217
2,11,0.0183
3,17,0.0283
...
```

**용도**:
- 고빈도/저빈도 번호 파악
- 핫/콜드 번호 분석
- 기본 통계 분석

**크기**: 약 1KB (45개 번호)

---

### 4. `processed/bonus_frequency.csv` (보너스 번호 빈도)

**설명**: 보너스 번호(1-45)의 출현 빈도

**컬럼**:
- `number`: 번호 (1-45)
- `frequency`: 보너스로 출현한 횟수
- `ratio`: 출현 비율

**샘플**:
```csv
number,frequency,ratio
1,2,0.02
5,3,0.03
...
```

**크기**: 약 500B (45개 번호)

---

### 5. `processed/co_occurrence_matrix.csv` (동반 출현 행렬)

**설명**: 번호 간 동시 출현 빈도 (45x45 행렬)

**구조**:
- 행: 번호 1-45
- 열: 번호 1-45
- 값: 두 번호가 함께 나온 횟수

**샘플**:
```csv
,1,2,3,4,5,...,45
1,0,2,3,1,2,...,1
2,2,0,1,3,0,...,2
3,3,1,0,2,1,...,0
...
```

**용도**:
- 번호 간 상관관계 분석
- 동반 출현 패턴 파악
- 조합 추천 시 활용

**크기**: 약 4-5KB (45x45 행렬)

---

### 6. `processed/trends.csv` (트렌드)

**설명**: 최근 20회차 기준 번호별 트렌드 점수

**컬럼**:
- `number`: 번호 (1-45)
- `trend_score`: 트렌드 점수 (높을수록 최근 자주 출현)

**계산 방식**:
```python
# 최근 회차일수록 높은 가중치 부여
trend_score = Σ (출현 여부 × 회차 가중치)
회차 가중치 = (회차 인덱스 + 1) / 총 회차 수
```

**샘플**:
```csv
number,trend_score
20,5.40
15,2.75
14,2.70
12,2.40
...
```

**용도**:
- 상승/하락 트렌드 파악
- 최근 핫한 번호 식별
- 예측 모델 특징으로 활용

**크기**: 약 500B (45개 번호)

---

## 💾 데이터베이스 (lotto.db)

**형식**: SQLite 3

**테이블**: `lotto_results`

**스키마**:
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**인덱스**:
- `idx_round`: round 컬럼 인덱스
- `idx_date`: draw_date 컬럼 인덱스

**크기**: 약 20-30KB (100회차)

---

## 📊 데이터 통계 (샘플 데이터 기준)

- **총 회차**: 100개 (1097~1196회)
- **날짜 범위**: 2023-01-07 ~ 2024-11-30
- **평균 번호 합계**: 136.5
- **평균 홀수 개수**: 2.92개
- **평균 연속 번호**: 0.72개
- **평균 소수 개수**: 1.95개

---

## 🔄 데이터 업데이트

### 자동 업데이트 (크롤링)
```bash
# 최신 데이터 수집
python -m src.data.collector --update

# 전체 데이터 재수집
python -m src.data.collector
```

### 수동 생성 (샘플 데이터)
```bash
# 100회차 샘플 데이터 생성
python scripts/generate_sample_data.py
```

### CSV 내보내기
```python
from src.data.storage import StorageManager

storage = StorageManager()
storage.export_to_csv('data/raw/lotto_data.csv')
```

---

## 📖 사용 예제

### Python으로 CSV 읽기

```python
import pandas as pd

# 원본 데이터
df = pd.read_csv('data/raw/lotto_sample_data.csv')
print(df.head())

# 전처리 데이터
df_processed = pd.read_csv('data/processed/lotto_processed.csv')

# 번호 빈도
freq = pd.read_csv('data/processed/number_frequency.csv')
top_10 = freq.nlargest(10, 'frequency')
print("상위 10개 번호:")
print(top_10)

# 동반 출현 행렬
co_matrix = pd.read_csv('data/processed/co_occurrence_matrix.csv', index_col=0)
print(f"번호 1과 2의 동반 출현: {co_matrix.loc[1, 2]}회")

# 트렌드
trends = pd.read_csv('data/processed/trends.csv')
hot_numbers = trends.head(10)
print("핫 번호 Top 10:")
print(hot_numbers)
```

### 데이터베이스 쿼리

```python
from src.data.storage import StorageManager

storage = StorageManager()

# 특정 회차 조회
result = storage.get_result_by_round(1150)
print(result)

# 전체 데이터
df = storage.get_all_results()

# 범위 조회
df_range = storage.get_results_range(1100, 1150)

# 통계
stats = storage.get_statistics()
print(f"총 회차: {stats['total_rounds']}")
```

---

## ⚠️ 주의사항

1. **샘플 데이터**: 현재 데이터는 랜덤 생성된 샘플입니다.
2. **실제 데이터**: 웹사이트 접근 제한으로 실제 크롤링이 제한될 수 있습니다.
3. **데이터 크기**: 전체 1,200회차 수집 시 약 150-200KB 예상
4. **업데이트**: 매주 토요일 추첨 후 수동/자동 업데이트 권장

---

## 📚 관련 문서

- **README.md**: 프로젝트 전체 개요
- **QUICKSTART.md**: 빠른 시작 가이드
- **ARCHITECTURE.md**: 시스템 아키텍처
- **ANALYSIS.md**: 모델 분석

---

**최종 업데이트**: 2025-11-07
**데이터 버전**: 1.0.0 (샘플)
