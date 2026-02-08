# Trading Research

Scripts I use to test trading ideas before I believe them.

Mostly Forex and Gold (XAUUSD). Moving from "I feel like..." to "the data says..."

## What's here

Code that tests specific hypotheses. Not a trading system. Not advice.

### H1.2: Volatility Clustering
Does high volatility follow high volatility in Gold?

**Result:** Yes. Strong ARCH effects. Regime-based sizing is essential.

[Script](hypotheses/H1_2_volatility_clustering.py)

### H2.1: Stop-Loss Evolution  
Do optimal stops get wider every year?

**Result:** No. They cycle. 2021=2.5x ATR, 2023=0.5x, 2024=2.5x again.

Market mood matters more than calendar year.

[Script](hypotheses/H2_1_stop_loss_evolution.py)

## How to use this

1. Clone it
2. Put your OHLC CSV in `data/`
3. Change the filename in the script (yeah, manual, sorry)
4. Run it

```bash
pip install pandas numpy matplotlib scipy statsmodels
python hypotheses/H1_2_volatility_clustering.py

What you won't find here

    Live trading code
    Optimized strategies
    Secrets I'm keeping back

Just raw tests. Some work, most don't. That's the point.
Disclaimer
This is research, not trading advice. If you blow up your account copying a script from the internet, that's on you.
MIT License. Do what you want.
