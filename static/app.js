// SMC Ink Scanner - Simplified JavaScript

let currentTab = 'ce'; // 'ce' (Call) or 'pe' (Put)
let currentTimeframe = '1m'; // Default to 1 minute
let autoRefreshTimer = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 SMC Ink Scanner initialized');
    setupEventListeners();
    startLiveClock();
    checkLicense(); // Added license check
});

function setupEventListeners() {
    // Tab buttons
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            tabs.forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentTab = e.target.dataset.tab;
            renderSignals(window.lastSignalsData || []);
        });
    });

    // Timeframe select
    const timeframeSelect = document.getElementById('timeframeSelect');
    if (timeframeSelect) {
        timeframeSelect.addEventListener('change', (e) => {
            currentTimeframe = e.target.value;
            performScan();
        });
    }

    // Scan button
    const scanBtn = document.getElementById('scanBtn');
    if (scanBtn) {
        scanBtn.addEventListener('click', () => {
            console.log('🔘 Search button clicked');
            performScan();
        });
    }

    // Nifty 500 button
    const niftyBtn = document.querySelector('.btn-nifty');
    if (niftyBtn) {
        niftyBtn.addEventListener('click', () => {
            console.log('🔘 Nifty 500 button clicked');
            performScan();
        });
        console.log('✅ Nifty 500 button found and listener attached');
    } else {
        console.error('❌ Nifty 500 button NOT found');
    }

    // Test Mock button
    const testMockBtn = document.getElementById('testMockBtn');
    if (testMockBtn) {
        testMockBtn.addEventListener('click', () => {
            console.log('🔘 Test Mock button clicked');
            loadMockData();
        });
    }

    // Activate License Button
    const activateBtn = document.getElementById('activateBtn');
    if (activateBtn) {
        activateBtn.addEventListener('click', () => {
            const key = document.getElementById('licenseKeyInput').value.trim();
            if (!key) return;
            validateLicense(key);
        });
    }
}

function startLiveClock() {
    updateClock();
    setInterval(updateClock, 1000);
}

function updateClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timeStr = `${hours}:${minutes}:${seconds}`;

    const lastScannedEl = document.getElementById('lastScanned');
    if (lastScannedEl && lastScannedEl.textContent === '09:30:27') {
        // Only update once scanned
    }

    const footerTimeEl = document.getElementById('footerTime');
    if (footerTimeEl && window.lastScanTime) {
        footerTimeEl.textContent = window.lastScanTime;
    }
}

// Helper to get/create unique device ID
function getDeviceId() {
    let id = localStorage.getItem('pacpl_device_id');
    if (!id) {
        id = 'DEV-' + Math.random().toString(36).substr(2, 9).toUpperCase();
        localStorage.setItem('pacpl_device_id', id);
    }
    return id;
}

async function checkLicense() {
    const key = localStorage.getItem('pacpl_license_key');
    const device_id = getDeviceId();
    if (!key) {
        document.getElementById('licenseOverlay').style.display = 'flex';
        return;
    }

    try {
        const response = await fetch('/api/license/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, device_id })
        });
        const result = await response.json();

        if (result.success) {
            document.getElementById('licenseOverlay').style.display = 'none';
            performScan();
            startAutoRefresh();
        } else {
            localStorage.removeItem('pacpl_license_key');
            document.getElementById('licenseOverlay').style.display = 'flex';
            document.getElementById('licenseError').textContent = 'Session Expired or Invalid Key';
        }
    } catch (err) {
        console.error('License check failed:', err);
    }
}

async function validateLicense(key) {
    const btn = document.getElementById('activateBtn');
    const errorEl = document.getElementById('licenseError');
    const device_id = getDeviceId();
    btn.textContent = 'Validating...';
    errorEl.textContent = '';

    try {
        const response = await fetch('/api/license/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, device_id })
        });
        const result = await response.json();

        if (result.success) {
            localStorage.setItem('pacpl_license_key', key);
            document.getElementById('licenseOverlay').style.display = 'none';
            performScan();
            startAutoRefresh();
        } else {
            errorEl.textContent = result.message || 'Activation Failed';
        }
    } catch (err) {
        errorEl.textContent = 'Server Error. Please try again.';
    } finally {
        btn.textContent = 'Activate Access';
    }
}

