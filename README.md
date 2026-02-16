# Trading Research

Testing ideas with data before I believe them.

Focus: Forex and Gold (XAUUSD). Moving from "I feel like..." to "the data says..."

## What's here

Code that tests specific hypotheses. Not a system, not advice.

### ✅ H1.2: Volatility Clustering
**Question:** Does high volatility follow high volatility in Gold?  
**Result:** Yes. Strong ARCH effects. Regime-based sizing works.  
[Script](hypotheses/H1_2_volatility_clustering.py) | [Post](link to reddit)

### ⚠️ H2.1: ATR Fast-Slow Ratio
**Question:** Does relative volatility beat absolute ATR?  
**Result:** Mixed. Good for dashboards, poor for prediction. Fixed stops won in 2024.  
[Script](hypotheses/H2_1_atr_ratio.py) | [Post](link to reddit)

### 🧪 H3.1: Efficiency Ratio Regime Detection
**Question:** Can we detect choppy vs trending markets?  
**Result:** Testing live. Backtest Sharpe: 0.68  
[Pine Script](indicators/H3_1_er_regime.pine) | [Details](indicators/README.md)

## Quick start
```bash
pip install pandas numpy matplotlib scipy statsmodels
python hypotheses/H2_1_atr_ratio.py
```

Drop your OHLC CSV in `data/` and update the path in the script.

## Live Testing (TradingView)

| Indicator | Status | Backtest Sharpe | Link |
|-----------|--------|-----------------|------|
| ER Regime Detector | Paper trading | 0.68 | [Pine](indicators/H3_1_er_regime.pine) |

Updates: Monthly logs in `output/live_results/`

---

**Disclaimer:** Educational only. Not financial advice. I lose money too.
