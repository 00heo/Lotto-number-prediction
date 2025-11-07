# 🚀 빠른 시작 가이드

## 1. 환경 설정

### 필수 요구사항
- Python 3.10 이상
- pip (패키지 관리자)
- 최소 2GB RAM
- 인터넷 연결 (데이터 수집용)

### 가상환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 패키지 설치

```bash
pip install -r requirements.txt
```

---

## 2. 데이터 수집

### 전체 데이터 수집 (최초 1회)

```bash
python -m src.data.collector
```

예상 소요 시간: 5-10분
결과: `data/lotto.db` 파일 생성 (1,196회차 데이터)

### 최신 데이터 업데이트

```bash
python -m src.data.collector --update
```

---

## 3. 데이터 전처리

```bash
python -m src.data.preprocessor
```

결과:
- `data/processed/lotto_processed.csv`
- `data/processed/number_frequency.csv`

---

## 4. 대시보드 실행

### Streamlit 대시보드 시작

```bash
streamlit run dashboard/app.py
```

브라우저에서 자동으로 열림 (http://localhost:8501)

### 대시보드 사용 방법

1. **데이터 로드**
   - 좌측 사이드바 → "📥 데이터 로드" 클릭

2. **모델 학습** (5-10분 소요)
   - 사이드바 → "🎓 모델 학습" 클릭
   - 진행 상황 확인

3. **번호 예측**
   - 사이드바 → "🎯 번호 예측" 클릭

4. **조합 생성**
   - "🎯 예측 결과" 탭 이동
   - 조합 방법 선택 (확률/균형/다양)
   - "🔄 조합 생성" 클릭

5. **결과 확인**
   - Top 5 추천 조합 확인
   - 각 조합의 예측 근거 확인
   - 통계 분석 및 시각화 탐색

---

## 5. CLI 사용법

### 특정 회차 데이터 수집

```bash
python -m src.data.collector --round 1150
```

### 특정 페이지 수집

```bash
python -m src.data.collector --pages 5
```

### 데이터베이스 통계 확인

```python
from src.data.storage import StorageManager

storage = StorageManager()
stats = storage.get_statistics()

print(f"총 회차: {stats['total_rounds']}")
print(f"범위: {stats['min_round']} ~ {stats['max_round']}")
```

---

## 6. 예측 코드 예제

### Python 스크립트로 예측 실행

```python
from src.prediction.predictor import LottoPredictor
from src.prediction.recommender import LottoRecommender

# 1. 예측기 초기화
predictor = LottoPredictor()

# 2. 데이터 로드
predictor.load_data()

# 3. 모델 학습
predictor.train_model()

# 4. 다음 회차 예측
prediction = predictor.predict_next_draw()

print(f"다음 회차: {prediction['next_round']}")
print(f"상위 10개 번호: {prediction['top_numbers']}")

# 5. 추천 조합 생성
recommender = LottoRecommender(predictor)
combinations = recommender.generate_combinations(n_combinations=5)

# 6. 결과 출력
for combo in combinations:
    print(f"\n[{combo['rank']}위] 확률: {combo['probability']:.4f}")
    print(f"번호: {combo['numbers']}")
    print(f"보너스: {combo['bonus']}")
```

---

## 7. 문제 해결

### 데이터 수집 실패

**증상**: "데이터 수집 실패" 오류

**해결방법**:
1. 인터넷 연결 확인
2. URL 접근 가능 여부 확인
3. 재시도 (일시적 네트워크 오류 가능)

```bash
# 재시도
python -m src.data.collector --update
```

### 모델 학습 오류

**증상**: "메모리 부족" 또는 "학습 실패"

**해결방법**:
1. 데이터가 로드되었는지 확인
2. 메모리 확인 (최소 2GB)
3. 다른 프로그램 종료

### 패키지 설치 오류

**증상**: 특정 패키지 설치 실패

**해결방법**:
```bash
# pip 업그레이드
pip install --upgrade pip

# 개별 패키지 설치
pip install pandas numpy scikit-learn xgboost streamlit plotly

# 캐시 클리어 후 재설치
pip cache purge
pip install -r requirements.txt
```

### 대시보드 실행 오류

**증상**: "ModuleNotFoundError" 또는 "Import Error"

**해결방법**:
```bash
# 프로젝트 루트에서 실행
cd /path/to/Lotto-number-prediction

# PYTHONPATH 설정 (Linux/Mac)
export PYTHONPATH=$PYTHONPATH:$(pwd)

# PYTHONPATH 설정 (Windows)
set PYTHONPATH=%PYTHONPATH%;%CD%

# 다시 실행
streamlit run dashboard/app.py
```

---

## 8. 성능 최적화

### 빠른 실행을 위한 팁

1. **데이터 캐싱**
   - 전처리된 데이터 저장
   - 모델 학습 결과 저장

2. **모델 저장/로드**
```python
# 모델 저장
predictor.model.save("models/trained/ensemble_model.pkl")

# 모델 로드
predictor.model.load("models/trained/ensemble_model.pkl")
```

3. **샘플 데이터로 테스트**
```python
# 최근 100회차만 사용
df_sample = df.tail(100)
predictor.df = df_sample
predictor.train_model()
```

---

## 9. 고급 사용법

### 커스텀 모델 추가

```python
from src.models.base_model import BaseModel

class MyCustomModel(BaseModel):
    def train(self, X, y=None):
        # 커스텀 학습 로직
        pass

    def predict(self, X=None):
        # 커스텀 예측 로직
        pass

# 앙상블에 추가
from src.models.ensemble import EnsembleModel

ensemble = EnsembleModel()
ensemble.add_model(MyCustomModel(), weight=0.2)
```

### 커스텀 특징 추가

```python
from src.analysis.feature_engineering import FeatureEngineer

engineer = FeatureEngineer(df)

# 기존 특징
features = engineer.create_feature_matrix()

# 커스텀 특징 추가
features['my_custom_feature'] = ...  # 커스텀 로직
```

---

## 10. 자주 묻는 질문 (FAQ)

**Q: 예측이 정확한가요?**
A: 아니요. 로또는 완전한 무작위 추첨이므로 예측할 수 없습니다. 본 시스템은 교육 및 재미 목적입니다.

**Q: 데이터는 어디서 가져오나요?**
A: 공개된 로또 당첨 정보 사이트에서 크롤링합니다.

**Q: 모델 학습에 시간이 얼마나 걸리나요?**
A: 약 5-10분 정도 소요됩니다 (컴퓨터 사양에 따라 다름).

**Q: 상용으로 사용할 수 있나요?**
A: MIT 라이선스이므로 자유롭게 사용 가능하지만, 당첨을 보장하지 않습니다.

**Q: 모바일에서 사용할 수 있나요?**
A: Streamlit 대시보드는 반응형이므로 모바일 브라우저에서도 사용 가능합니다.

---

## 11. 추가 리소스

- **README.md**: 프로젝트 전체 개요
- **ARCHITECTURE.md**: 시스템 아키텍처 상세 설명
- **ANALYSIS.md**: 모델 분석 및 개선 방안
- **config.yaml**: 설정 파일

---

## 12. 문의 및 기여

- 이슈: GitHub Issues
- 기여: Pull Request 환영
- 라이선스: MIT License

---

**Happy Coding! 🎲📊🚀**