async function performScan() {
    console.log('🔍 Streaming scan results...');

    // UI Elements
    const scanBtn = document.getElementById('scanBtn');
    const niftyBtn = document.querySelector('.btn-nifty');
    const detectedEl = document.getElementById('detectedSignals');
    const totalScannedEl = document.getElementById('totalScanned');
    const container = document.getElementById('signalsContainer');
    const lastScannedEl = document.getElementById('lastScanned');
    const footerTimeEl = document.getElementById('footerTime');

    // Reset state
    let signalsFound = 0;
    let stocksScanned = 0;

    // Disable buttons
    if (scanBtn) scanBtn.disabled = true;
    if (niftyBtn) {
        niftyBtn.disabled = true;
        niftyBtn.textContent = 'Scanning...';
    }

    // Show scanning message
    if (detectedEl) detectedEl.textContent = '0';
    if (totalScannedEl) totalScannedEl.textContent = '0';

    container.innerHTML = `
        <div class="no-signals" id="scanning-msg">
            <div class="no-signals-icon">⏳</div>
            <h3>Scanning Nifty Stocks...</h3>
            <p>Processing: <span id="scan-progress">0</span> completed</p>
        </div>
    `;

    // Start EventSource with license key and device id
    const licenseKey = localStorage.getItem('pacpl_license_key');
    const deviceId = getDeviceId();
    const url = `/api/scan/stream?timeframe=${currentTimeframe}&t=${Date.now()}&license_key=${licenseKey || ''}&device_id=${deviceId}`;
    const eventSource = new EventSource(url);

    // Used to remove the "Scanning..." message once first signal arrives
    let firstSignal = true;

    eventSource.onmessage = function (event) {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
            // Update counts
            stocksScanned = data.scanned;
            if (totalScannedEl) totalScannedEl.textContent = stocksScanned;

            // Update progress text
            const progressEl = document.getElementById('scan-progress');
            if (progressEl) progressEl.textContent = `${stocksScanned}/${data.total}`;

        } else if (data.type === 'signal') {
            const stock = data.data;

            // Derive direction from timeframes (same logic as createSignalCard)
            let signalDir = 'LONG';
            if (stock.timeframes) {
                const primaryTF = Object.values(stock.timeframes).find(tf => tf.has_signal);
                if (primaryTF && primaryTF.signal_dir) {
                    signalDir = primaryTF.signal_dir;
                }
            }

            // Only show if matches current tab
            const isCEMatch = currentTab === 'ce' && signalDir === 'LONG';
            const isPEMatch = currentTab === 'pe' && signalDir === 'SHORT';

            if (isCEMatch || isPEMatch) {
                // New signal found (that matches current view)!
                signalsFound++;
                if (detectedEl) detectedEl.textContent = signalsFound;

                // Remove scanning placeholder if it's the first signal
                if (firstSignal) {
                    const scanningMsg = document.getElementById('scanning-msg');
                    if (scanningMsg) scanningMsg.remove();

                    // Create grid wrapper if not exists
                    if (!document.querySelector('.signals-grid')) {
                        const gridDiv = document.createElement('div');
                        gridDiv.className = 'signals-grid';
                        gridDiv.id = 'live-signals-grid';
                        container.appendChild(gridDiv);
                    }
                    firstSignal = false;
                }

                // Get grid container
                const grid = document.querySelector('.signals-grid') || container;

                // Render card with NEW tag
                const cardHTML = createSignalCard(stock, true);
                grid.insertAdjacentHTML('afterbegin', cardHTML); // Add to TOP
            }

            // Always store for tab switching re-render
            if (!window.lastSignalsData) window.lastSignalsData = [];
            // Remove old entry for same stock if exists to update it?
            window.lastSignalsData = window.lastSignalsData.filter(s => s.name !== stock.name);
            window.lastSignalsData.push(stock);

        } else if (data.type === 'done') {
            // Scan complete
            eventSource.close();
            finalizeScan();
        }
    };

    eventSource.onerror = function (err) {
        console.error("EventSource failed:", err);
        eventSource.close();
        if (stocksScanned === 0) {
            container.innerHTML = `
                <div class="no-signals">
                    <div class="no-signals-icon">❌</div>
                    <h3>Scan Connection Failed</h3>
                    <p>Please try again.</p>
                </div>
            `;
        }
        finalizeScan();
    };

    function finalizeScan() {
        // Re-enable buttons
        if (scanBtn) scanBtn.disabled = false;
        if (niftyBtn) {
            niftyBtn.disabled = false;
            niftyBtn.textContent = 'Scan Nifty 500';
        }

        // Update timestamps
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        window.lastScanTime = timeStr;

        if (lastScannedEl) lastScannedEl.textContent = timeStr;
        if (footerTimeEl) footerTimeEl.textContent = timeStr;

        // If no signals found after completion
        if (signalsFound === 0) {
            container.innerHTML = `
                <div class="no-signals">
                    <div class="no-signals-icon">📪</div>
                    <h3>No Active Signals</h3>
                    <p>Scanned ${stocksScanned} stocks. Try again later.</p>
                </div>
            `;
        }
        console.log(`✅ Scan complete! Found ${signalsFound} signals`);
    }
}

