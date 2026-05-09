# 📊 일목균형표 Pro (v10) - 최종 개발 지식 항목 (Knowledge Item)

## 1. 프로젝트 개요
*   **목적**: 200일 박스권 돌파 전략과 일목균형표를 결합한 고성능 주식 스캐너 및 정밀 분석 도구.
*   **대상**: 한국 시장(KOSPI/KOSDAQ) 전 종목.
*   **특징**: 휴일 대응 로직, 중국 환경 호환성, 전문가용 4단 인터랙티브 차트.

## 2. 핵심 기술 스택
*   **Core**: Python 3.10+, Streamlit (UI Framework)
*   **Data**: PyKRX (Market Data), FinanceDataReader (Backup/Indices)
*   **Visualization**: Plotly (Subplots & Interactive Charts)
*   **Logic**: Pandas, Custom Indicator Library (`advanced_ichimoku_logic.py`)

## 3. 주요 구현 기능 및 노하우 (Key Achievements)

### 📈 4단 전문가용 차트 시스템
- **Chart 1 (Price & Box)**: 200일 최고/최저가 시각화(Shaded Area) 및 MA200(대세 생명선) 통합. 거래량 오버레이 적용.
- **Chart 2 (Ichimoku)**: 구름대와 기준선을 통한 지지/저항 정밀 분석.
- **Chart 3 (Momentum)**: 수급 점수(Center Line)와 모멘텀(Gray Line) 시각화.
- **Chart 4 (MACD)**: 추세 반전 포착을 위한 MACD 및 히스토그램 추가.

### 🖱️ 하이테크 인터랙션
- **인터랙티브 제어**: 모든 차트에 휠 줌(Scroll Zoom), 위치 이동(Pan), 십자선(Crosshair) 기능 적용.
- **갤러리 모드**: 스캔된 종목들을 '이전/다음' 버튼으로 빠르게 순회하며 분석 가능.

### 🌍 글로벌 및 환경 대응
- **중국 환경 호환성**: 인코딩 충돌 방지를 위해 배포 배치 파일(`build_exe.bat`, `setup_and_run.bat`)을 순수 영문(ASCII)으로 작성.
- **주말/휴일 자동 대응**: 장이 열리지 않는 날에는 자동으로 가장 최근 영업일(금요일 등) 데이터를 탐색하여 분석 중단을 방지.

### 💾 설정 보존 및 편의성
- **설정 저장**: `settings.json`을 통해 사용자의 필터링 설정(가격대, 체크박스 상태)을 영구 보관.
- **데이터 내보내기**: 분석 결과를 엑셀 호환 CSV(UTF-8-SIG)로 즉시 다운로드 가능.

## 4. 향후 유지보수 가이드 (Maintenance)
- **필터 완화**: 시장 거래대금이 줄어들 경우 `stock_screener_ko.py` 내의 `turnover` 기준(현재 1.5%~20%)을 조정할 것.
- **패키징**: EXE 빌드 시 `PyInstaller`의 `--collect-all` 옵션을 사용하여 Streamlit 종속성을 포함할 것.

---
**Antigravity Agent** - *사용자의 투자 파트너로서 작성됨 (2026-04-25)*
