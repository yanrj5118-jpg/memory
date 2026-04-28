import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from korea_finance import KoreaFinance
from advanced_ichimoku_logic import analyze_ichimoku
from stock_screener_ko import run_market_screener
from datetime import datetime
import re

# 페이지 설정
st.set_page_config(page_title="일목균형표 Pro 터미널", layout="wide", initial_sidebar_state="expanded")

# 프리미엄 라이트 테마 CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }
    
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
    }
    
    /* 사이드바 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #dee2e6;
    }
    
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #495057 !important;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #0056b3 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* 입력창 스타일 */
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #007bff !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 12px !important;
        font-size: 1.5rem !important;
        text-align: center !important;
        font-weight: bold !important;
    }
    
    div[data-testid="stTextInput"] input:focus {
        border-color: #007bff !important;
        box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25) !important;
    }
    
    /* 메트릭 및 시그널 카드 */
    div[data-testid="metric-container"], .signal-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    [data-testid="stMetricValue"] {
        color: #212529 !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] p {
        color: #6c757d !important;
        font-weight: 600 !important;
    }

    .signal-card {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로딩 함수
@st.cache_data(ttl=60)
def load_data(symbol, period):
    api = KoreaFinance()
    df = api.get_kline_df(symbol, period=period)
    
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), "알 수 없음", None
        
    # 실시간 요약 정보
    rt_data = api.fetch([symbol])
    rt = rt_data[0] if rt_data else None
    name = rt['name'] if rt else symbol
    
    # 분석 실행
    df = analyze_ichimoku(df)
    
    # 보조 차트용 일봉
    df_daily = df if period == 'daily' else api.get_kline_df(symbol, period='daily')
    
    return df, df_daily, name, rt

# 메인 헤더
st.markdown("<h1 style='text-align: center; color: #007bff;'>📊 일목균형표 Pro (Ichimoku Professional)</h1>", unsafe_allow_html=True)

# 실전 대비 시장 지수 모니터링 영역
@st.cache_data(ttl=30)
def get_market_indices():
    api = KoreaFinance()
    indices = api.fetch(['KS11', 'KQ11']) # 코스피, 코스닥 심볼
    return indices

