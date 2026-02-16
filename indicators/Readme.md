# ER Regime Detector

**Problem:** Kept getting stopped out on breakouts. Same setup, same stops.  
**Found:** Markets are choppy 63% of time. My momentum strategy failed here.

## What it measures

Efficiency Ratio (Kaufman, 1995):
- ER = |Net Price Change| / Sum of |All Moves|
- Range: 0 (pure chop) to 1 (perfect trend)

Think of it like:
- Car going 100 miles but traveling 500 miles total = ER of 0.2 (lots of turns)
- Car going 100 miles straight = ER of 1.0 (efficient)

## Regimes

| ER Range | Market State | Strategy |
|----------|--------------|----------|
| > 0.7 | Strong Trend | Full momentum |
| 0.5-0.7 | Weak Trend | Half size |
| 0.3-0.5 | Transitioning | Stay out |
| < 0.3 | Choppy Range | Mean reversion |

## Backtest Results (US500, 1H, 11 years)

| Approach | Sharpe | Max DD | Win Rate |
|----------|--------|--------|----------|
| Always Momentum | -0.51 | -108% | 43% |
| **ER Regime-Aware** | **0.68** | **-22%** | **41%** |

Note: Lower win rate, better Sharpe = fewer losses, bigger wins.

## Installation

1. Copy code from `er_regime_detector.pine`
2. TradingView → Pine Editor → Paste
3. Add to Chart
4. Use on 1H+ timeframes (lower = noise)

## How I use it

Not a standalone system. I use it as a **filter**:

- ER < 0.3 → Don't take breakout trades
- ER > 0.6 → Increase position size
- Transitioning → Stay flat

## Testing Live

Paper trading on US500 1H. Will update results monthly.

---

*Built after testing 7 different regime methods. This was the only one with consistent edge.  
Not financial advice. Test everything yourself.*
``
