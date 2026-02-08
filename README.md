# Trading Research

Scripts I use to test trading ideas before I believe them.

Mostly Forex and Gold (XAUUSD). Moving from "I feel like..." to "the data says..."

## What's here

Code that tests specific hypotheses. Not a trading system. Not advice.

### H1.2: Volatility Clustering
Does high volatility follow high volatility in Gold?

**Result:** ✅ Yes. Strong ARCH effects. Regime-based sizing is essential.

[Script](hypotheses/H1_2_volatility_clustering.py)

### H2.1: Stop-Loss Evolution  
Do optimal stops get wider every year?

**Result:** ❌ No. They cycle. 2021=2.5x ATR, 2023=0.5x, 2024=2.5x again. Market mood matters more than calendar year.

[Script](hypotheses/H2_1_stop_loss_evolution.py)

### H2.2: ATR Fast-Slow Ratio
Does relative volatility (Fast/Slow ATR) beat absolute ATR?

**Result:** ⚠️ Mixed. Good dashboard for current mood, poor predictor. Fixed stops won in 2024 backtest.

[Script](hypotheses/H2_2_atr_ratio.py)

## Quick start
```bash
pip install pandas numpy matplotlib scipy statsmodels
python hypotheses/H2_2_atr_ratio.py
```

## Structure
```
trading-research/
├── hypotheses/     # Test scripts
├── data/           # Your CSV files (not tracked)
└── output/         # Generated charts
```

Drop your OHLC CSV in `data/` and update the path in the script.

---

**Disclaimer:** Educational only. Not financial advice. Test everything yourself.
