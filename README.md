<div align="center">
  <h1>Execution And Hedge Analytics</h1>
  <p><strong>A public-safe post-trade analytics project for reviewing execution cost, urgency, hedge effectiveness, and residual risk.</strong></p>
  <p>Designed to complement a trader-front-end demo by showing what happens after the trade is sent.</p>
</div>

<p align="center">
  <code>execution analytics</code>
  <code>hedge review</code>
  <code>slippage analysis</code>
  <code>synthetic trade data</code>
  <code>post-trade workflow</code>
</p>

## Portfolio Role

This is the post-trade analytics repo in the portfolio. It sits naturally next to the trading-terminal project: one shows the live front-end, and this one shows the execution and hedge review layer that comes after.

## What This Project Covers

- implementation shortfall and slippage review
- urgency bucket analysis
- venue quality comparison
- hedge basket effectiveness
- residual beta and time-to-flat analysis
- an order replay panel for reviewing one synthetic order in detail

## Structure

```text
execution-and-hedge-analytics/
├── app.py
├── README.md
├── requirements.txt
├── data/
├── figures/
├── results/
└── src/
    ├── __init__.py
    ├── analytics.py
    ├── analysis.py
    ├── generate_data.py
    └── ui.py
```

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.generate_data
python -m src.analysis
streamlit run app.py
```

## Generated Outputs

After running the scripts, you should see:

- `data/synthetic_execution_data.csv`
- `results/top_line_metrics.csv`
- `results/urgency_summary.csv`
- `results/hedge_summary.csv`
- `results/venue_summary.csv`
- `results/worst_orders.csv`
- `results/key_findings.md`
- `figures/slippage_by_urgency.png`
- `figures/hedge_effectiveness_scatter.png`
- `figures/daily_execution_trends.png`

## Why This Is Useful In A Portfolio

This repo helps tell a more credible trader / quant workflow story:

- not just monitoring a live book
- but also measuring how expensive execution was
- how quickly hedges worked
- and where the desk should investigate poor outcomes

## Notes

- All trades, symbols, hedge baskets, and metrics in this repo are synthetic.
- The goal is to demonstrate analytics and workflow design, not proprietary execution logic.

## Screenshot Strategy

- use the hero plus `Urgency And Cost` as the main README screenshot
- optionally add the hedge effectiveness scatter as a second image
- if you want a tighter product feel, crop one screenshot around the order replay panel
