# Trading Research

This repository contains the public hypothesis-testing scripts that fuel my research on financial markets, primarily Forex and Gold (XAUUSD). The goal is to move beyond anecdotal evidence and use a data-driven approach to understand market behavior.

## Philosophy

Each script follows a structured approach:

1. **Hypothesis**: A clear, testable assumption about market behavior.
2. **Methodology**: The statistical and programmatic methods used for testing.
3. **Results**: The outcome of the test, often with visualizations.
4. **Conclusion**: Whether the hypothesis is accepted or rejected, and the implications for trading strategies.

## Hypotheses

### H1: Market Characteristics

#### H1.2: Volatility Clustering
- **File**: [`hypotheses/H1_2_volatility_clustering.py`](hypotheses/H1_2_volatility_clustering.py)
- **Assumption**: XAUUSD exhibits volatility clustering (ARCH effects), where high volatility periods follow each other.
- **Status**: ✅ **ACCEPTED**
- **Key Finding**: The analysis shows significant and persistent volatility clustering, making regime-based risk management essential.

### H2: Risk Management

#### H2.1: Stop-Loss Evolution
- **File**: [`hypotheses/H2_1_stop_loss_evolution.py`](hypotheses/H2_1_stop_loss_evolution.py)
- **Assumption**: The optimal stop-loss distance for XAUUSD changes significantly year over year.
- **Status**: ❌ **REJECTED**
- **Key Finding**: There is no steady trend, but rather a cycle between different market regimes (trending vs. choppy).

## How to Use

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/trading-research.git
cd trading-research
```

### 2. Install dependencies
```bash
pip install pandas numpy matplotlib scipy statsmodels
```

### 3. Provide Data

- Place your OHLC data (e.g., a CSV file with `timestamp`, `open`, `high`, `low`, `close` columns) into the `data/` directory.
- **Important**: The scripts are designed to be adapted. You will need to change the filename in the script:
```python
  pd.read_csv("data/your_file.csv")
```

### 4. Run a script
```bash
python hypotheses/H1_2_volatility_clustering.py
```

The script will print results to the console and save any generated plots to the `output/` directory.

## Repository Structure
```
trading-research/
├── hypotheses/          # Hypothesis test scripts
├── data/                # Place your CSV data here (not tracked)
├── output/              # Generated charts and results
└── README.md
```

## Contributing

Found a bug or have a hypothesis suggestion? Open an issue or submit a pull request. All contributions are welcome.

## Disclaimer

⚠️ **These scripts are for educational and research purposes only.** They are not investment advice. Past performance is not indicative of future results. Always do your own research before making any trading decisions.

## License

MIT License - feel free to use and modify as needed.

---

*Built with data, tested with rigor, shared with transparency.*
