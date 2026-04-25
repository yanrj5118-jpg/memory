import os
import pandas as pd
import concurrent.futures
from korea_finance import KoreaFinance
from advanced_ichimoku_logic import analyze_ichimoku
import streamlit as st

def get_filtered_stocks(status=None, min_price=0, max_price=1000000, filter_modes=['bullish'], turnover_mode=False, net_purchase_data=None):
    """1. 시장 스냅샷을 활용한 선제적 필터링 (Fast Filter)"""
    api = KoreaFinance()
    if status: status.info("1단계: 시장 전체 시세 데이터 분석 및 고속 필터링 중...")
    
    # 시장 전체 시세 스냅샷 가져오기
    df = api.get_all_target_stocks_with_snapshot()
    if df.empty:
        if status: status.error("🚨 데이터를 가져오지 못했습니다.")
        return []
        
    original_count = len(df)
    
    # 1. 시가총액/가격 필터 (기본)
    df['시가총액_억'] = df['시가총액'] / 100000000
    df['종가'] = pd.to_numeric(df['종가'], errors='coerce')
    df = df[(df['종가'] >= min_price) & (df['종가'] <= max_price)]
    df = df[(df['시가총액_억'] >= 500) & (df['시가총액_억'] <= 50000)]
    
    # 2. 필터 모드별 사전 선별 (Fast Track)
    if 'major_money' in filter_modes or 'super_pick' in filter_modes:
        df['거래대금_억'] = df['거래대금'] / 100000000
        df = df[df['거래대금_억'] >= 100]
        if net_purchase_data:
            df = df[df['Code'].isin(net_purchase_data.keys())]
            df = df[df['Code'].apply(lambda x: net_purchase_data[x].get('쌍끌이', False))]
            
    if turnover_mode:
        df['turnover'] = (df['거래량'] / df['상장주식수']) * 100
        df = df[(df['turnover'] >= 5.0) & (df['turnover'] <= 10.0)]
        
    filtered_count = len(df)
    if status: status.info(f"선제 필터링 완료: {original_count}개 → {filtered_count}개 후보 선정 (분석 시작)")
    
    if filtered_count > 300:
        df = df.sort_values(by='시가총액', ascending=False).head(300)
        if status: status.warning(f"후보가 너무 많아 시총 상위 300개로 정밀 분석을 제한합니다.")
    
    return df.to_dict('records')

