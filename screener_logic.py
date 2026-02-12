"""
PACPL Screener Logic - Ported from Pine Script
Implements gap analysis, ORB breakouts, and PDH/PDL retest signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from config import *


# Cache for bad symbols to avoid repeated timeouts
BAD_SYMBOLS = set()

def get_stock_data(symbol, timeframe="5m", days=5):
    """
    Fetch intraday data for a stock
    Returns data for specified timeframe interval
    """
    if symbol in BAD_SYMBOLS:
        return None
        
    try:
        ticker = yf.Ticker(symbol)
        
        # Adjust period based on interval constraints
        # 1m data is available for last 7 days max
        # 2m-90m data available for last 60 days
        period = f"{days}d"
        
        if timeframe == "1m":
            period = "5d"  # Request 5 days for 1m to ensure we trigger "last 7 days" range
            
        # Get data for specified timeframe
        data = ticker.history(period=period, interval=timeframe)
        
        if data.empty:
            # print(f"DEBUG: No data for {symbol}, marking as bad")
            BAD_SYMBOLS.add(symbol)
            return None
            
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol} ({timeframe}): {e}")
        if "delisted" in str(e).lower() or "no data" in str(e).lower():
            BAD_SYMBOLS.add(symbol)
        return None


def calculate_daily_levels(df):
    """
    Calculate Previous Day Close (PDC), High (PDH), Low (PDL)
    """
    if df is None or len(df) < 2:
        return None, None, None
    
    # Get yesterday's date
    df['Date'] = pd.to_datetime(df.index).date
    dates = df['Date'].unique()
    
    if len(dates) < 2:
        return None, None, None
    
    # Get previous day's data
    prev_date = dates[-2]
    prev_day_data = df[df['Date'] == prev_date]
    
    if prev_day_data.empty:
        return None, None, None
    
    pdc = prev_day_data['Close'].iloc[-1]
    pdh = prev_day_data['High'].max()
    pdl = prev_day_data['Low'].min()
    
    return pdc, pdh, pdl


def calculate_orb(df, orb_mins=ORB_MINS):
    """
    Calculate Opening Range Breakout levels
    Returns ORB High and ORB Low
    """
    if df is None or len(df) < 1:
        return None, None
    
    # Get today's data
    df['Date'] = pd.to_datetime(df.index).date
    today = df['Date'].iloc[-1]
    today_data = df[df['Date'] == today]
    
    if today_data.empty:
        return None, None
    
    # Parse timeframe to minutes
    tf_mins = 5 # Default
    if 'm' in df.index.freqstr if hasattr(df.index, 'freqstr') and df.index.freqstr else '5m':
         # Fallback generic parsing
         pass
         
    # Simple extraction since we pass timeframe string to scan_stock
    # But here we only have df. 
    # Let's infer from data diff or assume logic based on input?
    # Better: calculate time diff between first two rows
    if len(df) > 1:
        t1 = df.index[0]
        t2 = df.index[1]
        diff = (t2 - t1).total_seconds() / 60
        tf_mins = int(diff)
    
    # Calculate number of bars for ORB
    # orb_mins is total minutes (e.g. 15)
    # tf_mins is candle size (e.g. 1, 2, 5)
    orb_bars = max(1, int(orb_mins / tf_mins))
    
    # Get first N bars of the day
    orb_data = today_data.head(orb_bars)
    
    if orb_data.empty:
        return None, None
    
    orb_high = orb_data['High'].max()
    orb_low = orb_data['Low'].min()
    
    return orb_high, orb_low


def detect_gap(open_price, pdc):
    """
    Detect gap type: Large Up, Large Down, or Small Gap
    Returns: gap_pct, is_large_up, is_large_down, is_small_gap
    """
    if pdc == 0 or pdc is None:
        return 0, False, False, False
    
    gap_pct = ((open_price - pdc) / pdc) * 100.0
    
    is_large_up = gap_pct >= LARGE_GAP
    is_large_down = gap_pct <= -LARGE_GAP
    is_small_gap = not (is_large_up or is_large_down)
    
    return gap_pct, is_large_up, is_large_down, is_small_gap


def check_after_918(df):
    """
    Check if current time is after 9:18 AM
    """
    if df is None or len(df) < 1:
        return False
    
    current_time = pd.to_datetime(df.index[-1])
    current_mins = current_time.hour * 60 + current_time.minute
    
    print(f"DEBUG_TIME: Last={current_time} Mins={current_mins} Threshold={AFTER_918_MINS}")
    return current_mins >= AFTER_918_MINS


def check_signals(df, pdc, pdh, pdl, orb_high, orb_low):
    """
    Check for all PACPL trading signals
    Returns: dict with signal information
    """
    signals = {
        'follow_long': False,
        'follow_short': False,
        'fade_long': False,
        'fade_short': False,
        'reversal_long': False,
        'reversal_short': False,
        'trend_long': False,
        'trend_short': False,
        'pdh_retest_long': False,
        'pdl_retest_short': False,
        'signal_type': None,
        'signal_dir': None,
        'price': None
    }
    
    if df is None or len(df) < 1:
        return signals
    
    # Get today's data
    df['Date'] = pd.to_datetime(df.index).date
    today = df['Date'].iloc[-1]
    today_data = df[df['Date'] == today].copy()
    
    if today_data.empty:
        return signals
    
    # Current bar data
    current = today_data.iloc[-1]
    current_close = current['Close']
    current_high = current['High']
    current_low = current['Low']
    current_open = today_data.iloc[0]['Open']
    
    signals['price'] = current_close
    
    # Check if after 9:18 AM
    after_918 = check_after_918(today_data)
    if not after_918:
        # print(f"DEBUG {df.name if hasattr(df,'name') else ''}: before 9:18")
        return signals
    
    # Calculate gap
    gap_pct, is_large_up, is_large_down, is_small_gap = detect_gap(current_open, pdc)
    # Check if beyond sustain period
    sustain_bars = max(1, SUSTAIN_MINS // 5)
    beyond_sustain = len(today_data) >= sustain_bars

    print(f"DEBUG_SIG: {df.name if hasattr(df,'name') else 'Stock'} Gap={gap_pct:.2f} LUp={is_large_up} LDn={is_large_down} Sm={is_small_gap} Close={current_close} ORB_H={orb_high} ORB_L={orb_low} Sus={beyond_sustain}")
    
    # ===== FOLLOW SIGNALS (Large Gap) =====
    if is_large_up and beyond_sustain and orb_high is not None:
        if current_close > orb_high:
            signals['follow_long'] = True
            signals['signal_type'] = 'Follow'
            signals['signal_dir'] = 'LONG'
            print("DEBUG_SIG: Triggered Follow Long")
    
    if is_large_down and beyond_sustain and orb_low is not None:
        if current_close < orb_low:
            signals['follow_short'] = True
            signals['signal_type'] = 'Follow'
            signals['signal_dir'] = 'SHORT'
            print("DEBUG_SIG: Triggered Follow Short")
    
    # ===== FADE SIGNALS (Small Gap) =====
    if is_small_gap and orb_low is not None and gap_pct > 0:
        if current_close < orb_low:
            signals['fade_short'] = True
            signals['signal_type'] = 'Fade'
            signals['signal_dir'] = 'SHORT'
            print("DEBUG_SIG: Triggered Fade Short")
    
    if is_small_gap and orb_high is not None and gap_pct < 0:
        if current_close > orb_high:
            signals['fade_long'] = True
            signals['signal_type'] = 'Fade'
            signals['signal_dir'] = 'LONG'
            print("DEBUG_SIG: Triggered Fade Long")

    # ===== REVERSAL SIGNALS (3rd Condition) =====
    # Large Gap Down + Break ORB High -> Long
    if is_large_down and beyond_sustain and orb_high is not None:
        if current_close > orb_high:
            signals['reversal_long'] = True
            signals['signal_type'] = '3rd Condition'
            signals['signal_dir'] = 'LONG'
            print("DEBUG_SIG: Triggered Reversal Long")
            
    # Large Gap Up + Break ORB Low -> Short
    if is_large_up and beyond_sustain and orb_low is not None:
        if current_close < orb_low:
            signals['reversal_short'] = True
            signals['signal_type'] = '3rd Condition'
            signals['signal_dir'] = 'SHORT'
            print("DEBUG_SIG: Triggered Reversal Short")
    
    # ===== 3rd CONDITION: TREND (Small Gap Continuation) =====
    if is_small_gap and orb_high is not None and gap_pct > 0: # Small Gap Up -> Break High (Trend)
        if current_close > orb_high:
            signals['trend_long'] = True
            signals['signal_type'] = '3rd Condition'
            signals['signal_dir'] = 'LONG'
            print("DEBUG_SIG: Triggered Trend Long")
            
    if is_small_gap and orb_low is not None and gap_pct < 0: # Small Gap Down -> Break Low (Trend)
        if current_close < orb_low:
            signals['trend_short'] = True
            signals['signal_type'] = '3rd Condition'
            signals['signal_dir'] = 'SHORT'
            print("DEBUG_SIG: Triggered Trend Short")

    # ===== PDH/PDL RETEST SIGNALS =====
    if pdh is not None and pdl is not None:
        # Check if PDH was broken recently
        broke_pdh = any(today_data['Close'] > pdh)
        broke_pdl = any(today_data['Close'] < pdl)
        
        band_up = pdh * (1 + TOL_PCT / 100.0)
        band_dn = pdl * (1 - TOL_PCT / 100.0)
        
        # PDH Retest Long
        if broke_pdh and current_low <= band_up and current_close > pdh:
            signals['pdh_retest_long'] = True
            signals['signal_type'] = 'PDH_Retest'
            signals['signal_dir'] = 'LONG'
            print("DEBUG_SIG: Triggered PDH Retest")
        
        # PDL Retest Short
        if broke_pdl and current_high >= band_dn and current_close < pdl:
            signals['pdl_retest_short'] = True
            signals['signal_type'] = 'PDL_Retest'
            signals['signal_dir'] = 'SHORT'
            print("DEBUG_SIG: Triggered PDL Retest")
    
    # Calculate ATR (14)
    # Calculate ATR (14) using Wilder's Smoothing (RMA) to match TradingView
    try:
        if len(df) > 14:
            prev_close = df['Close'].shift(1)
            tr1 = df['High'] - df['Low']
            tr2 = (df['High'] - prev_close).abs()
            tr3 = (df['Low'] - prev_close).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            # Wilder's Smoothing (RMA) formula
            atr_series = tr.ewm(alpha=1/14, adjust=False).mean()
            atr = atr_series.iloc[-1]
        else:
            atr = 0
    except:
        atr = 0

    return enrich_signals_with_targets(signals, current_high, current_low, atr)
    
def enrich_signals_with_targets(signals, current_high, current_low, atr):
    """
    Compute Entry, SL, TP if signal is present
    """
    if signals['signal_type']:
        buffer = 1.0
        atr_mult_sl = 2.0
        rr = 1.5
        
        is_long = signals['signal_dir'] == 'LONG'
        
        # Entry
        entry = (current_high + buffer) if is_long else (current_low - buffer)
        
        # Risk
        risk = atr * atr_mult_sl if atr > 0 else (entry * 0.005) # Fallback 0.5% risk if ATR fails
        
        # SL & TP
        sl = (entry - risk) if is_long else (entry + risk)
        tp = (entry + risk * rr) if is_long else (entry - risk * rr)
        
        signals['entry'] = round(entry, 2)
        signals['sl'] = round(sl, 2)
        signals['tp'] = round(tp, 2)
        signals['risk'] = round(risk, 2)
        signals['atr'] = round(atr, 2)
        
    return signals


def scan_stock(symbol, timeframe="5m"):
    """
    Main function to scan a single stock for PACPL signals
    Returns: dict with stock name, price, and signal info
    """
    result = {
        'symbol': symbol,
        'name': symbol.replace('.NS', ''),
        'price': None,
        'signal_type': None,
        'signal_dir': None,
        'has_signal': False,
        'timeframe': timeframe,
        'error': None
    }
    
    try:
        # Fetch data
        df = get_stock_data(symbol, timeframe)
        
        if df is None or len(df) < 2:
            result['error'] = 'Insufficient data'
            return result
        
        # Calculate daily levels
        pdc, pdh, pdl = calculate_daily_levels(df)
        
        if pdc is None:
            result['error'] = 'Cannot calculate daily levels'
            return result
        
        # Calculate ORB
        orb_high, orb_low = calculate_orb(df)
        
        # Check signals
        signals = check_signals(df, pdc, pdh, pdl, orb_high, orb_low)
        
        # Merge all signal data including entry/sl/tp
        result.update(signals)

        # Check if any signal is active (already set in signals logic but good to double check or just rely on 'has_signal' logic if embedded)
        # Re-derive has_signal just in case signals dict flags are used
        has_signal = (signals['follow_long'] or signals['follow_short'] or 
                     signals['fade_long'] or signals['fade_short'] or
                     signals['pdh_retest_long'] or signals['pdl_retest_short'] or
                     signals.get('reversal_long', False) or signals.get('reversal_short', False) or
                     signals.get('trend_long', False) or signals.get('trend_short', False))
        
        result['has_signal'] = has_signal
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def scan_stock_dual_tf(symbol, timeframes):
    """
    Scan a stock on multiple timeframes
    Returns: dict with results for each timeframe
    """
    results = {
        'symbol': symbol,
        'name': symbol.replace('.NS', ''),
        'timeframes': {}
    }
    
    for tf in timeframes:
        # Get stock data
        df = get_stock_data(symbol, tf)
        
        level_high = None
        level_low = None
        
        if df is not None and len(df) >= 2:
            # Calculate ORB for levels
            orb_h, orb_l = calculate_orb(df)
            if orb_h is not None and orb_l is not None:
                level_high = orb_h
                level_low = orb_l
        
        tf_result = scan_stock(symbol, tf)
        
        # Merge scan results with calculated levels
        tf_data = tf_result.copy()
        tf_data['level_high'] = level_high
        tf_data['level_low'] = level_low
        
        results['timeframes'][tf] = tf_data
    
    # Check if any timeframe has a signal and pull top-level metadata
    has_any = False
    for tf_data in results['timeframes'].values():
        if tf_data.get('has_signal'):
            has_any = True
            # Propagate primary metadata to top level
            results['signal_type'] = tf_data.get('signal_type')
            results['signal_dir'] = tf_data.get('signal_dir')
            results['price'] = tf_data.get('price')
            results['entry'] = tf_data.get('entry')
            results['sl'] = tf_data.get('sl')
            results['tp'] = tf_data.get('tp')
            break
            
    results['has_any_signal'] = has_any
    
    return results



def scan_all_stocks(stock_list, timeframes=None):
    """
    Scan all stocks in the list on multiple timeframes using threading
    Returns: list of results for stocks with signals on any timeframe
    """
    if timeframes is None:
        timeframes = TIMEFRAMES
    
    results = []
    
    # Use ThreadPoolExecutor for parallel scanning
    # Adjust max_workers based on API limits and system capabilities
    # 20 workers is a safe starting point for yfinance
    import concurrent.futures
    
    print(f"Starting scan for {len(stock_list)} stocks on timeframes {timeframes}...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Create a dictionary to map futures to stock symbols
        future_to_stock = {
            executor.submit(scan_stock_dual_tf, symbol, timeframes): symbol 
            for symbol in stock_list
        }
        
        # Process completed futures
        for future in concurrent.futures.as_completed(future_to_stock):
            symbol = future_to_stock[future]
            try:
                result = future.result()
                # Only include stocks with active signals on any timeframe
                if result['has_any_signal']:
                    results.append(result)
            except Exception as exc:
                print(f'{symbol} generated an exception: {exc}')
                
    print(f"Scan complete. Found {len(results)} stocks with signals.")
    return results



def scan_stocks_generator(stock_list, timeframes=None):
    """
    Generator that yields progress and results in real-time
    Used for streaming responses to the frontend
    """
    if timeframes is None:
        timeframes = TIMEFRAMES
    
    import concurrent.futures
    import json
    import time
    
    total_stocks = len(stock_list)
    completed_count = 0
    
    print(f"DEBUG: Starting generator for {total_stocks} stocks")
    yield f"data: {json.dumps({'type': 'start', 'total': total_stocks})}\n\n"
    
    # Use ThreadPoolExecutor for parallel scanning
    # Increased workers to 30 to handle Nifty 500 efficiently
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        future_to_stock = {
            executor.submit(scan_stock_dual_tf, symbol, timeframes): symbol 
            for symbol in stock_list
        }
        
        print("DEBUG: All tasks submitted to executor")
        
        for future in concurrent.futures.as_completed(future_to_stock):
            symbol = future_to_stock[future]
            completed_count += 1
            
            try:
                result = future.result(timeout=10)
                # print(f"DEBUG: {symbol} completed")
                
                # Prepare progress update
                progress_data = {
                    'type': 'progress',
                    'scanned': completed_count,
                    'total': total_stocks,
                    'symbol': symbol
                }
                yield f"data: {json.dumps(progress_data)}\n\n"
                
                # If signal found, yield signal data immediately
                if result.get('has_any_signal', False):
                    print(f"DEBUG: SIGNAL FOUND in {symbol}")
                    signal_data = {
                        'type': 'signal',
                        'data': result
                    }
                    yield f"data: {json.dumps(signal_data)}\n\n"
                    
            except Exception as exc:
                print(f'{symbol} generated an exception: {exc}')
                # trace back
                import traceback
                traceback.print_exc()
    
    # Send completion event
    print("DEBUG: Generator finished")
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

