import pandas as pd
import numpy as np

def calculate_advanced_ichimoku(df):
    """
    OHLCV 데이터프레임을 받아 '최적화 일목균형표' 지표 및 시그널을 계산하는 함수입니다.
    필수 칼럼: 'High', 'Low', 'Close'
    """
    # 1. 일목균형표 기본 지표 계산
    # 전환선 (Conversion Line): 최근 9일간의 최고가와 최저가의 중간값
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2
    
    # 기준선 (Base Line): 최근 26일간의 최고가와 최저가의 중간값
    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (high_26 + low_26) / 2
    
    # 선행스팬 A & B (구름대 구성 요소)
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    
    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['senkou_span_b'] = ((high_52 + low_52) / 2).shift(26)
    
    # 구름대 상단과 하단
    df['cloud_top'] = df[['senkou_span_a', 'senkou_span_b']].max(axis=1)
    df['cloud_bottom'] = df[['senkou_span_a', 'senkou_span_b']].min(axis=1)
    
    # 2. 최적화 지표 계산 (오실레이터용)
    # 중심선 (Center Line): 가격이 구름대보다 위에 있으면 +, 아래에 있으면 - 표출
    def calc_center_line(row):
        if pd.isna(row['cloud_top']) or pd.isna(row['cloud_bottom']):
            return np.nan
        if row['Close'] > row['cloud_top']:
            return row['Close'] - row['cloud_top']
        elif row['Close'] < row['cloud_bottom']:
            return row['Close'] - row['cloud_bottom']
        else:
            return 0 # 구름대 내부에 있을 경우 0으로 처리

    df['center_line'] = df.apply(calc_center_line, axis=1)
    
    # 중심선 색상: 기준선이 전환선 위에 있으면 'green', 아래에 있으면 'red'
    df['center_color'] = np.where(df['kijun_sen'] >= df['tenkan_sen'], 'green', 'red')
    
    # 회색선 (Gray Line): 후행스팬(현재 종가)과 26일 주기 전 과거 가격 간의 차이 (모멘텀)
    df['gray_line'] = df['Close'] - df['Close'].shift(26)
    
    # 3. 매수/매도 시그널 및 청산(익절) 판단
    df['long_signal'] = False
    df['short_signal'] = False
    df['tp_signal'] = False # 익절 시그널 (TP)
    
    # 시그널 계산을 위한 이전 값들
    df['prev_center_line'] = df['center_line'].shift(1)
    df['prev_gray_line'] = df['gray_line'].shift(1)
    
    # Long (매수) 조건
    # 1: 중심선이 0선 위로 돌파, 2: 색상이 'green', 3: 회색선이 0선 위
    long_cond1 = (df['prev_center_line'] <= 0) & (df['center_line'] > 0)
    long_cond2 = (df['center_color'] == 'green')
    long_cond3 = (df['gray_line'] > 0)
    df.loc[long_cond1 & long_cond2 & long_cond3, 'long_signal'] = True
    
    # Short (매도) 조건
    # 1: 중심선이 0선 아래로 돌파, 2: 색상이 'red', 3: 회색선이 0선 아래
    short_cond1 = (df['prev_center_line'] >= 0) & (df['center_line'] < 0)
    short_cond2 = (df['center_color'] == 'red')
    short_cond3 = (df['gray_line'] < 0)
    df.loc[short_cond1 & short_cond2 & short_cond3, 'short_signal'] = True
    
    # 청산(TP) 시그널: 회색선이 0선을 터치(교차)
    df.loc[(df['prev_gray_line'] > 0) & (df['gray_line'] <= 0), 'tp_signal'] = True
    df.loc[(df['prev_gray_line'] < 0) & (df['gray_line'] >= 0), 'tp_signal'] = True
    
    return df

def detect_divergence(df, window=14):
    """
    단순화된 다이버전스(Divergence) 탐지 함수.
    주가의 흐름과 중심선(Center Line)의 흐름이 반대인 구간을 찾습니다.
    """
    df['bullish_divergence'] = False # 상승 다이버전스
    df['bearish_divergence'] = False # 하락 다이버전스
    
    # 성능을 위해 최신 데이터 위주로 계산하거나 벡터화할 수 있지만, 여기서는 루프를 사용합니다.
    for i in range(window, len(df)):
        if pd.isna(df['center_line'].iloc[i]): continue
            
        current_close = df['Close'].iloc[i]
        current_center = df['center_line'].iloc[i]
        
        # 이전 기간의 최저점/최고점 확인
        past_closes = df['Close'].iloc[i-window:i]
        past_centers = df['center_line'].iloc[i-window:i]
        
        # 최저점 기준 상승 다이버전스 판별
        min_past_close = past_closes.min()
        min_past_center = past_centers.min()
        
        if current_close < min_past_close and current_center > min_past_center:
            df.iloc[i, df.columns.get_loc('bullish_divergence')] = True
            
        # 최고점 기준 하락 다이버전스 판별
        max_past_close = past_closes.max()
        max_past_center = past_centers.max()
        
        if current_close > max_past_close and current_center < max_past_center:
            df.iloc[i, df.columns.get_loc('bearish_divergence')] = True

    return df

