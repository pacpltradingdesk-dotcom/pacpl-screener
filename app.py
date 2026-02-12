"""
PACPL Screener - Flask REST API
Provides endpoints for scanning stocks and managing configuration
"""

from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context
from flask_cors import CORS
from datetime import datetime
import config
from screener_logic import scan_all_stocks, scan_stocks_generator
import license_manager

license_manager.init_licenses()

app = Flask(__name__, static_folder='static')
CORS(app)

# Global stock list (can be updated via API)
current_stocks = config.DEFAULT_STOCKS.copy()


@app.route('/')
def index():
    """Serve the main dashboard page"""
    return send_from_directory('static', 'index.html')


@app.route('/api/scan', methods=['GET'])
def scan():
    """
    Scan all configured stocks for PACPL signals
    Returns: JSON with active signals
    """
    key = request.args.get('license_key')
    device_id = request.args.get('device_id')
    valid, message = license_manager.validate_license(key, device_id)
    if not valid:
        return jsonify({'success': False, 'error': message}), 403

    try:
        # Scan all stocks
        results = scan_all_stocks(current_stocks)
        
        response = {
            'success': True,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_stocks': len(current_stocks),
            'signals_found': len(results),
            'signals': results
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """
    Get the current stock list
    """
    return jsonify({
        'success': True,
        'stocks': current_stocks
    })


@app.route('/api/stocks', methods=['POST'])
def update_stocks():
    """
    Update the stock list
    Expects: JSON with 'stocks' array
    """
    try:
        data = request.get_json()
        
        if 'stocks' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing stocks array'
            }), 400
        
        new_stocks = data['stocks']
        
        # Validate (max 30 stocks)
        if len(new_stocks) > 30:
            return jsonify({
                'success': False,
                'error': 'Maximum 30 stocks allowed'
            }), 400
        
        # Update global stock list
        global current_stocks
        current_stocks = new_stocks
        
        return jsonify({
            'success': True,
            'stocks': current_stocks
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scan/mock', methods=['GET'])
def scan_mock():
    """
    Return mock data for UI testing with CE/PE signals
    """
    import random
    
    # Mock stock data with CE/PE signals
    mock_signals = [
        # CE (Call) signals
        {
            'name': 'RELIANCE',
            'timeframes': {
                '1m': {
                    'has_signal': True,
                    'signal_dir': 'LONG',
                    'signal_type': 'Follow',
                    'price': 2456.75,
                    'level_high': 2470.20,
                    'level_low': 2440.50,
                    'distance': 0.67
                }
            }
        },
        {
            'name': 'TCS',
            'timeframes': {
                '2m': {
                    'has_signal': True,
                    'signal_dir': 'LONG',
                    'signal_type': 'Fade',
                    'price': 3842.30,
                    'level_high': 3855.80,
                    'level_low': 3825.60,
                    'distance': 0.44
                }
            }
        },
        {
            'name': 'INFY',
            'timeframes': {
                '1m': {
                    'has_signal': True,
                    'signal_dir': 'LONG',
                    'signal_type': 'PDH_Retest',
                    'price': 1678.90,
                    'level_high': 1688.25,
                    'level_low': 1665.40,
                    'distance': 0.81
                }
            }
        },
        {
            'name': 'HDFCBANK',
            'timeframes': {
                '1m': {
                    'has_signal': True,
                    'signal_dir': 'LONG',
                    'signal_type': 'Follow',
                    'price': 1542.15,
                    'level_high': 1548.90,
                    'level_low': 1535.20,
                    'distance': 0.45
                }
            }
        },
        {
            'name': 'ICICIBANK',
            'timeframes': {
                '2m': {
                    'has_signal': True,
                    'signal_dir': 'LONG',
                    'signal_type': 'Fade',
                    'price': 892.60,
                    'level_high': 898.30,
                    'level_low': 885.40,
                    'distance': 0.81
                }
            }
        },
        # PE (Put) signals
        {
            'name': 'TATAMOTORS',
            'timeframes': {
                '1m': {
                    'has_signal': True,
                    'signal_dir': 'SHORT',
                    'signal_type': 'Follow',
                    'price': 678.40,
                    'level_high': 685.90,
                    'level_low': 672.20,
                    'distance': 0.92
                }
            }
        },
        {
            'name': 'WIPRO',
            'timeframes': {
                '2m': {
                    'has_signal': True,
                    'signal_dir': 'SHORT',
                    'signal_type': 'Fade',
                    'price': 456.20,
                    'level_high': 462.80,
                    'level_low': 451.60,
                    'distance': 1.02
                }
            }
        },
        {
            'name': 'MARUTI',
            'timeframes': {
                '1m': {
                    'has_signal': True,
                    'signal_dir': 'SHORT',
                    'signal_type': 'PDL_Retest',
                    'price': 12345.60,
                    'level_high': 12398.40,
                    'level_low': 12315.80,
                    'distance': 0.24
                }
            }
        },
        {
            'name': 'AXISBANK',
            'timeframes': {
                '1m': {
                    'has_signal': True,
                    'signal_dir': 'SHORT',
                    'signal_type': 'Follow',
                    'price': 1024.35,
                    'level_high': 1032.90,
                    'level_low': 1018.70,
                    'distance': 0.56
                }
            }
        },
        {
            'name': 'BAJFINANCE',
            'timeframes': {
                '2m': {
                    'has_signal': True,
                    'signal_dir': 'SHORT',
                    'signal_type': 'Fade',
                    'price': 6789.25,
                    'level_high': 6845.60,
                    'level_low': 6755.30,
                    'distance': 0.50
                }
            }
        }
    ]
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_stocks': 473,
        'signals_found': len(mock_signals),
        'signals': mock_signals
    })



