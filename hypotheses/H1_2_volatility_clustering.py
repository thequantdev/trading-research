"""
HYPOTHESIS H1.2: Volatility Clustering
======================================

Copyright (c) 2026 thequantdev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.diagnostic import het_arch
from statsmodels.graphics.tsaplots import plot_acf
import os

# --- DATA LOADING ---
# IMPORTANT: Replace 'your_data_file.csv' with your actual data file name.
# The file should be placed in the 'data/' directory.
# It must have the columns: 'Time', 'Open', 'High', 'Low', 'Close'.
try:
    data_path = os.path.join('data', 'your_data_file.csv')
    data = pd.read_csv(data_path, parse_dates=['Time'], index_col='Time')
    print(f"Data loaded successfully from {data_path}")
except FileNotFoundError:
    print("ERROR: Data file not found. Please place your OHLC CSV file in the 'data/' directory and update the 'data_path' variable.")
    exit()

print("="*70)
print("HYPOTHESIS H1.2: VOLATILITY CLUSTERING")
print("="*70)

# Calculate returns
returns = data['Close'].pct_change().dropna()
log_returns = np.log(data['Close'] / data['Close'].shift(1)).dropna()

# ============================================================================
# 1. ARCH-LM TEST
# ============================================================================

print(f"\n{'ARCH-LM TEST (Engle 1982)':-^70}")

# Test for various lags
for lag in [1, 5, 10, 20]:
    try:
        lm_stat, lm_pvalue, f_stat, f_pvalue = het_arch(returns.dropna(), nlags=lag)

        print(f"\nLag {lag}:")
        print(f"  LM Statistic: {lm_stat:.4f}")
        print(f"  p-value:      {lm_pvalue:.6f}")

        if lm_pvalue < 0.01:
            print(f"  → Very strong clustering (p < 0.01) ✓✓")
        elif lm_pvalue < 0.05:
            print(f"  → Significant clustering (p < 0.05) ✓")
        else:
            print(f"  → No significant clustering")
    except:
        print(f"Lag {lag}: Error in calculation")

# ============================================================================
# 2. AUTOCORRELATION OF SQUARED RETURNS
# ============================================================================

squared_returns = returns ** 2
acf_squared = [squared_returns.autocorr(lag=i) for i in range(1, 21)]

print(f"\n{'AUTOCORRELATION OF SQUARED RETURNS':-^70}")
print("Lag | ACF(r²) | Significant?")
print("-" * 70)

for i in range(10):
    is_sig = "✓✓" if acf_squared[i] > 0.10 else "✓" if acf_squared[i] > 0.05 else ""
    print(f"{i+1:3d} | {acf_squared[i]:7.4f} | {is_sig}")

lag1_acf_sq = acf_squared[0]
print(f"\nLag-1 ACF(r²): {lag1_acf_sq:.4f}")

if lag1_acf_sq > 0.10:
    print("  → STRONG volatility persistence ✓✓")
elif lag1_acf_sq > 0.05:
    print("  → MODERATE volatility persistence ✓")
else:
    print("  → Weak/No persistence")

# ============================================================================
# 3. ROLLING VOLATILITY & REGIME DETECTION
# ============================================================================

print(f"\n{'VOLATILITY REGIME ANALYSIS':-^70}")

# Rolling STD (different windows)
vol_24h = returns.rolling(24).std()  # 24H
vol_168h = returns.rolling(168).std()  # 1 Week

# Regime Classification (25/75 Percentile)
vol_threshold_low = vol_24h.quantile(0.25)
vol_threshold_high = vol_24h.quantile(0.75)

low_vol_regime = vol_24h < vol_threshold_low
high_vol_regime = vol_24h > vol_threshold_high
mid_vol_regime = ~low_vol_regime & ~high_vol_regime

# Statistics per regime
print(f"\nVolatility Thresholds (24H Rolling):")
print(f"  Low Vol (Q25):  < {vol_threshold_low:.6f}")
print(f"  High Vol (Q75): > {vol_threshold_high:.6f}")

print(f"\nRegime Distribution:")
print(f"  Low Vol:  {low_vol_regime.sum() / len(vol_24h) * 100:.1f}%")
print(f"  Mid Vol:  {mid_vol_regime.sum() / len(vol_24h) * 100:.1f}%")
print(f"  High Vol: {high_vol_regime.sum() / len(vol_24h) * 100:.1f}%")

# Volatility Persistence
avg_vol_low = vol_24h[low_vol_regime].mean()
avg_vol_high = vol_24h[high_vol_regime].mean()
vol_ratio = avg_vol_high / avg_vol_low

print(f"\nVolatility Ratio (High/Low): {vol_ratio:.2f}x")

if vol_ratio > 2.5:
    print("  → Very distinct regimes (>2.5x) ✓✓")
    print("  → Regime filters are ESSENTIAL")
elif vol_ratio > 1.5:
    print("  → Clear regimes (>1.5x) ✓")
    print("  → Regime filters recommended")
else:
    print("  → Weak regime differences")

# Clustering Metric: Average Regime Duration
def calculate_regime_duration(regime_series):
    """Calculates the average duration of a regime"""
    changes = regime_series.astype(int).diff().abs()
    regime_starts = changes[changes == 1].index

    if len(regime_starts) < 2:
        return 0

    durations = []
    for i in range(len(regime_starts) - 1):
        duration = (regime_starts[i+1] - regime_starts[i]).total_seconds() / 3600
        durations.append(duration)

    return np.mean(durations) if durations else 0

high_vol_duration = calculate_regime_duration(high_vol_regime)
low_vol_duration = calculate_regime_duration(low_vol_regime)

print(f"\nAverage Regime Duration:")
print(f"  High Vol: {high_vol_duration:.1f} hours")
print(f"  Low Vol:  {low_vol_duration:.1f} hours")

if high_vol_duration > 48:
    print("  → Long-lasting high-vol phases (>48h) ✓")
    print("  → Regime filters can react in time")

# ============================================================================
# 4. VOLATILITY CLUSTERING VISUALIZATION
# ============================================================================

fig, axes = plt.subplots(4, 1, figsize=(14, 12))

# Plot 1: Returns with Volatility Regimes
axes[0].plot(returns.index, returns, linewidth=0.5, color='black', alpha=0.6)
axes[0].fill_between(returns.index, returns.min(), returns.max(),
                     where=high_vol_regime, alpha=0.2, color='red', label='High Vol')
axes[0].fill_between(returns.index, returns.min(), returns.max(),
                     where=low_vol_regime, alpha=0.2, color='green', label='Low Vol')
axes[0].set_title('Returns with Volatility Regimes', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Returns')
axes[0].legend(loc='upper right')
axes[0].grid(alpha=0.3)

# Plot 2: Rolling Volatility
axes[1].plot(vol_24h.index, vol_24h, linewidth=1, color='darkblue', label='24H Vol')
axes[1].plot(vol_168h.index, vol_168h, linewidth=1, color='orange',
             alpha=0.7, label='168H Vol')
axes[1].axhline(y=vol_threshold_high, color='red', linestyle='--',
                label=f'High Threshold ({vol_threshold_high:.6f})')
axes[1].axhline(y=vol_threshold_low, color='green', linestyle='--',
                label=f'Low Threshold ({vol_threshold_low:.6f})')
axes[1].set_title('Rolling Volatility (24H & 168H)', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Volatility (Std Dev)')
axes[1].legend(loc='upper right', fontsize=9)
axes[1].grid(alpha=0.3)

# Plot 3: ACF of Squared Returns
axes[2].bar(range(1, 21), acf_squared, color='purple', alpha=0.7, edgecolor='black')
axes[2].axhline(y=0, color='black', linewidth=1)
axes[2].axhline(y=0.05, color='orange', linestyle='--', label='Moderate (0.05)')
axes[2].axhline(y=0.10, color='red', linestyle='--', label='Strong (0.10)')
axes[2].set_title('Autocorrelation of Squared Returns (Volatility Clustering)',
                 fontsize=12, fontweight='bold')
axes[2].set_xlabel('Lag')
axes[2].set_ylabel('ACF(r²)')
axes[2].legend()
axes[2].grid(alpha=0.3)

# Plot 4: Volatility Distribution
axes[3].hist(vol_24h.dropna(), bins=100, color='darkblue', alpha=0.7, edgecolor='black')
axes[3].axvline(x=vol_threshold_low, color='green', linestyle='--', linewidth=2,
                label='Low Vol Threshold')
axes[3].axvline(x=vol_threshold_high, color='red', linestyle='--', linewidth=2,
                label='High Vol Threshold')
axes[3].set_title('Volatility Distribution (24H Rolling)', fontsize=12, fontweight='bold')
axes[3].set_xlabel('Volatility (Std Dev)')
axes[3].set_ylabel('Frequency')
axes[3].legend()
axes[3].grid(alpha=0.3)

# Ensure the output directory exists
output_dir = 'output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save the plots in the output directory
plt.tight_layout()
plot_path = os.path.join(output_dir, 'H1_2_volatility_clustering.png')
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
print(f"\n✓ Visualization saved to {plot_path}")
plt.show()

# ============================================================================
# 5. SUMMARY & DECISION
# ============================================================================

print("\n" + "="*70)
print("HYPOTHESIS H1.2: DECISION")
print("="*70)

# Acceptance Scoring
score = 0

if lag1_acf_sq > 0.10:
    score += 2
    print(f"✓✓ Strong vol-persistence (ACF(r²) = {lag1_acf_sq:.4f})")
elif lag1_acf_sq > 0.05:
    score += 1
    print(f"✓ Moderate vol-persistence (ACF(r²) = {lag1_acf_sq:.4f})")

if vol_ratio > 2.5:
    score += 2
    print(f"✓✓ Very distinct regimes (Ratio = {vol_ratio:.2f}x)")
elif vol_ratio > 1.5:
    score += 1
    print(f"✓ Clear regimes (Ratio = {vol_ratio:.2f}x)")

if high_vol_duration > 48:
    score += 1
    print(f"✓ Persistent high-vol phases ({high_vol_duration:.1f}h)")

print(f"\nTotal Score: {score}/5")

print("\n" + "="*70)
print("H1.2 ACCEPTANCE CRITERION:")
print("="*70)

if score >= 3:
    print("✓ ACCEPTED: Volatility clustering is significant")
    print("\n→ IMPLICATIONS:")
    print("  1. Dynamic Position Sizing based on volatility regime")
    print("  2. Wider stops in high-vol, tighter in low-vol")
    print("  3. Regime filters for signal activation")
    print("  4. Consider GARCH models for volatility forecast")
    print("\n→ Next step: H1.3 (Intraday Patterns)")
elif score >= 2:
    print("⚠ PARTIALLY ACCEPTED: Moderate clustering")
    print("→ Use simple volatility filters")
    print("→ Next step: H1.3")
else:
    print("✗ REJECTED: No significant clustering")
    print("→ Volatility filters are likely not helpful")

print("="*70)
