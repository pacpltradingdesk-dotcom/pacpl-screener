
import sys
import os
from datetime import datetime
import pandas as pd
import yfinance as yf

# Mock config so we can run without importing everything
TIMEFRAMES = ["1m"]
LARGE_GAP = 0.3
SMALL_GAP = 0.15
SUSTAIN_MINS = 10
ORB_MINS = 15
TOL_PCT = 0.05

# Use explicit sys.path if needed
sys.path.append(os.getcwd())

from screener_logic import scan_stock, get_stock_data, calculate_daily_levels

if __name__ == "__main__":
    print(f"Testing scanner logic at {datetime.now()}")
    
    test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
    
    for symbol in test_symbols:
        print(f"\n--- Testing {symbol} ---")
        
        # Test 1: Fetch Data
        try:
            df = get_stock_data(symbol, timeframe="1m")
            if df is None:
                print("FAILURE: df is None")
                continue
            if df.empty:
                print("FAILURE: df is empty")
                continue
                
            print(f"Data fetched: {len(df)} rows")
            print(df.tail(3))
            
            # Test 2: Calculate Levels
            pdc, pdh, pdl = calculate_daily_levels(df)
            print(f"Levels: PDC={pdc}, PDH={pdh}, PDL={pdl}")
            
            if pdc is None:
                print("FAILURE: Could not calculate daily levels")
                continue
                
            # Test 3: Full Scan Logic
            result = scan_stock(symbol, "1m")
            print("Scan Result:", result)
            
        except Exception as e:
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

