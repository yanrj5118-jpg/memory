import FinanceDataReader as fdr
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
import os

class KoreaFinance:
    def __init__(self):
        self.market_data_cache = {}

    def fetch_net_purchase_data(self):
        """
        당일 기관 및 외국인의 순매수 데이터를 가져와서 수급 상위 종목을 파악합니다.
        """
        try:
            target_date = datetime.now().strftime("%Y%m%d")
            # 오늘 데이터가 아직 안 올라왔을 수 있으므로 예외 처리
            df = stock.get_market_net_purchases_of_equities_by_ticker(target_date, target_date, "ALL")
            if df.empty or df['기관합계'].sum() == 0:
                prev_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                df = stock.get_market_net_purchases_of_equities_by_ticker(prev_date, prev_date, "ALL")
            
            # 기관과 외국인이 모두 순매수한 종목 필터링
            df['쌍끌이'] = (df['기관합계'] > 0) & (df['외국인합계'] > 0)
            return df[['기관합계', '외국인합계', '쌍끌이']].to_dict('index')
        except Exception as e:
            print(f"Net Purchase Fetch Error: {e}")
            return {}

    def fetch(self, symbols):
        """
        여러 종목 또는 지수의 실시간성 요약 데이터를 가져옵니다.
        """
        if not symbols:
            return []
        
        results = []
        target_date = datetime.now().strftime("%Y%m%d")
        
        try:
            # 시장 전체 데이터를 한 번에 가져와서 필터링 (속도 개선)
            df_kospi = stock.get_market_ohlcv_by_ticker(target_date, market="KOSPI")
            df_kosdaq = stock.get_market_ohlcv_by_ticker(target_date, market="KOSDAQ")
            
            if df_kospi.empty and df_kosdaq.empty:
                prev_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                df_kospi = stock.get_market_ohlcv_by_ticker(prev_date, market="KOSPI")
                df_kosdaq = stock.get_market_ohlcv_by_ticker(prev_date, market="KOSDAQ")
            
            df_all = pd.concat([df_kospi, df_kosdaq])
            
            for sym in symbols:
                # 1. 시장 지수인 경우 (KS11: 코스피, KQ11: 코스닥)
                if sym in ['KS11', 'KQ11']:
                    name = "코스피" if sym == 'KS11' else "코스닥"
                    try:
                        df_idx = stock.get_index_ohlcv_by_date(target_date, target_date, sym)
                        if df_idx.empty:
                            prev_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                            df_idx = stock.get_index_ohlcv_by_date(prev_date, prev_date, sym)
                        
                        if not df_idx.empty:
                            row = df_idx.iloc[-1]
                            results.append({
                                'symbol': sym, 'name': name, 'price': float(row['종가']),
                                'pct': float(row['등락률']), 'high': float(row['고가']),
                                'low': float(row['저가']), 'volume': int(row['거래량']), 'time': target_date
                            })
                        else:
                            # pykrx 실패 시 FDR 시도
                            df_fdr = fdr.DataReader(sym)
                            if not df_fdr.empty:
                                last = df_fdr.iloc[-1]
                                prev = df_fdr.iloc[-2] if len(df_fdr) > 1 else last
                                pct = (last['Close'] - prev['Close']) / prev['Close'] * 100
                                results.append({
                                    'symbol': sym, 'name': name, 'price': float(last['Close']),
                                    'pct': float(pct), 'high': float(last['High']),
                                    'low': float(last['Low']), 'volume': int(last['Volume']), 'time': target_date
                                })
                    except:
                        pass
                
                # 2. 일반 종목인 경우
                elif sym in df_all.index:
                    row = df_all.loc[sym]
                    name = stock.get_market_ticker_name(sym)
                    results.append({
                        'symbol': sym, 'name': name, 'price': float(row['종가']),
                        'pct': float(row['등락률']), 'high': float(row['고가']),
                        'low': float(row['저가']), 'volume': int(row['거래량']), 
                        'amount': float(row['거래대금']), 'time': target_date
                    })
                else:
                    # pykrx에 없으면 FDR로 개별 시도
                    try:
                        df_fdr = fdr.DataReader(sym)
                        if not df_fdr.empty:
                            last = df_fdr.iloc[-1]
                            results.append({
                                'symbol': sym, 'name': sym, 'price': float(last['Close']),
                                'pct': 0, 'high': float(last['High']),
                                'low': float(last['Low']), 'volume': int(last['Volume']), 'time': target_date
                            })
                    except:
                        pass
            return results
        except Exception as e:
            print(f"Error fetching real-time data: {e}")
            return []

    def get_kline_df(self, symbol, period='daily'):
        """
        특정 종목의 K-라인(OHLCV) 데이터를 가져옵니다.
        """
        try:
            # FinanceDataReader는 '005930' 형태의 코드를 바로 지원함
            # 최근 500거래일 정도 가져옴 (일목균형표 선행스팬 등을 위해 충분히)
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
            df = fdr.DataReader(symbol, start_date)
            
            if df.empty:
                return pd.DataFrame()
            
            df = df.reset_index()
            # 컬럼명 표준화 (Date, Open, High, Low, Close, Volume)
            # FDR은 기본적으로 Date(Index), Open, High, Low, Close, Volume, Change를 제공함
            
            if period == 'weekly':
                df.set_index('Date', inplace=True)
                df = df.resample('W').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna().reset_index()
            
            return df
        except Exception as e:
            print(f"Error fetching K-line for {symbol}: {e}")
            return pd.DataFrame()

    def get_all_target_stocks_with_snapshot(self):
        """
        시장 전체의 시세 요약 데이터를 가져옵니다. 
        주말/공휴일 대응을 위해 최근 7일 내 가장 최근 영업일을 자동으로 찾습니다.
        """
        try:
            df_cap = pd.DataFrame()
            for i in range(7):
                target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                try:
                    df_cap = stock.get_market_cap_by_ticker(target_date, market="ALL")
                    if not df_cap.empty:
                        break
                except:
                    continue
            
            if df_cap.empty:
                # pykrx 실패 시 FinanceDataReader로 최종 보루
                df_fdr = fdr.StockListing('KRX')
                if not df_fdr.empty:
                    # FDR 컬럼명: Code, Name, Marcap, Close, Stocks, Volume, Amount 등
                    df_fdr = df_fdr.rename(columns={
                        'Code': 'Code', 'Name': 'Name', 
                        'Marcap': '시가총액', 'Close': '종가', 
                        'Stocks': '상장주식수', 'Volume': '거래량', 
                        'Amount': '거래대금'
                    })
                    return df_fdr
                return pd.DataFrame()
            
            df_cap = df_cap.reset_index()
            # pykrx columns: [티커, 종가, 시가총액, 거래량, 거래대금, 상장주식수]
            df_cap.columns = ['Code', '종가', '시가총액', '거래량', '거래대금', '상장주식수']
            # 이름 매핑 (캐시 활용)
            df_cap['Name'] = df_cap['Code'].apply(lambda x: stock.get_market_ticker_name(x))
            return df_cap
        except Exception as e:
            print(f"Snapshot Final Error: {e}")
            return pd.DataFrame()

    def get_all_target_stocks(self):
        """
        기존 방식의 전 종목 리스트 반환 (하위 호환성 유지)
        """
        df = self.get_all_target_stocks_with_snapshot()
        if df.empty:
            return [{'Code': '005930', 'Name': '삼성전자', '시가총액': 0, '종가': 0, '상장주식수': 5969782550}]
        return df.to_dict('records')

    def get_fundamentals(self, symbol):
        """
        특정 종목의 재무 지표(PER, PBR, EPS, 배당수익률 등)를 가져옵니다.
        """
        try:
            # 최근 7일 내 가장 최근 영업일의 재무 데이터 탐색
            for i in range(7):
                target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                try:
                    df = stock.get_market_fundamental_by_ticker(target_date, target_date, "ALL")
                    if not df.empty and symbol in df.index:
                        row = df.loc[symbol]
                        return {
                            'BPS': float(row['BPS']),
                            'PER': float(row['PER']),
                            'PBR': float(row['PBR']),
                            'EPS': float(row['EPS']),
                            'DIV': float(row['배당수익률']),
                            'DPS': float(row['주당배당금'])
                        }
                except:
                    continue
            return {}
        except Exception as e:
            print(f"Fundamentals Fetch Error for {symbol}: {e}")
            return {}

if __name__ == "__main__":
    api = KoreaFinance()
    print("삼성전자 데이터 테스트 중...")
    df = api.get_kline_df('005930')
    if not df.empty:
        print(df.tail())
    else:
        print("데이터를 가져오지 못했습니다.")