indices = get_market_indices()
if indices:
    idx_cols = st.columns(len(indices))
    for i, idx in enumerate(indices):
        color = "#ff5252" if idx['pct'] >= 0 else "#00e676"
        idx_cols[i].markdown(f"""
            <div style='background-color: white; border: 1px solid #dee2e6; padding: 10px; border-radius: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'>
                <span style='color: #6c757d; font-size: 0.8rem;'>{idx['name']}</span><br>
                <span style='color: {color}; font-size: 1.2rem; font-weight: bold;'>{idx['price']:,.2f}</span>
                <span style='color: {color}; font-size: 0.9rem;'> ({idx['pct']:+.2f}%)</span>
            </div>
        """, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 전 종목 리스트 캐싱 (검색용)
@st.cache_data
def get_all_stocks_list():
    api = KoreaFinance()
    stocks = api.get_all_target_stocks()
    df = pd.DataFrame(stocks)
    if df.empty or 'Name' not in df.columns:
        return pd.DataFrame([{'Code': '005930', 'Name': '삼성전자', '시가총액': 0, '종가': 0}])
    return df

df_stocks = get_all_stocks_list()

# 상단 검색 및 설정 영역
col_search, col_space = st.columns([1.5, 1.5])
with col_search:
    # 종목명/코드 선택형 검색
    if not df_stocks.empty and 'Name' in df_stocks.columns:
        stock_options = df_stocks['Name'] + " (" + df_stocks['Code'] + ")"
        # 삼성전자 인덱스 찾기
        try:
            default_idx = int(df_stocks[df_stocks['Code'] == '005930'].index[0])
        except:
            default_idx = 0
            
        selected_stock = st.selectbox("종목 선택", options=stock_options, index=default_idx)
        symbol = re.sub(r'[^0-9]', '', selected_stock.split('(')[-1])
    else:
        symbol = st.text_input("종목 코드 직접 입력", value="005930")


# 사이드바 설정
st.sidebar.title("🛠️ 시스템 설정")
period_map = {"일봉": "daily", "주봉": "weekly"}
selected_period = st.sidebar.selectbox("차트 주기", list(period_map.keys()))
period = period_map[selected_period]

import json
import os

# 후보 종목 저장 파일 경로
WATCHLIST_FILE = "d:/일목/watchlist.json"

def save_watchlist(stocks):
    with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(stocks, f, ensure_ascii=False, indent=4)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# 사이드바 설정 계속
# 사이드바 설정 계속
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 시장 스캐너")

# 초보자를 위한 가격 필터 슬라이더
st.sidebar.markdown("💸 **희망 가격 범위 (1주당)**")
price_range = st.sidebar.slider(
    "가성비 종목 찾기",
    min_value=0,
    max_value=200000,
    value=(0, 50000),
    step=1000,
    format="%d원"
)

# 필터 고정형 체크박스 UI
st.sidebar.markdown("### 🔍 필터 조건 선택")
st.sidebar.info("선택한 모든 조건을 만족하는 종목만 포착합니다.")

f_super = st.sidebar.checkbox("🏆 슈퍼 픽 (핵심 조건 결합)", value=True)
f_box = st.sidebar.checkbox("📦 200일 박스권/매집", value=False)
f_major = st.sidebar.checkbox("🏢 기관·외인 쌍끌이", value=False)
f_bullish = st.sidebar.checkbox("🔥 정배열", value=False)
f_ma = st.sidebar.checkbox("🚀 5/10 신규돌파", value=False)
f_macd = st.sidebar.checkbox("📊 MACD 신규돌파", value=False)
f_cloud = st.sidebar.checkbox("☁️ 구름대 돌파", value=False)
f_golden = st.sidebar.checkbox("⚔️ 일목 골든크로스", value=False)
f_ygy = st.sidebar.checkbox("🕯️ 장악형", value=False)
f_score = st.sidebar.checkbox("💎 고점수(80점이상)", value=False)

# 회전율 필터 옵션
turnover_on = st.sidebar.checkbox("⚡ 회전율 5%~10% 필터링", value=False, help="거래가 활발하면서 과열되지 않은 '손바뀜' 종목만 골라냅니다.")

if st.sidebar.button("🚀 전 종목 스캔 시작", use_container_width=True):
    # 선택된 체크박스들을 리스트로 취합
    selected_modes = []
    if f_super: selected_modes.append("super_pick")
    if f_box: selected_modes.append("box_squeeze")
    if f_major: selected_modes.append("major_money")
    if f_bullish: selected_modes.append("bullish")
    if f_ma: selected_modes.append("ma_cross")
    if f_macd: selected_modes.append("macd_cross")
    if f_cloud: selected_modes.append("cloud_break")
    if f_golden: selected_modes.append("golden_cross")
    if f_ygy: selected_modes.append("ygy")
    if f_score: selected_modes.append("score")
    
    if not selected_modes:
        st.error("🚨 최소 하나 이상의 필터를 선택해주세요.")
    else:
        with st.expander("스캐너 실행 로그", expanded=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results_df = run_market_screener(
                period=period, 
                filter_modes=selected_modes, 
                progress_bar=progress_bar, 
                status_text=status_text,
                min_price=price_range[0],
                max_price=price_range[1],
                turnover_mode=turnover_on
            )
        
        if not results_df.empty:
            st.session_state.results_df = results_df # 저장을 위해 세션에 보관
            st.success(f"총 {len(results_df)}개의 가성비 유망 종목을 발견했습니다!")
            st.dataframe(results_df, use_container_width=True)
            st.info("💡 **초보 투자자 팁**: 이 결과 중 맘에 드는 종목들을 왼쪽의 '관심종목 저장' 버튼으로 저장해 두세요!")
        else:
            st.warning("해당 가격대에서 조건에 맞는 종목이 없습니다. 가격 범위를 조절해 보세요.")

st.sidebar.markdown("---")
st.sidebar.subheader("💾 실전 대비 관심종목")

watchlist = load_watchlist()

if st.sidebar.button("현재 스캔 결과 관심종목으로 저장"):
    if 'results_df' in st.session_state and not st.session_state.results_df.empty:
        save_watchlist(st.session_state.results_df.to_dict('records'))
        st.sidebar.success(f"{len(st.session_state.results_df)}개 종목 저장 완료!")
        watchlist = load_watchlist()
    else:
        st.sidebar.warning("먼저 스캔을 실행해 주세요.")

if watchlist:
    st.sidebar.markdown(f"**현재 저장된 후보: {len(watchlist)}개**")
    if st.sidebar.button("저장된 후보 리스트 비우기"):
        save_watchlist([])
        st.sidebar.info("관심종목을 비웠습니다.")
        watchlist = []

if st.sidebar.button("장중 실시간 필승 대조 시작"):
    if not watchlist:
        st.error("먼저 저녁에 스캔한 후보 종목을 저장해 주세요!")
    else:
        st.subheader("⚔️ 저장된 후보 vs 실시간 시장 기세 비교")
        api = KoreaFinance()
        codes = [s['코드'] for s in watchlist]
        
        with st.spinner("후보 종목들의 현재 기세를 분석 중..."):
            rt_results = api.fetch(codes)
            
            if rt_results:
                final_picks = []
                for rt in rt_results:
                    # 추천 강도 계산
                    pick_strength = "⭐⭐⭐" if rt['pct'] > 2 else "⭐⭐" if rt['pct'] > 0 else "⭐"
                    vol_emoji = "⚡" if rt['pct'] > 1 else ""
                    
                    final_picks.append({
                        "종목명": rt['name'],
                        "현재가": f"{int(rt['price']):,}",
                        "현재등락": f"{rt['pct']:+.2f}%",
                        "추천강도": pick_strength,
                        "실전기세": f"{vol_emoji} 활발" if rt['pct'] > 0 else "대기중"
                    })
                
                df_picks = pd.DataFrame(final_picks)
                st.table(df_picks)
                st.success("💡 **고수의 팁**: 저녁에 뽑은 종목 중 '추천강도'가 ⭐⭐⭐이고 '실전기세'가 활발한 종목이 오늘의 타겟입니다!")
            else:
                st.warning("현재 실시간 데이터를 가져올 수 없습니다. 장중(9:00~15:30)에 시도해 보세요.")

# 메인 차트 실행
df, df_daily, name, rt = load_data(symbol, period)

if not df.empty:
    last = df.iloc[-1]
    
    # 대시보드 메트릭
    m1, m2, m3, m4 = st.columns(4)
    price_val = rt['price'] if rt else last['Close']
    pct_val = rt['pct'] if rt else 0
    
    m1.metric("현재가", f"{int(price_val):,}", f"{pct_val:+.2f}%")
    
    # 시그널 상태
    sig_text = "관망 (WAIT)"
    sig_color = "#8b949e"
    if last['long_signal']: sig_text = "매수 (BUY)"; sig_color = "#ff5252"
    elif last['short_signal']: sig_text = "매도 (SELL)"; sig_color = "#00e676"
    elif last['tp_signal']: sig_text = "익절 (TP)"; sig_color = "#d29922"
    
    m2.markdown(f"""
        <div class='signal-card'>
            <span style='color: #8b949e; font-size: 0.9rem;'>매매 시그널</span><br>
            <span style='color: {sig_color}; font-size: 1.5rem; font-weight: bold;'>{sig_text}</span>
        </div>
    """, unsafe_allow_html=True)
    
    # 다이버전스
    div_text = "정상"
    div_color = "#8b949e"
    if last['bullish_divergence']: div_text = "상승 다이버전스"; div_color = "#ff5252"
    elif last['bearish_divergence']: div_text = "하락 다이버전스"; div_color = "#00e676"
    
    m3.markdown(f"""
        <div class='signal-card'>
            <span style='color: #8b949e; font-size: 0.9rem;'>다이버전스</span><br>
            <span style='color: {div_color}; font-size: 1.5rem; font-weight: bold;'>{div_text}</span>
        </div>
    """, unsafe_allow_html=True)
    
    m4.metric("종목명", name)

    # Plotly 차트 생성
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])

    # 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="가격", increasing_line_color='#ff5252', decreasing_line_color='#00e676'
    ), row=1, col=1)

    # 일목균형표 라인
    fig.add_trace(go.Scatter(x=df['Date'], y=df['tenkan_sen'], line=dict(color='#2962ff', width=1), name="전환선"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['kijun_sen'], line=dict(color='#ff9800', width=1), name="기준선"), row=1, col=1)
    
    # 구름대
    fig.add_trace(go.Scatter(x=df['Date'], y=df['senkou_span_a'], line=dict(color='rgba(0, 255, 0, 0.2)', width=0), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['senkou_span_b'], fill='tonexty', fillcolor='rgba(88, 166, 255, 0.2)', line=dict(color='rgba(255, 0, 0, 0.2)', width=0), name="구름대"), row=1, col=1)

    # 중심선 오실레이터
    colors = ['#ff5252' if v >= 0 else '#00e676' for v in df['center_line']]
    fig.add_trace(go.Bar(x=df['Date'], y=df['center_line'], marker_color=colors, name="중심선"), row=2, col=1)

    # 회색선 (모멘텀)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['gray_line'], line=dict(color='#8b949e', width=1.5), name="회색선"), row=3, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color="white", row=3, col=1)

    fig.update_layout(
        height=800, 
        template="plotly_white", 
        paper_bgcolor="#ffffff", 
        plot_bgcolor="#ffffff", 
        xaxis_rangeslider_visible=False,
        legend=dict(font=dict(color="#212529")),
        font=dict(color="#212529")
    )
    st.plotly_chart(fig, use_container_width=True)

    # 점수 현황
    st.markdown("---")
    score = last['sentiment_score']
    st.subheader(f"🛡️ 시장 에너지 점수: {int(score)}점")
    st.progress(int(score)/100)
    
else:
    st.error("데이터를 불러올 수 없습니다. 종목 코드를 확인해 주세요.")

st.sidebar.markdown("---")
st.sidebar.caption("Powered by Ichimoku Pro KR Engine")
