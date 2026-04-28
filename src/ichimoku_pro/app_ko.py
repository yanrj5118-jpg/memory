import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from korea_finance import KoreaFinance
from advanced_ichimoku_logic import analyze_ichimoku
from stock_screener_ko import run_market_screener
from datetime import datetime
import re
import json
import os

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
    
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #dee2e6;
    }
    
    .stButton > button {
        background-color: #007bff !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }
    
    div[data-testid="stTextInput"] input {
        background-color: #ffffff !important;
        color: #007bff !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 12px !important;
        font-size: 1.5rem !important;
        text-align: center !important;
        font-weight: bold !important;
    }
    
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
        return pd.DataFrame(), pd.DataFrame(), "알 수 없음", None, None
        
    rt_data = api.fetch([symbol])
    rt = rt_data[0] if rt_data else None
    name = rt['name'] if rt else symbol
    
    df = analyze_ichimoku(df)
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean() # 200일선 추가
    
    # MACD 계산
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    fundamentals = api.get_fundamentals(symbol)
    df_daily = df if period == 'daily' else api.get_kline_df(symbol, period='daily')
    
    return df, df_daily, name, rt, fundamentals

# 후보 종목 저장 파일 경로
WATCHLIST_FILE = "d:/일목/watchlist.json"
SETTINGS_FILE = "d:/일목/settings.json"

def save_watchlist(stocks):
    with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(stocks, f, ensure_ascii=False, indent=4)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "price_range": [0, 50000],
        "filters": {"super": True, "box_break": False, "box": False, "major": False, "bullish": False, "ma": False, "macd": False, "cloud": False, "golden": False, "ygy": False, "score": False},
        "turnover_on": False
    }

# 초기화
if 'current_symbol' not in st.session_state: st.session_state.current_symbol = "005930"
if 'result_idx' not in st.session_state: st.session_state.result_idx = 0
if 'settings' not in st.session_state: st.session_state.settings = load_settings()

# 메인 헤더
st.markdown("<h1 style='text-align: center; color: #007bff;'>📊 일목균형표 Pro (Ichimoku Professional)</h1>", unsafe_allow_html=True)

