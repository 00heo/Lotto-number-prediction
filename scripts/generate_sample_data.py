"""샘플 로또 데이터 생성"""

import pandas as pd
import random
from datetime import datetime, timedelta

# 최근 100회차 샘플 데이터 생성
data = []

start_round = 1097
start_date = datetime(2023, 1, 7)  # 샘플 시작 날짜

for i in range(100):
    round_num = start_round + i
    draw_date = start_date + timedelta(weeks=i)

    # 1-45 중 6개 랜덤 선택 (중복 없이)
    numbers = sorted(random.sample(range(1, 46), 6))

    # 보너스 번호 (당첨 번호 제외)
    remaining = [n for n in range(1, 46) if n not in numbers]
    bonus = random.choice(remaining)

    # 추가 정보 (샘플)
    sales_amount = random.randint(80000000000, 120000000000)  # 800억 ~ 1200억
    winner_count_1st = random.randint(0, 15)
    prize_1st = sales_amount // 2 // max(winner_count_1st, 1)  # 1등 상금

    data.append({
        'round': round_num,
        'draw_date': draw_date.strftime('%Y-%m-%d'),
        'num1': numbers[0],
        'num2': numbers[1],
        'num3': numbers[2],
        'num4': numbers[3],
        'num5': numbers[4],
        'num6': numbers[5],
        'bonus': bonus,
        'sales_amount': sales_amount,
        'winner_count_1st': winner_count_1st,
        'prize_1st': prize_1st,
    })

# DataFrame 생성
df = pd.DataFrame(data)

# CSV 저장
df.to_csv('data/raw/lotto_sample_data.csv', index=False, encoding='utf-8-sig')
print(f'✅ 샘플 데이터 생성 완료: {len(df)}개 회차')
print(f'✅ CSV 저장: data/raw/lotto_sample_data.csv')

# 미리보기
print('\n📊 데이터 미리보기 (최근 5회차):')
print(df.tail(5).to_string(index=False))

print(f'\n📈 통계:')
print(f'  회차 범위: {df["round"].min()} ~ {df["round"].max()}')
print(f'  날짜 범위: {df["draw_date"].min()} ~ {df["draw_date"].max()}')
print(f'  평균 판매금액: {df["sales_amount"].mean():,.0f}원')
print(f'  평균 1등 당첨자: {df["winner_count_1st"].mean():.1f}명')
