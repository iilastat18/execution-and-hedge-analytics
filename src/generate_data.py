from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REGIONS = ["US", "Europe", "Asia"]
SECTORS = ["Semis", "Software", "Healthcare", "Industrials", "Consumer", "Energy"]
URGENCY_BUCKETS = ["Patient", "Normal", "Urgent"]
STRATEGIES = ["TWAP", "VWAP", "Liquidity Seeking", "Manual Hedge"]
VENUES = ["XNAS", "BATS", "ARCX", "XPAR", "XAMS", "XTKS", "XHKG"]
HEDGE_BASKETS = {"US": ["HXUS", "HXUS_TECH"], "Europe": ["HXEU", "HXEU_GROWTH"], "Asia": ["HXAS", "HXAS_HIGHBETA"]}


def build_execution_dataset(seed: int = 17, n_orders: int = 260) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-01-05", periods=90, freq="B")
    rows: list[dict[str, object]] = []

    for idx in range(n_orders):
        region = REGIONS[idx % len(REGIONS)]
        sector = SECTORS[(idx * 2) % len(SECTORS)]
        urgency = URGENCY_BUCKETS[(idx + (idx // 7)) % len(URGENCY_BUCKETS)]
        strategy = STRATEGIES[(idx * 3) % len(STRATEGIES)]
        venue_choices = [venue for venue in VENUES if (region == "US" and venue in {"XNAS", "BATS", "ARCX"}) or (region == "Europe" and venue in {"XPAR", "XAMS"}) or (region == "Asia" and venue in {"XTKS", "XHKG"})]
        venue = venue_choices[idx % len(venue_choices)]
        symbol = f"{region[0]}{sector[:2].upper()}{idx + 1:03d}"
        side = "BUY" if idx % 2 == 0 else "SELL"

        arrival_mid = float(np.clip(rng.lognormal(mean=4.35, sigma=0.32), 18.0, 240.0))
        base_notional = float(np.clip(rng.lognormal(mean=13.4, sigma=0.55), 85_000.0, 4_200_000.0))
        participation = float(np.clip(rng.normal(14.5, 5.8), 4.0, 32.0))
        vol_1m_pct = float(np.clip(rng.normal(1.25, 0.55), 0.25, 3.8))
        spread_bps = float(np.clip(rng.normal(9.0, 3.4), 3.0, 26.0))

        urgency_penalty = {"Patient": 1.8, "Normal": 4.2, "Urgent": 8.4}[urgency]
        strategy_adjustment = {"TWAP": 0.6, "VWAP": -0.2, "Liquidity Seeking": 1.4, "Manual Hedge": 2.1}[strategy]
        adverse_noise = float(rng.normal(0.0, 2.2))
        slippage_bps = round(spread_bps * 0.32 + urgency_penalty + strategy_adjustment + vol_1m_pct * 3.7 + adverse_noise, 2)
        slippage_bps = float(np.clip(slippage_bps, -2.0, 28.0))

        completion_rate = float(np.clip(rng.normal(97.2 if urgency != "Patient" else 93.8, 2.5), 84.0, 100.0))
        fill_minutes = float(np.clip(rng.normal(13 if urgency == "Urgent" else 26 if urgency == "Normal" else 44, 7.5), 4.0, 75.0))
        shares = int(round(base_notional / arrival_mid))
        filled_qty = int(round(shares * completion_rate / 100))
        avg_fill_price = arrival_mid * (1 + slippage_bps / 10_000) if side == "BUY" else arrival_mid * (1 - slippage_bps / 10_000)
        arrival_notional = arrival_mid * filled_qty
        realized_notional = avg_fill_price * filled_qty
        implementation_shortfall_usd = realized_notional - arrival_notional if side == "BUY" else arrival_notional - realized_notional

        benchmark_mid_5m = arrival_mid * (1 + rng.normal(0.0005, 0.004))
        benchmark_mid_30m = arrival_mid * (1 + rng.normal(0.0012, 0.006))
        shortfall_bps = round((implementation_shortfall_usd / max(arrival_notional, 1.0)) * 10_000, 2)

        pre_beta_usd = float(np.clip(rng.normal(0.0, base_notional * 0.52), -2_400_000.0, 2_400_000.0))
        hedge_basket = HEDGE_BASKETS[region][idx % len(HEDGE_BASKETS[region])]
        hedge_notional = float(np.clip(abs(pre_beta_usd) * rng.uniform(0.72, 1.08), 10_000.0, 2_800_000.0))
        beta_reduction_pct = float(np.clip(rng.normal(71 if urgency == "Urgent" else 78 if urgency == "Normal" else 83, 9.0), 42.0, 96.0))
        post_beta_usd = pre_beta_usd * (1 - beta_reduction_pct / 100)
        time_to_flat_min = float(np.clip(rng.normal(34 if urgency == "Patient" else 21 if urgency == "Normal" else 12, 5.0), 3.0, 60.0))
        residual_beta_ratio = abs(post_beta_usd) / max(abs(pre_beta_usd), 1.0)
        fill_quality_score = float(np.clip(100 - slippage_bps * 2.4 - residual_beta_ratio * 18 - (100 - completion_rate) * 0.9 + rng.normal(0, 2.5), 28.0, 96.0))

        rows.append(
            {
                "order_id": f"EXE{idx + 1:04d}",
                "trade_date": dates[idx % len(dates)],
                "symbol": symbol,
                "region": region,
                "sector": sector,
                "side": side,
                "urgency": urgency,
                "strategy": strategy,
                "venue": venue,
                "hedge_basket": hedge_basket,
                "arrival_mid": round(arrival_mid, 2),
                "avg_fill_price": round(float(avg_fill_price), 2),
                "benchmark_mid_5m": round(float(benchmark_mid_5m), 2),
                "benchmark_mid_30m": round(float(benchmark_mid_30m), 2),
                "order_qty": shares,
                "filled_qty": filled_qty,
                "completion_rate_pct": round(completion_rate, 2),
                "participation_rate_pct": round(participation, 2),
                "fill_minutes": round(fill_minutes, 2),
                "vol_1m_pct": round(vol_1m_pct, 2),
                "spread_bps": round(spread_bps, 2),
                "slippage_bps": slippage_bps,
                "shortfall_bps": shortfall_bps,
                "implementation_shortfall_usd": round(float(implementation_shortfall_usd), 2),
                "pre_beta_usd": round(pre_beta_usd, 2),
                "post_beta_usd": round(post_beta_usd, 2),
                "hedge_notional_usd": round(hedge_notional, 2),
                "beta_reduction_pct": round(beta_reduction_pct, 2),
                "time_to_flat_min": round(time_to_flat_min, 2),
                "fill_quality_score": round(fill_quality_score, 2),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "data" / "synthetic_execution_data.csv"
    dataset = build_execution_dataset()
    output.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output, index=False)
    print(f"Wrote {len(dataset)} rows to {output}")


if __name__ == "__main__":
    main()
