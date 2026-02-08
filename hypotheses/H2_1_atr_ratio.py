"""
HYPOTHESIS: ATR FAST-SLOW RATIO
===============================
Based on u/ionone777's suggestion:
"Fast ATR / Slow ATR gives normalized values around 1.0
> 1.2 = high relative volatility (more stop-outs)
< 1.0 = low relative volatility (safer to trade)"

TEST:
1. Compare ATR(14)/ATR(50) vs absolute ATR(24)
2. Backtest with ratio-based risk management
3. Visualize when ratio >1.2 warned before stop-out clusters

GOAL: Show if relative > absolute volatility
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_PATH = "data/xau_usd_1H.csv"  # Change this to your data file
OUTPUT_DIR = "output"
YEAR = 2024

# Create output directory if it doesn't exist
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# ============================================================================
# DATA LOADING
# ============================================================================

try:
    data = pd.read_csv(DATA_PATH, parse_dates=['Time'], index_col='Time')
    data.index = pd.to_datetime(data.index)
    data = data[data.index.year == YEAR].copy()
    print(f"Loaded {YEAR} data: {data.index.min()} to {data.index.max()}")
except FileNotFoundError:
    print(f"ERROR: File not found at {DATA_PATH}")
    print("Please place your CSV in the data/ directory")
    exit(1)

# ============================================================================
# ATR CALCULATIONS
# ============================================================================

def calculate_atr(df, period):
    """Calculate Average True Range using Exponential Moving Average"""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.ewm(span=period, adjust=False).mean()
    return atr

data['atr_fast'] = calculate_atr(data, 14)
data['atr_slow'] = calculate_atr(data, 50)
data['atr_24'] = calculate_atr(data, 24)
data['atr_ratio'] = data['atr_fast'] / data['atr_slow']

# ============================================================================
# VISUALIZATION 1: RATIO TIMELINE
# ============================================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

# Price with volatility zones
ax1.plot(data.index, data['Close'], color='black', linewidth=1, alpha=0.7)

high_vol = data[data['atr_ratio'] > 1.2]
for idx in high_vol.index:
    ax1.axvspan(idx, idx + pd.Timedelta(hours=12), color='red', alpha=0.15)

ax1.set_ylabel('XAUUSD Price', fontweight='bold')
ax1.set_title('Price Action + High Volatility Zones (ATR Ratio > 1.2)', 
              fontweight='bold', fontsize=13)
ax1.grid(alpha=0.3)

# ATR Ratio
ax2.plot(data.index, data['atr_ratio'], color='blue', linewidth=1.5,
         label='ATR Fast/Slow Ratio')
ax2.axhline(1.2, color='red', linestyle='--', linewidth=2, label='High Vol (1.2)')
ax2.axhline(1.0, color='green', linestyle='--', linewidth=2, label='Neutral (1.0)')
ax2.axhline(0.8, color='orange', linestyle='--', linewidth=2, label='Low Vol (0.8)')

ax2.fill_between(data.index, 1.2, 2.0, color='red', alpha=0.1, label='Danger Zone')
ax2.fill_between(data.index, 0.8, 1.0, color='green', alpha=0.1, label='Safe Zone')

ax2.set_xlabel('Date', fontweight='bold')
ax2.set_ylabel('ATR Ratio (Fast/Slow)', fontweight='bold')
ax2.set_title("ATR Fast-Slow Indicator", fontweight='bold', fontsize=13)
ax2.legend(loc='upper right')
ax2.grid(alpha=0.3)
ax2.set_ylim(0.6, 1.6)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/atr_ratio_timeline.png', dpi=150, bbox_inches='tight')
print(f"Saved: {OUTPUT_DIR}/atr_ratio_timeline.png")

# ============================================================================
# BACKTEST
# ============================================================================

def backtest_with_regime(df, method='ratio'):
    """
    method='ratio': Adjust position size based on ATR ratio
    method='fixed': Same position size always
    """
    results = []
    base_risk = 100  # Base risk per trade in USD
    
    for i in range(len(df) - 24):
        row = df.iloc[i]
        
        # Simple entry: bullish candle
        if row['Close'] <= row['Open']:
            continue
            
        entry_price = row['Close']
        
        if method == 'ratio':
            ratio = row['atr_ratio']
            if ratio > 1.2:
                position_size = 0.5
                sl_pips = 50
            elif ratio < 0.9:
                position_size = 1.0
                sl_pips = 20
            else:
                position_size = 0.75
                sl_pips = 30
        else:
            position_size = 1.0
            sl_pips = 25
            
        sl_price = entry_price - (sl_pips * 0.0001)
        future = df.iloc[i+1:i+25]
        sl_hit = (future['Low'] <= sl_price).any()
        
        if sl_hit:
            pnl = -base_risk * position_size
            outcome = 'loss'
        else:
            exit_price = future.iloc[-1]['Close']
            pnl_pips = (exit_price - entry_price) / 0.0001
            pnl = (pnl_pips / sl_pips) * base_risk * position_size
            outcome = 'win' if pnl > 0 else 'loss'
            
        results.append({
            'pnl': pnl,
            'outcome': outcome,
            'position_size': position_size,
            'ratio': row['atr_ratio']
        })
        
    return pd.DataFrame(results)

trades_ratio = backtest_with_regime(data, method='ratio')
trades_fixed = backtest_with_regime(data, method='fixed')

# ============================================================================
# METRICS
# ============================================================================

def calculate_metrics(trades_df, label):
    wins = trades_df[trades_df['outcome'] == 'win']
    losses = trades_df[trades_df['outcome'] == 'loss']
    
    win_rate = len(wins) / len(trades_df) * 100
    avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
    avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    total_pnl = trades_df['pnl'].sum()
    
    print(f"\n{label}:")
    print(f"  Trades: {len(trades_df)}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Profit Factor: {profit_factor:.2f}")
    print(f"  Total P&L: ${total_pnl:.2f}")
    
    return {'win_rate': win_rate, 'total_pnl': total_pnl, 'profit_factor': profit_factor}

print("\n" + "="*70)
print("BACKTEST COMPARISON")
print("="*70)

metrics_ratio = calculate_metrics(trades_ratio, "ATR RATIO METHOD")
metrics_fixed = calculate_metrics(trades_fixed, "FIXED STOP METHOD")

# ============================================================================
# VISUALIZATION 2: EQUITY CURVES
# ============================================================================

fig, ax = plt.subplots(figsize=(12, 6))

trades_ratio['cumulative'] = trades_ratio['pnl'].cumsum()
trades_fixed['cumulative'] = trades_fixed['pnl'].cumsum()

ax.plot(trades_ratio['cumulative'].values, linewidth=2,
        label=f"ATR Ratio - Final: ${trades_ratio['cumulative'].iloc[-1]:.0f}",
        color='blue')
ax.plot(trades_fixed['cumulative'].values, linewidth=2,
        label=f"Fixed 25-pip - Final: ${trades_fixed['cumulative'].iloc[-1]:.0f}",
        color='red', alpha=0.7)

ax.axhline(0, color='black', linestyle='--', alpha=0.3)
ax.set_xlabel('Trade Number', fontweight='bold')
ax.set_ylabel('Cumulative P&L ($)', fontweight='bold')
ax.set_title('Equity Curve: Adaptive vs Fixed Stop-Loss', 
             fontweight='bold', fontsize=13)
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/atr_ratio_equity.png', dpi=150, bbox_inches='tight')
print(f"\nSaved: {OUTPUT_DIR}/atr_ratio_equity.png")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)

improvement = ((metrics_ratio['total_pnl'] - metrics_fixed['total_pnl']) / 
               abs(metrics_fixed['total_pnl'])) * 100

print(f"Ratio method vs Fixed: {improvement:+.1f}%")

if improvement > 10:
    print("Ratio method outperformed")
elif improvement < -10:
    print("Fixed method outperformed")
else:
    print("Similar performance")

print("="*70)
