"""
HYPOTHESIS 4.1: BETTER MEAN REVERSION ENTRY SIGNAL
===================================================
Root cause:
  BB-bounce signal with ffill creates "always active" pseudo-signal.
  It measures market direction, not actual bounce entries.

Proper MR entry needs:
  1. A clear ENTRY event (price crosses into band)
  2. A defined EXIT (return to middle band or fixed time)
  3. No ffill — only hold position during specific trade window

Hypothesis:
  Replacing the ffill BB signal with PROPER trade logic:

  Entry: Price touches/crosses BB outer band
  Exit options to test:
    A) Price returns to BB middle (MA20)
    B) Fixed bars (4h, 8h, 16h, 24h)
    C) Stop: price moves further N×ATR against position

  This is a TRADE-BASED backtest, not a bar-by-bar signal.
  Compare to: proper momentum breakout (same methodology).

  The question: Is there actually a tradeable MR edge when
  measured correctly?

Reddit hook:
  "I was measuring my strategy wrong for 3 hypotheses.
   Here's what proper trade-based testing actually shows."
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from ta.trend import ADXIndicator
from ta.volatility import AverageTrueRange, BollingerBands

# ============================================================================
# LOAD + INDICATORS
# ============================================================================

# UPDATE THIS PATH ↓↓↓
DATA_PATH = "data/us500_1H.csv"

df = pd.read_csv(DATA_PATH, parse_dates=['Time'], index_col='Time')

print("=" * 70)
print("HYPOTHESIS 4.1: PROPER TRADE-BASED MR SIGNAL")
print("=" * 70)
print(f"Data: {len(df)} bars ({df.index[0].date()} to {df.index[-1].date()})")

adx_i = ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
df['ADX'] = adx_i.adx()
atr_i = AverageTrueRange(df['High'], df['Low'], df['Close'], window=14)
df['ATR'] = atr_i.average_true_range()
df['ATR_SMA'] = df['ATR'].rolling(100).mean()
df['ATR_Ratio'] = df['ATR'] / df['ATR_SMA']

bb = BollingerBands(df['Close'], window=20, window_dev=2)
df['BB_Upper'] = bb.bollinger_hband()
df['BB_Lower'] = bb.bollinger_lband()
df['BB_Middle'] = bb.bollinger_mavg()
df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

df = df.dropna()
df['Returns'] = df['Close'].pct_change()


def classify_regime(row):
    adx, atr_ratio = row['ADX'], row['ATR_Ratio']
    if adx > 25 and atr_ratio >= 0.9:
        return 'TRENDING'
    elif adx < 20 and atr_ratio <= 1.1:
        return 'RANGING'
    elif atr_ratio > 1.25:
        return 'VOLATILE'
    else:
        return 'CHOPPY'


df['Regime'] = df.apply(classify_regime, axis=1)

# ============================================================================
# TRADE-BASED BACKTEST ENGINE
# ============================================================================


def run_mr_trades(df, exit_mode='middle', max_hold=24, stop_atr=None,
                  regime_filter=None, bb_dev=2.0):
    """
    Proper trade-based MR backtest.

    Entry: price crosses BB lower → long | BB upper → short
    Exit:  (a) return to BB middle, (b) max_hold bars, (c) ATR stop

    Returns: DataFrame of individual trades
    """
    # Recompute BB for given deviation
    bb_temp = BollingerBands(df['Close'], window=20, window_dev=bb_dev)
    upper = bb_temp.bollinger_hband()
    lower = bb_temp.bollinger_lband()
    middle = bb_temp.bollinger_mavg()

    trades = []
    in_trade = False
    entry_bar = None
    direction = None
    entry_price = None

    close = df['Close'].values
    atr = df['ATR'].values
    regime = df['Regime'].values
    up_arr = upper.values
    lo_arr = lower.values
    mi_arr = middle.values

    i = 1
    while i < len(df):
        if not in_trade:
            # Check entry condition
            if regime_filter and regime[i] not in regime_filter:
                i += 1
                continue

            if close[i] < lo_arr[i] and close[i - 1] >= lo_arr[i - 1]:
                # Cross below lower band → long
                in_trade = True
                direction = 1
                entry_bar = i
                entry_price = close[i]

            elif close[i] > up_arr[i] and close[i - 1] <= up_arr[i - 1]:
                # Cross above upper band → short
                in_trade = True
                direction = -1
                entry_bar = i
                entry_price = close[i]

        if in_trade:
            bars_held = i - entry_bar
            exit_reason = None
            exit_price = None

            # Exit conditions
            if exit_mode == 'middle':
                if direction == 1 and close[i] >= mi_arr[i]:
                    exit_price = close[i]
                    exit_reason = 'middle'
                elif direction == -1 and close[i] <= mi_arr[i]:
                    exit_price = close[i]
                    exit_reason = 'middle'

            if exit_price is None and bars_held >= max_hold:
                exit_price = close[i]
                exit_reason = f'timeout_{max_hold}h'

            if stop_atr and exit_price is None:
                stop_dist = stop_atr * atr[entry_bar]
                if direction == 1 and close[i] < entry_price - stop_dist:
                    exit_price = close[i]
                    exit_reason = 'stop'
                elif direction == -1 and close[i] > entry_price + stop_dist:
                    exit_price = close[i]
                    exit_reason = 'stop'

            if exit_price is not None:
                ret = (exit_price / entry_price - 1) * direction * 100
                trades.append({
                    'entry_time': df.index[entry_bar],
                    'exit_time': df.index[i],
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'bars_held': bars_held,
                    'return_pct': ret,
                    'exit_reason': exit_reason,
                    'regime': regime[entry_bar],
                    'atr_ratio': df['ATR_Ratio'].iloc[entry_bar],
                })
                in_trade = False

        i += 1

    return pd.DataFrame(trades)


# ============================================================================
# TEST 1: Exit mode comparison
# ============================================================================

print("\n" + "=" * 70)
print("EXIT MODE COMPARISON (BB-2σ, no regime filter)")
print("=" * 70)

for exit_mode, max_hold, stop_atr, label in [
    ('middle', 48, None, 'Return to Middle, max 48h'),
    ('timeout', 4, None, 'Fixed 4h hold'),
    ('timeout', 8, None, 'Fixed 8h hold'),
    ('timeout', 16, None, 'Fixed 16h hold'),
    ('timeout', 24, None, 'Fixed 24h hold'),
    ('middle', 48, 2.0, 'Middle + 2 ATR stop'),
    ('middle', 48, 1.5, 'Middle + 1.5 ATR stop'),
]:
    trades = run_mr_trades(df, exit_mode=exit_mode, max_hold=max_hold,
                           stop_atr=stop_atr)
    if len(trades) < 20:
        continue
    wr = (trades['return_pct'] > 0).mean() * 100
    avg = trades['return_pct'].mean()
    sh = avg / trades['return_pct'].std() * np.sqrt(252) if trades['return_pct'].std() > 0 else 0
    avg_hold = trades['bars_held'].mean()
    print(f"{label:<32} | n={len(trades):4} | WR={wr:.1f}% | "
          f"Avg={avg:+.3f}% | Sh={sh:+.3f} | AvgHold={avg_hold:.0f}h")

# ============================================================================
# TEST 2: Regime filter (trade MR only in specific regimes)
# ============================================================================

print("\n" + "=" * 70)
print("REGIME FILTER COMPARISON (Return to Middle, 2 ATR stop)")
print("=" * 70)

for regimes, label in [
    (None, 'All regimes'),
    (['RANGING'], 'RANGING only'),
    (['TRENDING'], 'TRENDING only'),
    (['VOLATILE'], 'VOLATILE only'),
    (['CHOPPY'], 'CHOPPY only'),
    (['RANGING', 'CHOPPY'], 'RANGING + CHOPPY'),
]:
    trades = run_mr_trades(df, exit_mode='middle', max_hold=48,
                           stop_atr=2.0, regime_filter=regimes)
    if len(trades) < 15:
        continue
    wr = (trades['return_pct'] > 0).mean() * 100
    avg = trades['return_pct'].mean()
    sh = avg / trades['return_pct'].std() * np.sqrt(252) if trades['return_pct'].std() > 0 else 0
    print(f"{label:<28} | n={len(trades):4} | WR={wr:.1f}% | "
          f"Avg={avg:+.3f}% | Sh={sh:+.3f}")

# ============================================================================
# TEST 3: BB deviation width (tighter vs wider bands)
# ============================================================================

print("\n" + "=" * 70)
print("BB BAND WIDTH (return to middle, 2 ATR stop)")
print("=" * 70)

for dev in [1.5, 1.75, 2.0, 2.5, 3.0]:
    trades = run_mr_trades(df, exit_mode='middle', max_hold=48,
                           stop_atr=2.0, bb_dev=dev)
    if len(trades) < 10:
        continue
    wr = (trades['return_pct'] > 0).mean() * 100
    avg = trades['return_pct'].mean()
    sh = avg / trades['return_pct'].std() * np.sqrt(252) if trades['return_pct'].std() > 0 else 0
    print(f"BB {dev}σ  | n={len(trades):4} | WR={wr:.1f}% | Avg={avg:+.3f}% | Sh={sh:+.3f}")

# ============================================================================
# BEST CONFIG — detailed analysis
# ============================================================================

print("\n" + "=" * 70)
print("BEST CONFIG: DETAILED YEARLY BREAKDOWN")
print("=" * 70)

best_trades = run_mr_trades(df, exit_mode='middle', max_hold=48,
                            stop_atr=2.0, bb_dev=2.0)
best_trades['Year'] = pd.to_datetime(best_trades['entry_time']).dt.year

print(f"\n{'Year':<6} | {'Trades':>7} | {'WR':>8} | {'Avg Ret':>10} | "
      f"{'Total':>8} | {'Timeout%':>9}")
print("-" * 60)
for year in sorted(best_trades['Year'].unique()):
    yd = best_trades[best_trades['Year'] == year]
    wr = (yd['return_pct'] > 0).mean() * 100
    avg = yd['return_pct'].mean()
    tot = yd['return_pct'].sum()
    to_pct = (yd['exit_reason'].str.startswith('timeout')).mean() * 100
    print(f"{year:<6} | {len(yd):>7} | {wr:>7.1f}% | {avg:>+9.3f}% | "
          f"{tot:>+7.1f}% | {to_pct:>8.0f}%")

wr_overall = (best_trades['return_pct'] > 0).mean() * 100
avg_overall = best_trades['return_pct'].mean()
print(f"\nOVERALL | n={len(best_trades)} | WR={wr_overall:.1f}% | Avg={avg_overall:+.3f}%")

# ============================================================================
# VISUALIZATION
# ============================================================================

fig = plt.figure(figsize=(16, 12))
fig.suptitle('HYPOTHESIS 4.1: Proper Trade-Based MR Signal\n'
             '"No ffill. No fake edges. Actual entries and exits."',
             fontsize=14, fontweight='bold')

gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.4)

# --- Plot 1: Trade return distribution ---
ax1 = fig.add_subplot(gs[0, 0])
rets_clipped = best_trades['return_pct'].clip(-2, 2)
ax1.hist(rets_clipped, bins=50, color='#3498db', alpha=0.7, edgecolor='none', density=True)
ax1.axvline(0, color='black', linewidth=1.5)
ax1.axvline(best_trades['return_pct'].mean(), color='red', linewidth=2,
            linestyle='--', label=f"Mean: {best_trades['return_pct'].mean():+.3f}%")
ax1.set_title(f'Trade Return Distribution\n(n={len(best_trades)}, WR={wr_overall:.1f}%)',
              fontweight='bold')
ax1.set_xlabel('Trade Return (%)')
ax1.legend(fontsize=9)
ax1.grid(alpha=0.3)

# --- Plot 2: Hold duration distribution ---
ax2 = fig.add_subplot(gs[0, 1])
ax2.hist(best_trades['bars_held'].clip(upper=48), bins=30,
         color='#e67e22', alpha=0.7, edgecolor='none')
to_pct_total = (best_trades['exit_reason'].str.startswith('timeout')).mean() * 100
ax2.set_title(f'Hold Duration Distribution\n({to_pct_total:.0f}% exit via timeout, rest via middle band)',
              fontweight='bold')
ax2.set_xlabel('Bars Held (hours)')
ax2.set_ylabel('Count')
ax2.grid(alpha=0.3)

# --- Plot 3: Win rate by regime ---
ax3 = fig.add_subplot(gs[0, 2])
regime_wr = best_trades.groupby('regime').agg(
    WR=('return_pct', lambda x: (x > 0).mean() * 100),
    N=('return_pct', 'count'),
    Avg=('return_pct', 'mean')
).reset_index()

colors_r = {'TRENDING': '#2ecc71', 'RANGING': '#3498db',
            'VOLATILE': '#e74c3c', 'CHOPPY': '#f39c12'}
bar_cols_r = [colors_r.get(r, 'gray') for r in regime_wr['regime']]
bars = ax3.bar(regime_wr['regime'], regime_wr['WR'],
               color=bar_cols_r, alpha=0.8, edgecolor='black')
ax3.axhline(50, color='red', linestyle='--', linewidth=1.5, label='50% random')
ax3.set_ylabel('Win Rate (%)')
ax3.set_title('MR Trade Win Rate by Regime\n(Proper entry/exit)', fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(axis='y', alpha=0.3)
ax3.set_ylim(40, 70)
for bar, row in zip(bars, regime_wr.itertuples()):
    ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
             f'{row.WR:.1f}%\nn={row.N}', ha='center', fontsize=8, fontweight='bold')

# --- Plot 4: Cumulative trade equity ---
ax4 = fig.add_subplot(gs[1, 0])
eq = (1 + best_trades['return_pct'] / 100).cumprod()
ax4.plot(range(len(eq)), eq.values, color='#3498db', linewidth=2)
ax4.axhline(1, color='black', linewidth=1)
ax4.fill_between(range(len(eq)), 1, eq.values,
                 where=eq.values > 1, color='#2ecc71', alpha=0.3)
ax4.fill_between(range(len(eq)), 1, eq.values,
                 where=eq.values < 1, color='#e74c3c', alpha=0.3)
ax4.set_xlabel('Trade #')
ax4.set_ylabel('Cumulative equity')
ax4.set_title(f'Trade-by-Trade Equity\n(Final: {eq.iloc[-1]:.2f}x)',
              fontweight='bold')
ax4.grid(alpha=0.3)

# --- Plot 5: Example trades on chart ---
ax5 = fig.add_subplot(gs[1, 1:])

# FIX: Define timestamps with timezone awareness (UTC) to match the data
t_start = pd.Timestamp('2022-01-01', tz='UTC')
t_end = pd.Timestamp('2023-01-01', tz='UTC')

sample_period = df[(df.index >= t_start) & (df.index <= t_end)]
ax5.plot(sample_period.index, sample_period['Close'],
         color='black', linewidth=1, label='Price')
ax5.plot(sample_period.index, sample_period['BB_Upper'],
         color='#e74c3c', linewidth=1, alpha=0.7, linestyle='--', label='BB Upper/Lower')
ax5.plot(sample_period.index, sample_period['BB_Lower'],
         color='#e74c3c', linewidth=1, alpha=0.7, linestyle='--')
ax5.plot(sample_period.index, sample_period['BB_Middle'],
         color='gray', linewidth=1, alpha=0.5, linestyle=':', label='BB Middle')

# Plot trades in this period
# FIX: Use the same timezone-aware timestamps for filtering
sample_trades = best_trades[
    (pd.to_datetime(best_trades['entry_time']) >= t_start) &
    (pd.to_datetime(best_trades['entry_time']) <= t_end)
]

for _, t in sample_trades.iterrows():
    try:
        etime = pd.Timestamp(t['entry_time'])
        # Ensure we only plot if the time is actually in the sample_period index
        if etime in sample_period.index:
            color = '#2ecc71' if t['return_pct'] > 0 else '#e74c3c'
            marker = '^' if t['direction'] == 1 else 'v'
            ax5.scatter([etime], [t['entry_price']], color=color,
                        s=50, zorder=5, marker=marker)
    except Exception:
        continue

ax5.set_title('Example Trades on Chart (2022)\n(▲ = long entry, ▼ = short entry, green=win, red=loss)',
              fontweight='bold')
ax5.legend(fontsize=8)
ax5.grid(alpha=0.3)

plt.savefig('h4_1_proper_mr_trades.png', dpi=150, bbox_inches='tight')
print("\n✓ Saved: h4_1_proper_mr_trades.png")
print("=" * 70)
