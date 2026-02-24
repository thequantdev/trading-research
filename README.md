# Trading Research

Testing ideas with data before I believe them.

Focus: Forex and Gold (XAUUSD). Moving from "I feel like..." to "the data says..."

## What's here

Code that tests specific hypotheses. Not a system, not advice.

### ✅ H1.2: Volatility Clustering
**Question:** Does high volatility follow high volatility in Gold?  
**Result:** Yes. Strong ARCH effects. Regime-based sizing works.  
[Script](hypotheses/H1_2_volatility_clustering.py) | [Post](https://www.reddit.com/r/Forex/comments/1qvtuqr/i_kept_getting_stopped_out_then_i_ran_the_numbers/)

### ⚠️ H2.1: ATR Fast-Slow Ratio
**Question:** Does relative volatility beat absolute ATR?  
**Result:** Mixed. Good for dashboards, poor for prediction. Fixed stops won in 2024.  
[Script](hypotheses/H2_1_atr_ratio.py) | [Post](https://www.reddit.com/r/Forex/comments/1qzm7sh/tested_atr_ratio_idea_higher_win_rate_less_profit/)

### 🧪 H3.1: Efficiency Ratio Regime Detection
**Question:** Can we detect choppy vs trending markets?  
**Result:** Testing live. Backtest Sharpe: 0.68  
[Script](hypotheses/H3_1_er_regime.py) | [Pine Script](indicators/H3_1_er_regime.pine) | [Post](https://www.reddit.com/r/algotrading/comments/1r7c2p3/kept_getting_chopped_up_in_us500_then_i_checked/) | [Video](https://youtube.com/shorts/zW1g_VzLznM?feature=share)

🧪 H4.1: Proper Mean Reversion Entry
Question: Was I measuring MR wrong? (No ffill, actual trade entries/exits)
Result: Walk-forward tested. 10/11 folds positive. OOS Sharpe: 1.995
[Script](hypotheses/H4_1_better_mean_reversion.py) 

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