def calculate_sentiment_score(df):
    """
    일목균형표 지표들을 기반으로 시장의 강세/약세 점수(0~100)를 계산합니다.
    """
    if df.empty or 'tenkan_sen' not in df.columns:
        return df

    # 마지막 행 기준으로 점수 산출
    last = df.iloc[-1]
    score = 0
    
    # 1. 가격 vs 구름대 (25점)
    if last['Close'] > last['cloud_top']: score += 25
    elif last['Close'] >= last['cloud_bottom']: score += 10
    
    # 2. 전환선 vs 기준선 (20점)
    if last['tenkan_sen'] > last['kijun_sen']: score += 20
    
    # 3. 중심선 (20점)
    if last['center_line'] > 0: score += 20
    
    # 4. 회색선 (15점)
    if last['gray_line'] > 0: score += 15
    
    # 5. 구름대 색상 (10점)
    if last['senkou_span_a'] > last['senkou_span_b']: score += 10
    
    # 6. 후행스팬 (10점) - 현재 종가 vs 26일 전 종가
    if len(df) > 26:
        past_close = df['Close'].iloc[-26]
        if last['Close'] > past_close: score += 10
        
    df['sentiment_score'] = score
    return df

def detect_patterns(df, dfp_params=None, ygy_params=None, ql_params=None):
    """
    중국 시장 특화 3대 패턴 감지 (다방포, 양개음, 기린) - 가변 파라미터 적용
    """
    if len(df) < 5:
        return df
        
    # 기본값 설정
    ql_short = ql_params.get('short', 5) if ql_params else 5
    ql_mid = ql_params.get('mid', 10) if ql_params else 10
    ql_long = ql_params.get('long', 20) if ql_params else 20
    
    df['pattern_dfp'] = False # 다방포 (多方炮)
    df['pattern_ygy'] = False # 양개음 (阳盖阴)
    df['pattern_ql'] = False  # 기린 (麒麟)
    
    # 1. 다방포 (양-음-양)
    # T-2: 양봉, T-1: 음봉, T: 양봉 & T종가 > T-2종가
    for i in range(2, len(df)):
        c0, o0 = df['Close'].iloc[i], df['Open'].iloc[i]
        c1, o1 = df['Close'].iloc[i-1], df['Open'].iloc[i-1]
        c2, o2 = df['Close'].iloc[i-2], df['Open'].iloc[i-2]
        
        if (c2 > o2) and (c1 < o1) and (c0 > o0) and (c0 > c2):
            df.iloc[i, df.columns.get_loc('pattern_dfp')] = True
            
    # 2. 양개음 (상승장악형)
    # T-1: 음봉, T: 양봉 & T몸통이 T-1몸통을 완전히 덮음
    for i in range(1, len(df)):
        c0, o0 = df['Close'].iloc[i], df['Open'].iloc[i]
        c1, o1 = df['Close'].iloc[i-1], df['Open'].iloc[i-1]
        
        if (c1 < o1) and (c0 > o0) and (c0 >= o1) and (o0 <= c1):
            df.iloc[i, df.columns.get_loc('pattern_ygy')] = True
            
    # 3. 기린 (麒麟 - 이동평균선 정배열 추세) - 동적 이평선 적용
    ma_s = df['Close'].rolling(window=ql_short).mean()
    ma_m = df['Close'].rolling(window=ql_mid).mean()
    ma_l = df['Close'].rolling(window=ql_long).mean()
    
    df['pattern_ql'] = (ma_s > ma_m) & (ma_m > ma_l) & (df['Close'] > ma_s)
    
    return df

def analyze_ichimoku(df, pattern_params=None):
    """
    전체 프로세스(지표 계산 -> 다이버전스 탐지 -> 패턴 감지 -> 에너지 점수 산출)를 실행하는 통합 함수
    """
    if df.empty:
        return df
    
    # 파이프라인 실행
    df = calculate_advanced_ichimoku(df)
    df = detect_divergence(df)
    
    # 패턴 파라미터 분해 및 적용
    dfp_p = pattern_params.get('dfp') if pattern_params else None
    ygy_p = pattern_params.get('ygy') if pattern_params else None
    ql_p = pattern_params.get('ql') if pattern_params else None
    
    df = detect_patterns(df, dfp_params=dfp_p, ygy_params=ygy_p, ql_params=ql_p)
    df = calculate_sentiment_score(df)
    return df

if __name__ == "__main__":
    print("일목균형표 분석 모듈이 로드되었습니다.")
