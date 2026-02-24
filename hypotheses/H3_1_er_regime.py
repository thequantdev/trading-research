"""
H3.1: Why momentum keeps failing (68K bars of US500)

Claim: Markets chop 63% of time. Momentum = 43% win rate. Mean reversion = 68%.
Test it yourself: Update DATA_PATH below, run script.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from ta.volatility import BollingerBands

# ============================================================================
# DATA LOADING
# ============================================================================

df = pd.read_csv('/content/drive/MyDrive/Video/data/us500_1H.csv',
                 parse_dates=['Time'], index_col='Time')

print("="*70)
print("US500 BACKTEST - REDDIT PLOT v3")
print("="*70)
print(f"\nData: {len(df)} bars ({df.index[0]} to {df.index[-1]})")

# ============================================================================
# EFFICIENCY RATIO
# ============================================================================

def calculate_efficiency_ratio(df, period=20):
    direction = abs(df['Close'] - df['Close'].shift(period))
    volatility = df['Close'].diff().abs().rolling(period).sum()
    return direction / volatility

df['ER_20'] = calculate_efficiency_ratio(df, 20)
df['ER_50'] = calculate_efficiency_ratio(df, 50)

bb = BollingerBands(df['Close'], window=20, window_dev=2)
df['BB_Upper'] = bb.bollinger_hband()
df['BB_Lower'] = bb.bollinger_lband()
df['BB_Middle'] = bb.bollinger_mavg()

df = df.dropna()

# ============================================================================
# REGIME CLASSIFICATION
# ============================================================================

def classify_regime(row):
    er20 = row['ER_20']
    er50 = row['ER_50']
    if er20 > 0.6 and er50 > 0.5:
        return 'STRONG_TREND'
    elif 0.4 < er20 < 0.6:
        return 'WEAK_TREND'
    elif er20 < 0.3:
        return 'CHOPPY_RANGE'
    elif er20 > 0.6 and er50 < 0.4:
        return 'BREAKOUT_SETUP'
    else:
        return 'TRANSITIONING'

df['Regime'] = df.apply(classify_regime, axis=1)
regime_counts = df['Regime'].value_counts()
regime_pct = (regime_counts / len(df) * 100).round(1)

# ============================================================================
# STRATEGY SIGNALS
# ============================================================================

df['Returns'] = df['Close'].pct_change()

df['High_20'] = df['High'].rolling(20).max()
df['Low_20']  = df['Low'].rolling(20).min()
df['Momentum_Signal'] = 0
df.loc[df['Close'] > df['High_20'].shift(1), 'Momentum_Signal'] = 1
df.loc[df['Close'] < df['Low_20'].shift(1),  'Momentum_Signal'] = -1
df['Momentum_Signal'] = df['Momentum_Signal'].replace(0, np.nan).ffill().fillna(0)

df['MR_Signal'] = 0
df.loc[df['Close'] < df['BB_Lower'], 'MR_Signal'] = 1
df.loc[df['Close'] > df['BB_Upper'], 'MR_Signal'] = -1
df['MR_Signal'] = df['MR_Signal'].replace(0, np.nan).ffill().fillna(0)

df['Momentum_Returns'] = df['Returns'] * df['Momentum_Signal'].shift(1)
df['MR_Returns']       = df['Returns'] * df['MR_Signal'].shift(1)

# ============================================================================
# REGIME-AWARE STRATEGY
# ============================================================================

STRATEGY_MAP = {
    'STRONG_TREND':   ('momentum', 1.0),
    'WEAK_TREND':     ('momentum', 0.5),
    'CHOPPY_RANGE':   ('mr',       1.0),
    'BREAKOUT_SETUP': ('momentum', 1.0),
    'TRANSITIONING':  ('none',     0),
}

df['Smart_Signal'] = 0.0
for regime, (strategy, size) in STRATEGY_MAP.items():
    mask = df['Regime'] == regime
    if strategy == 'momentum':
        df.loc[mask, 'Smart_Signal'] = df.loc[mask, 'Momentum_Signal'] * size
    elif strategy == 'mr':
        df.loc[mask, 'Smart_Signal'] = df.loc[mask, 'MR_Signal'] * size

df['Smart_Returns'] = df['Returns'] * df['Smart_Signal'].shift(1)
df = df.dropna()

always_returns = df['Momentum_Returns'].fillna(0)
smart_returns  = df['Smart_Returns'].fillna(0)

# ============================================================================
# METRICS
# ============================================================================

sharpe_always = (always_returns.mean() / always_returns.std()) * np.sqrt(252 * 24)
sharpe_smart  = (smart_returns.mean()  / smart_returns.std())  * np.sqrt(252 * 24)

equity_always = (1 + always_returns).cumprod()
equity_smart  = (1 + smart_returns).cumprod()

final_always = equity_always.iloc[-1]
final_smart  = equity_smart.iloc[-1]

def calculate_max_dd(equity):
    rolling_max = equity.expanding().max()
    return ((equity - rolling_max) / rolling_max).min()

max_dd_always = calculate_max_dd(equity_always)
max_dd_smart  = calculate_max_dd(equity_smart)

choppy_mask       = df['Regime'] == 'CHOPPY_RANGE'
strong_trend_mask = df['Regime'].isin(['STRONG_TREND', 'WEAK_TREND'])

choppy_mom_wr = (df.loc[choppy_mask,       'Momentum_Returns'] > 0).mean() * 100
choppy_mr_wr  = (df.loc[choppy_mask,       'MR_Returns']       > 0).mean() * 100
trend_mom_wr  = (df.loc[strong_trend_mask, 'Momentum_Returns'] > 0).mean() * 100

print(f"\nAlways Momentum: {final_always:.2f}x | Sharpe: {sharpe_always:.2f} | DD: {max_dd_always*100:.1f}%")
print(f"Regime-Aware:    {final_smart:.2f}x  | Sharpe: {sharpe_smart:.2f}  | DD: {max_dd_smart*100:.1f}%")
print(f"\nWin Rates — Choppy Mom: {choppy_mom_wr:.1f}% | Choppy MR: {choppy_mr_wr:.1f}% | Trend Mom: {trend_mom_wr:.1f}%")

# ============================================================================
# COLORS
# ============================================================================

C = {
    'bg':      '#0d1117',
    'bg2':     '#161b22',
    'border':  '#30363d',
    'grid':    '#21262d',
    'text':    '#c9d1d9',
    'subtext': '#8b949e',
    'green':   '#3fb950',
    'red':     '#f85149',
    'yellow':  '#d29922',
    'blue':    '#58a6ff',
}

# ============================================================================
# FIGURE
# ============================================================================

fig = plt.figure(figsize=(18, 6.5))
fig.patch.set_facecolor(C['bg'])

fig.text(0.5, 0.97,
         f'US500 · {len(df):,} bars · 2014–2026  |  Efficiency Ratio Regime Detection',
         ha='center', va='top',
         color=C['subtext'], fontsize=10.5, style='italic')

gs = gridspec.GridSpec(1, 3, figure=fig,
                       left=0.06, right=0.97,
                       top=0.88, bottom=0.14,
                       wspace=0.32)

def style_ax(ax, title):
    ax.set_facecolor(C['bg2'])
    ax.set_title(title, color=C['text'], fontsize=11,
                 fontweight='bold', pad=10)
    ax.tick_params(colors=C['subtext'], labelsize=9)
    ax.grid(axis='y', alpha=0.15, color=C['grid'], linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_color(C['border'])

# ============================================================================
# PANEL 1 — Regime Distribution
# ============================================================================

ax1 = fig.add_subplot(gs[0])
style_ax(ax1, '① Market Regime Distribution')

regimes    = ['Choppy\nRange', 'Weak\nTrend', 'Transition', 'Breakout\nSetup', 'Strong\nTrend']
pcts       = [
    regime_pct.get('CHOPPY_RANGE', 0),
    regime_pct.get('WEAK_TREND', 0),
    regime_pct.get('TRANSITIONING', 0),
    regime_pct.get('BREAKOUT_SETUP', 0),
    regime_pct.get('STRONG_TREND', 0),
]
bar_colors = [C['red'], C['yellow'], C['border'], C['blue'], C['green']]

bars1 = ax1.bar(regimes, pcts, color=bar_colors,
                alpha=0.85, edgecolor=C['bg'], linewidth=1.2, width=0.6)

for bar, pct in zip(bars1, pcts):
    if pct > 0.5:
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.8,
                 f'{pct:.1f}%',
                 ha='center', va='bottom',
                 color=C['text'], fontsize=10, fontweight='bold')

ax1.set_ylabel('% of Time', color=C['subtext'], fontsize=10)
ax1.set_ylim(0, max(pcts) * 1.25)

choppy_val = regime_pct.get('CHOPPY_RANGE', 0)
ax1.annotate('momentum\nfails here',
             xy=(0, choppy_val),
             xytext=(1.7, choppy_val * 0.82),
             fontsize=8.5, color=C['red'], ha='center',
             arrowprops=dict(arrowstyle='->', color=C['red'],
                             lw=1.2, connectionstyle='arc3,rad=0.2'))

# ============================================================================
# PANEL 2 — Win Rate by Condition
# FIX: kein Legend-Overlap — "50% breakeven" wird direkt auf die Linie
#      geschrieben (links, in der Mitte der Achse), keine Legend-Box mehr
# ============================================================================

ax2 = fig.add_subplot(gs[1])
style_ax(ax2, '② Win Rate by Market Condition')

conditions = ['CHOPPY\n(Momentum)', 'CHOPPY\n(Mean Rev.)', 'TRENDING\n(Momentum)']
win_rates  = [choppy_mom_wr, choppy_mr_wr, trend_mom_wr]
wr_colors  = [C['red'], C['green'], C['green']]

bars2 = ax2.bar(conditions, win_rates, color=wr_colors,
                alpha=0.85, edgecolor=C['bg'], linewidth=1.2, width=0.5)

for bar, wr in zip(bars2, win_rates):
    ax2.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + 0.3,
             f'{wr:.1f}%',
             ha='center', va='bottom',
             color=C['text'], fontsize=11, fontweight='bold')

ax2.set_ylabel('Win Rate %', color=C['subtext'], fontsize=10)
ax2.set_ylim(35, 75)

# 50%-Linie ohne Legend — Label direkt links auf die Linie
ax2.axhline(y=50, color=C['subtext'], linestyle='--', linewidth=1.2, alpha=0.6)
ax2.text(-0.34, 50.5,                    # x=-0.48 = knapp links vom ersten Balken
         '— 50% breakeven',
         color=C['subtext'], fontsize=7.5, va='bottom', ha='left')

# ✗ / ✓ Labels — nach unten verschoben damit kein Overlap mehr möglich
ax2.text(0,  71, '✗ Wrong\nstrategy', ha='center', va='bottom',
         color=C['red'],   fontsize=8.5, fontweight='bold')
ax2.text(2,  71, '✓ Right\nstrategy', ha='center', va='bottom',
         color=C['green'], fontsize=8.5, fontweight='bold')

# ============================================================================
# PANEL 3 — Equity Curves
# Annotation unter dem Rand: absichtlich (roter Pfad endet nahe 0)
# ============================================================================

ax3 = fig.add_subplot(gs[2])
style_ax(ax3, '③ Same Signals — Regime-Aware vs Always-On')

trading_days = np.arange(len(equity_always)) / 24

ax3.plot(trading_days, equity_always.values,
         color=C['red'],   linewidth=1.8,
         label=f'Always Momentum ({final_always:.2f}x)', alpha=0.85)
ax3.plot(trading_days, equity_smart.values,
         color=C['green'], linewidth=2.2,
         label=f'Regime-Aware ({final_smart:.2f}x)',     alpha=0.95)

ax3.annotate(
    f'{(final_always-1)*100:.0f}%\nSharpe {sharpe_always:.2f}\nDD {max_dd_always*100:.0f}%',
    xy=(trading_days[-1], final_always),
    xytext=(-60, -35), textcoords='offset points',
    color=C['red'], fontsize=8.5, ha='center',
    arrowprops=dict(arrowstyle='->', color=C['red'], lw=1)
)
ax3.annotate(
    f'+{(final_smart-1)*100:.0f}%\nSharpe {sharpe_smart:.2f}\nDD {max_dd_smart*100:.0f}%',
    xy=(trading_days[-1], final_smart),
    xytext=(-65, 18), textcoords='offset points',
    color=C['green'], fontsize=9, ha='center', fontweight='bold',
    arrowprops=dict(arrowstyle='->', color=C['green'], lw=1)
)

ax3.set_ylabel('Equity Multiplier', color=C['subtext'], fontsize=10)
ax3.set_xlabel('Trading Days',      color=C['subtext'], fontsize=10)
ax3.legend(facecolor=C['bg2'], edgecolor=C['border'],
           labelcolor=C['text'], loc='upper left', fontsize=8.5)
ax3.set_ylim(0, max(final_smart, 1) * 1.35)
ax3.grid(alpha=0.12, color=C['grid'])

# ── Footer ───────────────────────────────────────────────────────────────────
fig.text(0.97, 0.005,
         'ER-based Regime Detection  |  US500 1H  |  2014–2026  |  ~68K bars',
         ha='right', va='bottom',
         color=C['subtext'], fontsize=7.5, style='italic')

# ============================================================================
# SAVE
# ============================================================================

plt.savefig('h3_1_results.png', dpi=150, bbox_inches='tight', facecolor='#0d1117')
print("Saved: h3_1_results.png")
plt.show()

print("\n" + "="*70)
print("✓ Saved: reddit_plot_us500_v3.png")
print(f"  Always Momentum: {final_always:.2f}x | Sharpe: {sharpe_always:.2f} | DD: {max_dd_always*100:.1f}%")
print(f"  Regime-Aware:    {final_smart:.2f}x  | Sharpe: {sharpe_smart:.2f}  | DD: {max_dd_smart*100:.1f}%")
print("="*70)