def process_single_stock(stock_info, period, api, filter_modes=['bullish'], pattern_params=None, turnover_mode=False, net_purchase_data=None):
    """2. 단일 종목 분석 및 시그널 감지 (당일 돌파 원칙 고수)"""
    sym = stock_info['Code']
    name = stock_info['Name']
    stocks_count = stock_info.get('상장주식수', 1)
    
    try:
        df = api.get_kline_df(sym, period=period)
        if df is None or len(df) < 120:
            return None
            
        # 지표 계산
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        df['VMA120'] = df['Volume'].rolling(window=120).mean()
        
        # MACD (10, 20, 7)
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA20_M'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['MACD'] = df['EMA10'] - df['EMA20_M']
        df['Signal'] = df['MACD'].ewm(span=7, adjust=False).mean()
        
        # 일목균형표 분석
        df = analyze_ichimoku(df, pattern_params=pattern_params)
        
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        
        # 기본 정보 추출
        trade_amount = last['Volume'] * last['Close'] / 100000000
        is_major_buy = net_purchase_data[sym]['쌍끌이'] if net_purchase_data and sym in net_purchase_data else False
        turnover_rate = (last['Volume'] / stocks_count) * 100
        is_vol_120_over = last['Volume'] > last['VMA120']
        is_bullish_aligned = (last['MA5'] > last['MA20']) and (last['MA20'] > last['MA60'])
        
        match_results = []
        pattern_descs = []
        
        for mode in filter_modes:
            m, d = False, ""
            if mode == 'bullish':
                m, d = is_bullish_aligned, "🔥정배열"
            elif mode == 'major_money':
                m, d = (is_major_buy and trade_amount >= 100), "🏢쌍끌이"
            elif mode == 'ma_cross':
                m = (last['MA5'] > last['MA10']) and (prev['MA5'] <= prev['MA10']) and is_vol_120_over
                d = "🚀5/10신규"
            elif mode == 'macd_cross':
                m = (last['MACD'] > last['Signal']) and (prev['MACD'] <= prev['Signal']) and (last['MACD'] > 0)
                d = "📊MACD신규"
            elif mode == 'super_pick':
                is_ma_c = (last['MA5'] > last['MA10']) and (prev['MA5'] <= prev['MA10'])
                is_macd_c = (last['MACD'] > last['Signal']) and (prev['MACD'] <= prev['Signal'])
                is_abc = last['Close'] > last['cloud_top']
                m = is_bullish_aligned and (is_ma_c or is_macd_c) and is_abc
                d = "🏆슈퍼픽"
            elif mode == 'cloud_break':
                m = (last['Close'] > last['cloud_top']) and (prev['Close'] <= prev['cloud_top'])
                d = "☁️구름신규"
            elif mode == 'box_squeeze':
                df_200 = df.tail(200)
                range_pct = (df_200['High'].max() - df_200['Low'].min()) / df_200['Low'].min()
                m, d = (range_pct <= 0.30), "📦박스권"
            elif mode == 'box_breakout':
                # 1. 박스권 매집 확인 (어제까지의 200일)
                df_prev_200 = df.iloc[-201:-1]
                if len(df_prev_200) >= 199:
                    max_prev = df_prev_200['High'].max()
                    min_prev = df_prev_200['Low'].min()
                    range_pct = (max_prev - min_prev) / min_prev
                    # 2. 박스권(30%이내) + 오늘 종가가 전고점 돌파
                    m = (range_pct <= 0.30) and (last['Close'] > max_prev)
                    d = "🚀박스돌파"
                else:
                    m, d = False, ""
            
            match_results.append(m)
            if m: pattern_descs.append(d)
            
        if all(match_results) if match_results else True:
            major_emoji = "🏢" if is_major_buy else ""
            pattern_desc = " + ".join(pattern_descs) if pattern_descs else "기본조건"
            return {
                "코드": sym, "종목명": name, "현재가": f"{int(last['Close']):,}",
                "거래대금": f"{int(trade_amount)}억", "수급": f"{major_emoji}{'쌍끌이' if is_major_buy else '일반'}",
                "회전율": f"{turnover_rate:.2f}%", "패턴": pattern_desc, "점수": int(last.get('sentiment_score', 0))
            }
        return None
    except Exception:
        return None

def run_market_screener(period='daily', filter_modes=['bullish'], progress_bar=None, status_text=None, pattern_params=None, min_price=0, max_price=1000000, turnover_mode=False):
    """3. 병렬 스캐너 실행 (최적화 버전)"""
    api = KoreaFinance()
    
    if status_text: status_text.info("준비 단계: 기관 및 외국인 수급 데이터 분석 중...")
    net_purchase_data = api.fetch_net_purchase_data()
    
    target_stocks = get_filtered_stocks(
        status=status_text, 
        min_price=min_price, 
        max_price=max_price, 
        filter_modes=filter_modes, 
        turnover_mode=turnover_mode,
        net_purchase_data=net_purchase_data
    )
    
    if not target_stocks:
        return pd.DataFrame()
        
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(process_single_stock, st_info, period, api, filter_modes, pattern_params, turnover_mode, net_purchase_data): st_info for st_info in target_stocks}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res = future.result()
            if res:
                results.append(res)
            
            if progress_bar:
                progress_bar.progress((i + 1) / len(target_stocks))
                status_text.text(f"차트 심층 분석 중... [{i + 1}/{len(target_stocks)}] ({len(results)}개 종목 포착)")

    if results:
        df_res = pd.DataFrame(results)
        df_res = df_res.sort_values(by="점수", ascending=False).reset_index(drop=True)
        return df_res
    return pd.DataFrame()