async function loadMockData() {
    console.log('🎭 Loading mock data...');

    // Update UI to scanning state
    const detectedEl = document.getElementById('detectedSignals');
    if (detectedEl) {
        detectedEl.textContent = '...';
    }

    try {
        const response = await fetch('/api/scan/mock');
        const data = await response.json();

        if (data.success) {
            updateDashboard(data);
            renderSignals(data.signals);
            window.lastSignalsData = data.signals;

            // Update last scan time
            const now = new Date();
            const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
            window.lastScanTime = timeStr;

            const lastScannedEl = document.getElementById('lastScanned');
            if (lastScannedEl) {
                lastScannedEl.textContent = timeStr;
            }

            const footerTimeEl = document.getElementById('footerTime');
            if (footerTimeEl) {
                footerTimeEl.textContent = timeStr;
            }

            console.log('✅ Mock data loaded successfully!');
        }
    } catch (error) {
        console.error('Error loading mock data:', error);
    }
}

function updateDashboard(data) {
    // Update total scanned
    const totalEl = document.getElementById('totalScanned');
    if (totalEl) {
        totalEl.textContent = data.total_stocks || 501;
    }

    // Update detected signals
    const detectedEl = document.getElementById('detectedSignals');
    if (detectedEl) {
        detectedEl.textContent = data.signals_found || 0;
    }
}

function renderSignals(signals) {
    const container = document.getElementById('signalsContainer');

    if (!signals || signals.length === 0) {
        container.innerHTML = `
            <div class="no-signals">
                <div class="no-signals-icon">📭</div>
                <h3>No Active Signals</h3>
                <p>Click "Scan Nifty 500" to start scanning...</p>
            </div>
        `;
        return;
    }

    // Filter by current tab (ce/pe)
    let filteredSignals = signals.filter(stock => {
        if (!stock.timeframes) return false;

        // Check if any timeframe has a signal
        const hasSignal = Object.values(stock.timeframes).some(tf => tf.has_signal);
        if (!hasSignal) return false;

        // Get primary signal
        const primaryTF = Object.values(stock.timeframes).find(tf => tf.has_signal);
        if (!primaryTF) return false;

        // Filter by CE (LONG) / PE (SHORT)
        if (currentTab === 'ce') {
            return primaryTF.signal_dir === 'LONG';
        } else {
            return primaryTF.signal_dir === 'SHORT';
        }
    });

    if (filteredSignals.length === 0) {
        container.innerHTML = `
            <div class="no-signals">
                <div class="no-signals-icon">📭</div>
                <h3>No ${currentTab === 'ce' ? 'CE (Call)' : 'PE (Put)'} Signals</h3>
                <p>Try switching tabs or scanning again...</p>
            </div>
        `;
        return;
    }

    // Render cards
    container.innerHTML = `
        <div class="signals-grid">
            ${filteredSignals.map(stock => createSignalCard(stock)).join('')}
        </div>
    `;
}

function createSignalCard(stock, isNew = false) {
    // Get primary signal from any timeframe
    const primaryTF = Object.values(stock.timeframes).find(tf => tf.has_signal);
    if (!primaryTF) return '';

    const price = primaryTF.price || 0;
    const signalDir = primaryTF.signal_dir || 'LONG';
    const isCE = signalDir === 'LONG';

    // Simple CE or PE label
    const conditionLabel = isCE ? 'CE' : 'PE';

    // Get level zone
    const levelHigh = primaryTF.level_high || (price * 1.02);
    const levelLow = primaryTF.level_low || (price * 0.98);
    const distance = ((Math.abs(price - (isCE ? levelLow : levelHigh)) / price) * 100).toFixed(2);

    return `
        <div class="signal-card ${isCE ? 'bullish' : 'bearish'}">
            ${isNew ? '<span class="new-tag">NEW</span>' : ''}
            <div class="card-badge ${isCE ? 'bullish' : 'bearish'}">
                ${conditionLabel}
            </div>
            <div class="stock-symbol">${stock.name}</div>
            <div class="card-timeframe">TIMEFRAME: ${currentTimeframe.toUpperCase()}</div>
            
            <div class="card-info">
                <div class="info-row">
                    <span class="info-label">Signal</span>
                    <span class="info-value" style="color: ${isCE ? 'var(--green)' : 'var(--red)'}; font-weight: 700;">${isCE ? 'CE' : 'PE'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Live Price</span>
                    <span class="info-value price">₹${price.toFixed(2)}</span>
                </div>
            </div>
            
            <button class="btn-chart" onclick="window.open('https://www.tradingview.com/chart/?symbol=NSE:${stock.name}', '_blank')">
                VIEW CHART
            </button>
        </div>
    `;
}

function startAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
    }

    const autoScan = document.getElementById('autoScan');
    if (autoScan && autoScan.checked) {
        autoRefreshTimer = setInterval(() => {
            performScan();
        }, 600000); // 10 minutes (600000 ms)
    }
}

// Auto scan toggle
document.addEventListener('DOMContentLoaded', () => {
    const autoScan = document.getElementById('autoScan');
    if (autoScan) {
        autoScan.addEventListener('change', () => {
            startAutoRefresh();
        });
    }
});

// Clean up on unload
window.addEventListener('beforeunload', () => {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
    }
});
