# Configuration settings for PACPL Screener

# Indicator Name
INDICATOR_NAME = "🔁 PACPL – Stocks Level Pro 1.0"

# Import Nifty 500 and F&O stocks
from nifty500_stocks import get_nifty_500_list, get_nifty_50_list
from fno_stocks import get_fno_list

# Default stock list - Use F&O Stocks (approx 180) for better focus
DEFAULT_STOCKS = get_fno_list()

# PACPL Parameters (adjusted for easier detection)
LARGE_GAP = 0.5          # Default
SMALL_GAP = 0.25         # Default
SUSTAIN_MINS = 10        # Sustain Minutes (FOLLOW)
ORB_MINS = 15            # Opening Range Minutes
TOL_PCT = 0.05           # PDH/PDL Retest Tolerance %
RETEST_LOOK = 12         # PDH/PDL Retest Lookback (bars)

# Dual Timeframe settings
TIMEFRAMES = ["1m", "2m"]  # 1-minute and 2-minute timeframes (Yahoo Finance compatible)
REFRESH_INTERVAL = 600      # Refresh every 10 minutes (600 seconds)

# Trading session time (IST)
SESSION_START = "09:15"
SESSION_END = "15:30"
AFTER_918_MINS = 558     # 9:18 AM in minutes (9*60 + 18)

# Server settings
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True