# 지수 모니터링
api = KoreaFinance()
indices = api.fetch(['KS11', 'KQ11'])
if indices:
    data_date = indices[0]['time']
    # 날짜 형식 변환 (YYYYMMDD -> YYYY-MM-DD)
    formatted_date = f"{data_date[:4]}-{data_date[4:6]}-{data_date[6:]}"
    st.markdown(f"<div style='text-align: right; color: #6c757d; font-size: 0.9rem; margin-bottom: 5px;'>📅 데이터 기준일: {formatted_date} (주말/휴일 대응 완료)</div>", unsafe_allow_html=True)
    
    idx_cols = st.columns(len(indices))
    for i, idx in enumerate(indices):
        color = "#ff5252" if idx['pct'] >= 0 else "#00e676"
        idx_cols[i].markdown(f"""
            <div style='background-color: white; border: 1px solid #dee2e6; padding: 10px; border-radius: 12px; text-align: center;'>
                <span style='color: #6c757d; font-size: 0.8rem;'>{idx['name']}</span><br>
                <span style='color: {color}; font-size: 1.2rem; font-weight: bold;'>{idx['price']:,.2f}</span>
                <span style='color: {color}; font-size: 0.9rem;'> ({idx['pct']:+.2f}%)</span>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 검색 및 설정 영역
df_stocks_raw = api.get_all_target_stocks()
df_stocks = pd.DataFrame(df_stocks_raw)

col_search, col_space = st.columns([1.5, 1.5])
with col_search:
    if not df_stocks.empty:
        stock_options = df_stocks['Name'] + " (" + df_stocks['Code'] + ")"
        try:
            target_idx = int(df_stocks[df_stocks['Code'] == st.session_state.current_symbol].index[0])
        except: target_idx = 0
        selected_stock = st.selectbox("🔍 종목 검색", options=stock_options, index=target_idx)
        st.session_state.current_symbol = re.sub(r'[^0-9]', '', selected_stock.split('(')[-1])

# 사이드바
st.sidebar.title("🛠️ 시스템 설정")
period_map = {"일봉": "daily", "주봉": "weekly"}
period = period_map[st.sidebar.selectbox("차트 주기", list(period_map.keys()))]

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 시장 스캐너")
price_range = st.sidebar.slider("희망 가격 범위", 0, 200000, tuple(st.session_state.settings['price_range']), step=1000, format="%d원")

saved_filters = st.session_state.settings['filters']
f_super = st.sidebar.checkbox("🏆 슈퍼 픽", value=saved_filters.get("super", True))
f_box_break = st.sidebar.checkbox("🚀 박스권 돌파", value=saved_filters.get("box_break", False))
f_box = st.sidebar.checkbox("📦 200일 박스권/매집", value=saved_filters.get("box", False))
f_major = st.sidebar.checkbox("🏢 기관·외인 쌍끌이", value=saved_filters.get("major", False))
f_bullish = st.sidebar.checkbox("🔥 정배열", value=saved_filters.get("bullish", False))
f_ma = st.sidebar.checkbox("🚀 5/10 신규돌파", value=saved_filters.get("ma", False))
f_macd = st.sidebar.checkbox("📊 MACD 신규돌파", value=saved_filters.get("macd", False))
f_cloud = st.sidebar.checkbox("☁️ 구름대 돌파", value=saved_filters.get("cloud", False))
f_golden = st.sidebar.checkbox("⚔️ 일목 골든크로스", value=saved_filters.get("golden", False))
f_ygy = st.sidebar.checkbox("🕯️ 장악형", value=saved_filters.get("ygy", False))
f_score = st.sidebar.checkbox("💎 고점수(80점이상)", value=saved_filters.get("score", False))
turnover_on = st.sidebar.checkbox("⚡ 회전율 5%~10% 필터", value=st.session_state.settings['turnover_on'])

if st.sidebar.button("🚀 전 종목 스캔 시작", use_container_width=True):
    modes = []
    if f_super: modes.append("super_pick")
    if f_box_break: modes.append("box_breakout")
    if f_box: modes.append("box_squeeze")
    if f_major: modes.append("major_money")
    if f_bullish: modes.append("bullish")
    if f_ma: modes.append("ma_cross")
    if f_macd: modes.append("macd_cross")
    if f_cloud: modes.append("cloud_break")
    if f_golden: modes.append("golden_cross")
    if f_ygy: modes.append("ygy")
    if f_score: modes.append("score")
    
    with st.expander("스캐너 실행 로그", expanded=True):
        res = run_market_screener(period, modes, st.progress(0), st.empty(), price_range[0], price_range[1], turnover_on)
        if not res.empty:
            st.session_state.results_df = res
            st.session_state.current_symbol = res.iloc[0]['코드']
            st.session_state.result_idx = 0
            st.success(f"{len(res)}개 종목 포착!")
        else: st.warning("조건에 맞는 종목이 없습니다.")

# 스캔 결과 탐색
if 'results_df' in st.session_state and not st.session_state.results_df.empty:
    results_df = st.session_state.results_df
    st.markdown("---")
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ 이전 종목", use_container_width=True):
            st.session_state.result_idx = (st.session_state.result_idx - 1) % len(results_df)
            st.session_state.current_symbol = results_df.iloc[st.session_state.result_idx]['코드']
            st.rerun()
    with col_info:
        st.markdown(f"<div style='text-align: center; font-weight: bold; color: #007bff;'>{st.session_state.result_idx+1}/{len(results_df)} [{results_df.iloc[st.session_state.result_idx]['종목명']}]</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("다음 종목 ➡️", use_container_width=True):
            st.session_state.result_idx = (st.session_state.result_idx + 1) % len(results_df)
            st.session_state.current_symbol = results_df.iloc[st.session_state.result_idx]['코드']
            st.rerun()

# 관심종목 관리
st.sidebar.markdown("---")
if st.sidebar.button("현재 결과 관심종목 저장"):
    if 'results_df' in st.session_state: save_watchlist(st.session_state.results_df.to_dict('records'))
    st.sidebar.success("저장 완료!")

watchlist = load_watchlist()
if st.sidebar.button("장중 실시간 필승 대조"):
    if not watchlist: st.error("먼저 후보를 저장해 주세요!")
    else:
        st.subheader("⚔️ 실시간 시장 기세 비교")
        rt_res = api.fetch([s['코드'] for s in watchlist])
        if rt_res:
            final = []
            for r in rt_res:
                final.append({"종목명": r['name'], "현재가": f"{int(r['price']):,}", "등락": f"{r['pct']:+.2f}%", "기세": "⭐⭐⭐" if r['pct'] > 2 else "⭐"})
            st.table(pd.DataFrame(final))

# 메인 데이터 로딩 및 차트
df, df_daily, name, rt, fundamentals = load_data(st.session_state.current_symbol, period)
if not df.empty:
    last = df.iloc[-1]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("현재가", f"{int(rt['price'] if rt else last['Close']):,}", f"{(rt['pct'] if rt else 0):+.2f}%")
    
    sig_text = "관망"; sig_color = "#8b949e"
    if last['long_signal']: sig_text = "매수"; sig_color = "#ff5252"
    elif last['short_signal']: sig_text = "매도"; sig_color = "#00e676"
    m2.markdown(f"<div class='signal-card'><span style='color: {sig_color}; font-size: 1.5rem; font-weight: bold;'>{sig_text}</span></div>", unsafe_allow_html=True)
    
    div_text = "정상"; div_color = "#8b949e"
    if last['bullish_divergence']: div_text = "상승 다이버"; div_color = "#ff5252"
    m3.markdown(f"<div class='signal-card'><span style='color: {div_color}; font-size: 1.5rem; font-weight: bold;'>{div_text}</span></div>", unsafe_allow_html=True)
    m4.metric("종목명", name)

    # --- [고도화 차트 1] ---
    st.markdown("### 1️⃣ 박스권 돌파 및 거래량 분석 (Price & Volume)")
    df_200 = df.tail(200)
    h_line = df_200['High'].max()
    l_line = df_200['Low'].min()
    
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    # 박스 영역
    fig1.add_trace(go.Scatter(x=df['Date'].tolist() + df['Date'].tolist()[::-1], y=[h_line]*len(df) + [l_line]*len(df), fill='toself', fillcolor='rgba(135, 206, 250, 0.07)', line=dict(color='rgba(0,0,0,0)'), showlegend=False), secondary_y=False)
    # 거래량 오버레이
    vol_colors = ['rgba(255, 82, 82, 0.3)' if c >= o else 'rgba(0, 230, 118, 0.3)' for c, o in zip(df['Close'], df['Open'])]
    fig1.add_trace(go.Bar(x=df['Date'], y=df['Volume'], marker_color=vol_colors, name="거래량", showlegend=False), secondary_y=True)
    # 볼린저 밴드
    fig1.add_trace(go.Scatter(x=df['Date'], y=df['BB_upper'], line=dict(color='rgba(173,181,189,0.2)', dash='dot'), name="BB상단", showlegend=False), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Date'], y=df['BB_lower'], line=dict(color='rgba(173,181,189,0.2)', dash='dot'), fill='tonexty', fillcolor='rgba(173,181,189,0.05)', name="BB하단", showlegend=False), secondary_y=False)
    # 캔들
    fig1.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#ff5252', decreasing_line_color='#00e676', name="가격"), secondary_y=False)
    
    # 6. 이동평균선
    fig1.add_trace(go.Scatter(x=df['Date'], y=df['MA5'], line=dict(color='#ffeb3b', width=2), name="MA5"), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], line=dict(color='#e040fb', width=2), name="MA20"), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df['Date'], y=df['MA200'], line=dict(color='#212529', width=2, dash='solid'), name="MA200"), secondary_y=False) # 200일선 추가

    # 지지 저항
    fig1.add_hline(y=h_line, line_dash="dash", line_color="#ff1744", annotation_text="🚀 저항")
    fig1.add_hline(y=l_line, line_dash="dash", line_color="#2979ff", annotation_text="🛡️ 지지")
    
    fig1.update_layout(
        height=600, 
        template="plotly_white", 
        xaxis_rangeslider_visible=False, 
        margin=dict(l=10, r=10, t=30, b=10), 
        xaxis=dict(range=[df['Date'].iloc[-100] if len(df) > 100 else df['Date'].iloc[0], df['Date'].iloc[-1]], gridcolor='rgba(0,0,0,0.03)'),
        yaxis=dict(title="가격", side="right", showgrid=True, gridcolor='rgba(0,0,0,0.05)', fixedrange=False),
        yaxis2=dict(overlaying="y", side="left", range=[0, df['Volume'].max()*5], showgrid=False, showticklabels=False),
        hovermode="x unified",
        xaxis_showspikes=True, yaxis_showspikes=True,
        xaxis_spikemode="across", yaxis_spikemode="across",
        xaxis_spikethickness=1, yaxis_spikethickness=1,
        xaxis_spikedash="dot", yaxis_spikedash="dot",
        dragmode="pan"
    )
    st.plotly_chart(fig1, use_container_width=True, config={'scrollZoom': True})

    # --- [차트 2: 일목] ---
    st.markdown("### 2️⃣ 일목균형표 정밀 분석 (Ichimoku Detail)")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df['Date'], y=df['Close'], line=dict(color='rgba(0,0,0,0.1)'), name="종가"))
    fig2.add_trace(go.Scatter(x=df['Date'], y=df['tenkan_sen'], line=dict(color='#2962ff'), name="전환선"))
    fig2.add_trace(go.Scatter(x=df['Date'], y=df['kijun_sen'], line=dict(color='#ff9800'), name="기준선"))
    fig2.add_trace(go.Scatter(x=df['Date'], y=df['senkou_span_a'], line=dict(width=0), showlegend=False))
    fig2.add_trace(go.Scatter(x=df['Date'], y=df['senkou_span_b'], fill='tonexty', fillcolor='rgba(88, 166, 255, 0.2)', line=dict(width=0), name="구름대"))
    fig2.update_layout(
        height=400, 
        template="plotly_white", 
        xaxis_rangeslider_visible=False, 
        margin=dict(l=10, r=10, t=30, b=10),
        # 인터랙션 추가
        hovermode="x unified",
        xaxis=dict(range=[df['Date'].iloc[-100] if len(df) > 100 else df['Date'].iloc[0], df['Date'].iloc[-1]], gridcolor='rgba(0,0,0,0.03)'),
        xaxis_showspikes=True, yaxis_showspikes=True,
        xaxis_spikemode="across", yaxis_spikemode="across",
        xaxis_spikethickness=1, yaxis_spikethickness=1,
        dragmode="pan"
    )
    st.plotly_chart(fig2, use_container_width=True, config={'scrollZoom': True})

    # --- [차트 3: 모멘텀] ---
    st.markdown("### 3️⃣ 모멘텀 및 수급 분석 (Momentum)")
    fig3 = go.Figure()
    colors = ['#ff5252' if v >= 0 else '#00e676' for v in df['center_line']]
    fig3.add_trace(go.Bar(x=df['Date'], y=df['center_line'], marker_color=colors, name="수급에너지"))
    fig3.add_trace(go.Scatter(x=df['Date'], y=df['gray_line'], line=dict(color='#8b949e', width=2), name="모멘텀"))
    fig3.add_hline(y=0, line_dash="dot", line_color="#dee2e6")
    fig3.update_layout(
        height=300, 
        template="plotly_white", 
        margin=dict(l=10, r=10, t=30, b=10),
        # 인터랙션 추가
        hovermode="x unified",
        xaxis=dict(range=[df['Date'].iloc[-100] if len(df) > 100 else df['Date'].iloc[0], df['Date'].iloc[-1]], gridcolor='rgba(0,0,0,0.03)'),
        xaxis_showspikes=True, yaxis_showspikes=True,
        xaxis_spikemode="across", yaxis_spikemode="across",
        xaxis_spikethickness=1, yaxis_spikethickness=1,
        dragmode="pan"
    )
    st.plotly_chart(fig3, use_container_width=True, config={'scrollZoom': True})

    # --- [차트 4: MACD] ---
    st.markdown("### 4️⃣ MACD 추세 및 신호 분석 (MACD)")
    fig4 = go.Figure()
    # 히스토그램
    hist_colors = ['#ff5252' if v >= 0 else '#00e676' for v in df['MACD_Hist']]
    fig4.add_trace(go.Bar(x=df['Date'], y=df['MACD_Hist'], marker_color=hist_colors, name="MACD Hist"))
    # MACD & Signal 라인
    fig4.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], line=dict(color='#2962ff', width=1.5), name="MACD"))
    fig4.add_trace(go.Scatter(x=df['Date'], y=df['MACD_Signal'], line=dict(color='#ff9800', width=1.5, dash='dot'), name="Signal"))
    fig4.add_hline(y=0, line_dash="dot", line_color="#dee2e6")
    fig4.update_layout(
        height=300, 
        template="plotly_white", 
        margin=dict(l=10, r=10, t=30, b=10),
        # 인터랙션 추가
        hovermode="x unified",
        xaxis=dict(range=[df['Date'].iloc[-100] if len(df) > 100 else df['Date'].iloc[0], df['Date'].iloc[-1]], gridcolor='rgba(0,0,0,0.03)'),
        xaxis_showspikes=True, yaxis_showspikes=True,
        xaxis_spikemode="across", yaxis_spikemode="across",
        xaxis_spikethickness=1, yaxis_spikethickness=1,
        dragmode="pan"
    )
    st.plotly_chart(fig4, use_container_width=True, config={'scrollZoom': True})

    # 분석표
    st.markdown("---")
    col_box, col_fund = st.columns(2)
    with col_box:
        st.subheader("📦 200일 박스권 분석")
        h2, l2 = df_200['High'].max(), df_200['Low'].min()
        box_range = (h2 - l2) / l2 * 100
        st.info(f"최고: {int(h2):,}원 / 최저: {int(l2):,}원 / 변동폭: {box_range:.2f}%")
        st.progress(min(1.0, (last['Close'] - l2) / (h2 - l2)) if h2 != l2 else 0)
    with col_fund:
        st.subheader("🏢 기업 재무 하이라이트")
        if fundamentals:
            f_df = pd.DataFrame({
                "지표": ["PER", "PBR", "배당률", "EPS"],
                "값": [f"{fundamentals.get('PER',0):.2f}", f"{fundamentals.get('PBR',0):.2f}", f"{fundamentals.get('DIV',0):.2f}%", f"{int(fundamentals.get('EPS',0)):,}"]
            })
            st.table(f_df)
        else: st.warning("재무 데이터 없음")
else: st.error("데이터 로딩 실패")
