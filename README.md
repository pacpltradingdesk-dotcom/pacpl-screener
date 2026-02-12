# 🔁 PACPL Screener - Web Edition

A powerful web-based stock screener that can scan up to **30 NSE stocks** simultaneously using PACPL trading logic (Gap Analysis, ORB Breakouts, PDH/PDL Retests).

## 🎯 Features

- ✅ Scan **30 NSE stocks** simultaneously (no Pine Script limits!)
- ✅ Same PACPL logic from TradingView indicator
- ✅ Ravan-style professional dashboard
- ✅ Real-time signal detection
- ✅ Auto-refresh every 60 seconds
- ✅ Configurable stock list
- ✅ Color-coded signals
- ✅ Live time/timeframe display

## 📊 Signal Types

1. **CE 1st (Follow Long)** - Large gap up + ORB High breakout
2. **PE 1st (Follow Short)** - Large gap down + ORB Low breakdown
3. **CE 2nd (Fade Long)** - Small gap down + ORB High breakout
4. **PE 2nd (Fade Short)** - Small gap up + ORB Low breakdown
5. **CE 3rd (PDH Retest Long)** - Previous Day High retest
6. **PE 3rd (PDL Retest Short)** - Previous Day Low retest

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Navigate to the project directory:**
```powershell
cd C:\Users\USER\.gemini\antigravity\scratch\pacpl-screener-web
```

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Run the server:**
```powershell
python app.py
```

4. **Open your browser:**
```
http://localhost:5000
```

## ⚙️ Configuration

### Change Stocks

1. Click the **⚙️ Settings** button
2. Edit the stock list (one symbol per line, format: `SYMBOL.NS`)
3. Maximum 30 stocks allowed
4. Click **Save Changes**

### Default Stock List (30 Stocks)

```
RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ICICIBANK.NS,
HINDUNILVR.NS, SBIN.NS, BHARTIARTL.NS, KOTAKBANK.NS, ITC.NS,
LT.NS, AXISBANK.NS, BAJFINANCE.NS, ASIANPAINT.NS, MARUTI.NS,
HCLTECH.NS, WIPRO.NS, ULTRACEMCO.NS, TITAN.NS, SUNPHARMA.NS,
NESTLEIND.NS, POWERGRID.NS, NTPC.NS, TATAMOTORS.NS, ONGC.NS,
M&M.NS, TECHM.NS, BAJAJFINSV.NS, ADANIPORTS.NS, COALINDIA.NS
```

### PACPL Parameters

- **Large Gap:** 0.5%
- **Small Gap:** 0.25%
- **ORB Minutes:** 15 minutes
- **Sustain Minutes:** 10 minutes
- **Timeframe:** 5 minutes
- **Refresh Interval:** 60 seconds (configurable)

## 📱 Usage

1. **Dashboard View:** Shows all active signals in real-time
2. **Auto-Refresh:** Automatically scans stocks every 60 seconds
3. **Manual Refresh:** Click 🔄 Refresh to scan immediately
4. **Settings:** Configure stocks and refresh interval

## 🎨 Dashboard Features

- **Header:** Live time, timeframe, refresh and settings buttons
- **Stats Bar:** Total stocks, active signals, last update time, status
- **Signals Table:** Color-coded signals with stock name, signal type, direction, price
- **Auto-Refresh:** Configurable interval (30-300 seconds)

## ⚠️ Important Notes

### Data Source
- Uses **yfinance** (Yahoo Finance) for NSE data
- Data is delayed by ~15 minutes for NSE stocks
- For real-time data, consider paid APIs (Zerodha Kite, Upstox)

### Trading Hours
- Signals are generated only after 9:18 AM IST
- Dashboard works 24/7 but signals only during market hours

### Performance
- Scanning 30 stocks takes ~10-20 seconds
- Auto-refresh is set to 60 seconds by default
- You can adjust refresh interval in settings

## 🛠️ Troubleshooting

### Server won't start
```powershell
# Make sure you're in the correct directory
cd C:\Users\USER\.gemini\antigravity\scratch\pacpl-screener-web

# Check if dependencies are installed
pip install -r requirements.txt

# Try running with Python 3 explicitly
python3 app.py
```

### No signals showing
- Check if it's after 9:18 AM IST
- Verify stock symbols are correct (format: `SYMBOL.NS`)
- Check server console for errors
- Try manual refresh

### Browser can't connect
- Make sure the server is running
- Check if port 5000 is available
- Try accessing: http://127.0.0.1:5000

## 📂 Project Structure

```
pacpl-screener-web/
├── app.py              # Flask API server
├── screener_logic.py   # PACPL screening logic
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── static/
│   ├── index.html     # Dashboard UI
│   ├── style.css      # Styling
│   └── app.js         # Frontend logic
└── README.md          # This file
```

## 🔧 API Endpoints

- `GET /` - Dashboard page
- `GET /api/scan` - Scan all stocks
- `GET /api/stocks` - Get stock list
- `POST /api/stocks` - Update stock list
- `GET /api/config` - Get configuration

## 📝 License

This project is for personal use. PACPL logic is based on the TradingView indicator.

## 🤝 Support

For issues or questions, check the server console output for error messages.

---

**Made with 🔁 PACPL Logic | Web Edition v1.0**