@app.route('/api/license/validate', methods=['POST'])
def validate_license_route():
    data = request.get_json()
    key = data.get('key')
    device_id = data.get('device_id')
    valid, message = license_manager.validate_license(key, device_id)
    return jsonify({'success': valid, 'message': message})

@app.route('/api/admin/generate', methods=['POST'])
def generate_license_route():
    # Simple admin protection (you can change this password)
    admin_pass = request.headers.get('Admin-Password')
    if admin_pass != "PACPL-ADMIN-99":
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
    data = request.get_json()
    user_name = data.get('username', 'Customer')
    days = data.get('days', 30)
    
    key, expiry = license_manager.generate_key(user_name, days)
    return jsonify({'success': True, 'key': key, 'expiry': expiry})

@app.route('/api/admin/list', methods=['GET'])
def list_licenses_route():
    admin_pass = request.headers.get('Admin-Password')
    if admin_pass != "PACPL-ADMIN-99":
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    return jsonify({'success': True, 'licenses': license_manager.load_licenses()})
def get_config():
    """
    Get PACPL configuration parameters
    """
    return jsonify({
        'success': True,
        'config': {
            'large_gap': config.LARGE_GAP,
            'small_gap': config.SMALL_GAP,
            'sustain_mins': config.SUSTAIN_MINS,
            'orb_mins': config.ORB_MINS,
            'tol_pct': config.TOL_PCT,
            'timeframes': config.TIMEFRAMES,
            'refresh_interval': config.REFRESH_INTERVAL
        }
    })


@app.route('/api/scan/stream')
def scan_stream():
    """
    Stream scan results using Server-Sent Events (SSE)
    """
    key = request.args.get('license_key')
    device_id = request.args.get('device_id')
    valid, message = license_manager.validate_license(key, device_id)
    if not valid:
        return jsonify({'success': False, 'error': message}), 403

    timeframes = config.TIMEFRAMES
    
    def generate():
        # Use the generator function
        # Using current_stocks list
        # Yielding events as formatted SSE
        for event in scan_stocks_generator(current_stocks, timeframes):
            yield event
            
    resp = Response(stream_with_context(generate()), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp



@app.route('/api/test/stream')
def test_stream_route():
    def generate():
        print("DEBUG: test_stream_route generator started")
        yield ": start\n\n"
        for i in range(10):
            import time
            time.sleep(1)
            yield f"data: {i}\n\n"
    
    resp = Response(stream_with_context(generate()), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['X-Accel-Buffering'] = 'no'
    return resp



if __name__ == '__main__':
    print("\n" + "="*60)
    print("PACPL SCREENER - DUAL TIMEFRAME (1m & 3m)")
    print("="*60)
    print(f"Scanning {len(current_stocks)} stocks")
    print(f"Timeframes: {', '.join(config.TIMEFRAMES)}")
    print(f"Dashboard: http://localhost:{config.PORT}")
    print("="*60 + "\n")
    
    # Ensure threading is enabled
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)

