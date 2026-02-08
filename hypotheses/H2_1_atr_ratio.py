"""
HYPOTHESIS: ATR FAST-SLOW RATIO (ionone777's suggestion)
========================================================
Testing u/ionone777's method: ATR(10)/ATR(100)
> 1.2 = high relative volatility
< 0.8 = low relative volatility
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================================
# DATA LOADING
# ============================================================================

data = pd.read_csv("/content/drive/MyDrive/Video/data/xau_usd_1H.csv",
                   parse_dates=['Time'], index_col='Time')
data.index = pd.to_datetime(data.index)
data = data[data.index.year == 2024].copy()

print(f"Loaded: {data.index.min()} to {data.index.max()}")
print(f"Total candles: {len(data)}")

# ============================================================================
# ATR CALCULATIONS
# ============================================================================

def calculate_atr(df, period):
    """Calculate ATR using EMA"""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

data['atr_fast'] = calculate_atr(data, 10)
data['atr_slow'] = calculate_atr(data, 100)
data['atr_ratio'] = data['atr_fast'] / data['atr_slow']

print(f"\nATR Ratio stats:")
print(f"  Mean: {data['atr_ratio'].mean():.2f}")
print(f"  >1.2: {(data['atr_ratio'] > 1.2).sum()} candles ({(data['atr_ratio'] > 1.2).sum()/len(data)*100:.1f}%)")
print(f"  <0.8: {(data['atr_ratio'] < 0.8).sum()} candles ({(data['atr_ratio'] < 0.8).sum()/len(data)*100:.1f}%)")

# ============================================================================
# VISUALIZATION 1: TIMELINE
# ============================================================================

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

ax1.plot(data.index, data['Close'], color='black', linewidth=1, alpha=0.7)

# Highlight high vol zones
high_vol = data[data['atr_ratio'] > 1.2]
for idx in high_vol.index:
    ax1.axvspan(idx, idx + pd.Timedelta(hours=12), color='red', alpha=0.15)

ax1.set_ylabel('XAUUSD Price', fontweight='bold')
ax1.set_title('Price + High Volatility Zones (Ratio >1.2)', fontweight='bold')
ax1.grid(alpha=0.3)

# ATR Ratio
ax2.plot(data.index, data['atr_ratio'], color='blue', linewidth=1.5)
ax2.axhline(1.2, color='red', linestyle='--', linewidth=2, label='High (1.2)')
ax2.axhline(1.0, color='green', linestyle='--', linewidth=2, label='Neutral (1.0)')
ax2.axhline(0.8, color='orange', linestyle='--', linewidth=2, label='Low (0.8)')

ax2.fill_between(data.index, 1.2, 2.0, color='red', alpha=0.1)
ax2.fill_between(data.index, 0.8, 1.0, color='green', alpha=0.1)

ax2.set_xlabel('Date', fontweight='bold')
ax2.set_ylabel('ATR Ratio', fontweight='bold')
ax2.set_title("ionone777's ATR Fast/Slow (10/100)", fontweight='bold')
ax2.legend()
ax2.grid(alpha=0.3)
ax2.set_ylim(0.6, 1.6)

plt.tight_layout()
plt.savefig('/content/drive/MyDrive/Video/data/atr_ratio_timeline.png', dpi=150, bbox_inches='tight')
print("\n✓ Saved: atr_ratio_timeline.png")

# ============================================================================
# BACKTEST - FIXED VERSION
# ============================================================================

def backtest_fixed(df, method='ratio', verbose=True):
    """
    Cleaner backtest with proper P&L calculation
    """
    results = []
    
    for i in range(100, len(df) - 24):  # Start at 100 to have ATR data
        row = df.iloc[i]
        
        # Skip if ATR not ready
        if pd.isna(row['atr_ratio']):
            continue
        
        # Simple entry: bullish candle
        if row['Close'] <= row['Open']:
            continue
        
        entry_price = row['Close']
        
        # Determine stop and position size
        if method == 'ratio':
            ratio = row['atr_ratio']
            if ratio > 1.2:
                # High vol: smaller position, wider stop
                position_size = 0.5
                sl_distance = row['atr_fast'] * 2.0  # 2x fast ATR
            elif ratio < 0.9:
                # Low vol: full position, tighter stop
                position_size = 1.0
                sl_distance = row['atr_fast'] * 1.5
            else:
                # Medium vol
                position_size = 0.75
                sl_distance = row['atr_fast'] * 1.75
        else:
            # Fixed method
            position_size = 1.0
            sl_distance = row['atr_slow'] * 1.0  # 1x slow ATR
        
        sl_price = entry_price - sl_distance
        
        # Check next 24 hours
        future = df.iloc[i+1:i+25]
        
        # Did we hit stop?
        sl_hit = (future['Low'] <= sl_price).any()
        
        if sl_hit:
            # Loss = 1R (1x risk)
            pnl_r = -1.0
        else:
            # Win/Loss based on 24h close
            exit_price = future.iloc[-1]['Close']
            pnl_distance = exit_price - entry_price
            pnl_r = pnl_distance / sl_distance  # In R-multiples
        
        # Convert to dollar P&L (risk $100 per R)
        pnl_dollars = pnl_r * 100 * position_size
        
        results.append({
            'pnl_r': pnl_r,
            'pnl': pnl_dollars,
            'position_size': position_size,
            'ratio': row['atr_ratio'],
            'sl_distance': sl_distance,
            'outcome': 'win' if pnl_r > 0 else 'loss'
        })
    
    df_results = pd.DataFrame(results)
    
    if verbose and len(df_results) > 0:
        # Sanity checks
        print(f"\nTrades: {len(df_results)}")
        print(f"Avg P&L: ${df_results['pnl'].mean():.2f}")
        print(f"Avg R-multiple: {df_results['pnl_r'].mean():.2f}")
        print(f"Max win: ${df_results['pnl'].max():.2f} ({df_results['pnl_r'].max():.2f}R)")
        print(f"Max loss: ${df_results['pnl'].min():.2f} ({df_results['pnl_r'].min():.2f}R)")
        
        # Check for bugs
        if df_results['pnl'].abs().max() > 10000:
            print("⚠️ WARNING: Unrealistic P&L detected!")
        if df_results['pnl_r'].abs().max() > 50:
            print("⚠️ WARNING: Extreme R-multiples detected!")
    
    return df_results

print("\n" + "="*70)
print("BACKTEST: RATIO METHOD")
print("="*70)
trades_ratio = backtest_fixed(data, method='ratio')

print("\n" + "="*70)
print("BACKTEST: FIXED METHOD")
print("="*70)
trades_fixed = backtest_fixed(data, method='fixed')

# ============================================================================
# METRICS
# ============================================================================

def calculate_metrics(df, label):
    wins = df[df['outcome'] == 'win']
    losses = df[df['outcome'] == 'loss']
    
    win_rate = len(wins) / len(df) * 100 if len(df) > 0 else 0
    avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
    avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
    total_pnl = df['pnl'].sum()
    avg_r = df['pnl_r'].mean()
    
    print(f"\n{label}:")
    print(f"  Trades: {len(df)}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg Win: ${avg_win:.2f}")
    print(f"  Avg Loss: ${avg_loss:.2f}")
    print(f"  Avg R-multiple: {avg_r:.2f}")
    print(f"  Total P&L: ${total_pnl:.2f}")
    
    return {'win_rate': win_rate, 'total_pnl': total_pnl, 'avg_r': avg_r}

print("\n" + "="*70)
print("FINAL COMPARISON")
print("="*70)

metrics_ratio = calculate_metrics(trades_ratio, "RATIO METHOD (ionone777)")
metrics_fixed = calculate_metrics(trades_fixed, "FIXED METHOD")

# ============================================================================
# VISUALIZATION 2: EQUITY CURVES
# ============================================================================

fig, ax = plt.subplots(figsize=(12, 6))

trades_ratio['cumulative'] = trades_ratio['pnl'].cumsum()
trades_fixed['cumulative'] = trades_fixed['pnl'].cumsum()

ax.plot(trades_ratio['cumulative'].values, linewidth=2,
        label=f"Ratio Method - Final: ${trades_ratio['cumulative'].iloc[-1]:.0f}",
        color='blue')
ax.plot(trades_fixed['cumulative'].values, linewidth=2,
        label=f"Fixed Method - Final: ${trades_fixed['cumulative'].iloc[-1]:.0f}",
        color='red', alpha=0.7)

ax.axhline(0, color='black', linestyle='--', alpha=0.3)
ax.set_xlabel('Trade Number', fontweight='bold')
ax.set_ylabel('Cumulative P&L ($)', fontweight='bold')
ax.set_title('Equity Curve: Adaptive vs Fixed', fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('/content/drive/MyDrive/Video/data/atr_ratio_equity.png', dpi=150, bbox_inches='tight')
print("\n✓ Saved: atr_ratio_equity.png")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)

if metrics_ratio['total_pnl'] > metrics_fixed['total_pnl']:
    improvement = ((metrics_ratio['total_pnl'] - metrics_fixed['total_pnl']) / 
                   abs(metrics_fixed['total_pnl'])) * 100
    print(f"✓ Ratio method won by {improvement:.1f}%")
else:
    improvement = ((metrics_fixed['total_pnl'] - metrics_ratio['total_pnl']) / 
                   abs(metrics_ratio['total_pnl'])) * 100
    print(f"✗ Fixed method won by {improvement:.1f}%")

print("\nNote: Simple bullish candle entry. Results depend on entry logic.")
print("="*70)
