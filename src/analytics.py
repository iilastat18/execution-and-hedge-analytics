from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_execution_data(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["trade_date"])
    return frame.sort_values(["trade_date", "order_id"]).reset_index(drop=True)


def top_line_metrics(frame: pd.DataFrame) -> dict[str, float]:
    total_notional = float((frame["arrival_mid"] * frame["filled_qty"]).sum())
    total_shortfall = float(frame["implementation_shortfall_usd"].sum())
    hedge_reduction = float(frame["beta_reduction_pct"].mean())
    return {
        "orders": float(len(frame)),
        "total_notional": total_notional,
        "avg_slippage_bps": float(frame["slippage_bps"].mean()),
        "avg_shortfall_bps": float(frame["shortfall_bps"].mean()),
        "avg_completion_rate": float(frame["completion_rate_pct"].mean()),
        "avg_time_to_flat": float(frame["time_to_flat_min"].mean()),
        "avg_beta_reduction": hedge_reduction,
        "total_shortfall_usd": total_shortfall,
    }


def urgency_summary(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("urgency", as_index=False)
        .agg(
            orders=("order_id", "count"),
            avg_slippage_bps=("slippage_bps", "mean"),
            avg_shortfall_bps=("shortfall_bps", "mean"),
            avg_completion_rate=("completion_rate_pct", "mean"),
            avg_time_to_flat=("time_to_flat_min", "mean"),
            avg_beta_reduction=("beta_reduction_pct", "mean"),
        )
        .round(2)
    )


def hedge_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary = (
        frame.groupby(["region", "hedge_basket"], as_index=False)
        .agg(
            orders=("order_id", "count"),
            avg_slippage_bps=("slippage_bps", "mean"),
            avg_beta_reduction=("beta_reduction_pct", "mean"),
            avg_time_to_flat=("time_to_flat_min", "mean"),
            residual_beta_usd=("post_beta_usd", lambda values: np.abs(values).mean()),
        )
        .round(2)
    )
    summary["efficiency_score"] = (
        100
        - summary["avg_slippage_bps"] * 2.4
        - summary["avg_time_to_flat"] * 0.7
        - (summary["residual_beta_usd"] / 100_000) * 1.2
        + summary["avg_beta_reduction"] * 0.45
    ).clip(20, 95).round(2)
    return summary.sort_values("efficiency_score", ascending=False).reset_index(drop=True)


def venue_summary(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("venue", as_index=False)
        .agg(
            orders=("order_id", "count"),
            avg_slippage_bps=("slippage_bps", "mean"),
            avg_completion_rate=("completion_rate_pct", "mean"),
            avg_fill_quality=("fill_quality_score", "mean"),
        )
        .round(2)
        .sort_values("avg_fill_quality", ascending=False)
        .reset_index(drop=True)
    )


def worst_orders(frame: pd.DataFrame, n: int = 12) -> pd.DataFrame:
    cols = [
        "order_id",
        "trade_date",
        "symbol",
        "region",
        "side",
        "urgency",
        "strategy",
        "venue",
        "slippage_bps",
        "shortfall_bps",
        "completion_rate_pct",
        "beta_reduction_pct",
        "time_to_flat_min",
        "fill_quality_score",
    ]
    return frame.sort_values(["slippage_bps", "time_to_flat_min"], ascending=[False, False]).loc[:, cols].head(n).reset_index(drop=True)


def daily_summary(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("trade_date", as_index=False)
        .agg(
            avg_slippage_bps=("slippage_bps", "mean"),
            avg_beta_reduction=("beta_reduction_pct", "mean"),
            total_shortfall_usd=("implementation_shortfall_usd", "sum"),
        )
        .round(2)
    )


def execution_path(order_row: pd.Series, points: int = 12) -> pd.DataFrame:
    seed = sum(ord(ch) for ch in str(order_row["order_id"]))
    rng = np.random.default_rng(seed)
    minutes = np.linspace(0, float(order_row["fill_minutes"]), points)
    completion_curve = np.clip(np.cumsum(rng.uniform(0.05, 0.16, size=points)), 0, 1)
    completion_curve = completion_curve / completion_curve.max()

    arrival = float(order_row["arrival_mid"])
    avg_fill = float(order_row["avg_fill_price"])
    side = str(order_row["side"])
    drift = np.linspace(arrival, avg_fill, points)
    noise = rng.normal(0, max(arrival * 0.0025, 0.02), size=points)
    if side == "BUY":
        path = np.maximum(0.01, drift + np.abs(noise))
    else:
        path = np.maximum(0.01, drift - np.abs(noise))

    frame = pd.DataFrame(
        {
            "minute": minutes.round(1),
            "execution_price": path.round(2),
            "cum_completion_pct": (completion_curve * 100).round(1),
        }
    )
    return frame


def write_outputs(frame: pd.DataFrame, root: str | Path) -> None:
    root_path = Path(root)
    results_dir = root_path / "results"
    figures_dir = root_path / "figures"
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    urgency = urgency_summary(frame)
    hedges = hedge_summary(frame)
    venues = venue_summary(frame)
    daily = daily_summary(frame)
    worst = worst_orders(frame)
    metrics = top_line_metrics(frame)

    urgency.to_csv(results_dir / "urgency_summary.csv", index=False)
    hedges.to_csv(results_dir / "hedge_summary.csv", index=False)
    venues.to_csv(results_dir / "venue_summary.csv", index=False)
    daily.to_csv(results_dir / "daily_summary.csv", index=False)
    worst.to_csv(results_dir / "worst_orders.csv", index=False)
    pd.DataFrame([metrics]).to_csv(results_dir / "top_line_metrics.csv", index=False)
    (results_dir / "key_findings.md").write_text(build_findings_markdown(metrics, urgency, hedges), encoding="utf-8")

    _save_slippage_by_urgency(urgency, figures_dir / "slippage_by_urgency.png")
    _save_hedge_scatter(frame, figures_dir / "hedge_effectiveness_scatter.png")
    _save_daily_trends(daily, figures_dir / "daily_execution_trends.png")


def build_findings_markdown(metrics: dict[str, float], urgency: pd.DataFrame, hedges: pd.DataFrame) -> str:
    worst_urgency = urgency.sort_values("avg_slippage_bps", ascending=False).iloc[0]
    best_basket = hedges.sort_values("efficiency_score", ascending=False).iloc[0]
    return "\n".join(
        [
            "# Key Findings",
            "",
            f"- Average execution slippage across the sample is `{metrics['avg_slippage_bps']:.2f} bps`.",
            f"- Average hedge beta reduction is `{metrics['avg_beta_reduction']:.2f}%`, with flatten time averaging `{metrics['avg_time_to_flat']:.2f}` minutes.",
            f"- The most expensive urgency bucket is `{worst_urgency['urgency']}` at `{worst_urgency['avg_slippage_bps']:.2f} bps` average slippage.",
            f"- The most efficient hedge basket in the sample is `{best_basket['hedge_basket']}` with efficiency score `{best_basket['efficiency_score']:.2f}`.",
            f"- Total synthetic implementation shortfall across the sample is `${metrics['total_shortfall_usd']:,.0f}`.",
        ]
    )


def _save_slippage_by_urgency(frame: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.bar(frame["urgency"], frame["avg_slippage_bps"], color=["#7eb6ff", "#1f7a8c", "#d97706"])
    ax.set_title("Average Slippage By Urgency")
    ax.set_ylabel("Slippage (bps)")
    ax.grid(axis="y", alpha=0.18)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _save_hedge_scatter(frame: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    scatter = ax.scatter(
        frame["time_to_flat_min"],
        frame["beta_reduction_pct"],
        c=frame["slippage_bps"],
        cmap="viridis",
        alpha=0.78,
    )
    ax.set_title("Hedge Effectiveness")
    ax.set_xlabel("Time To Flat (min)")
    ax.set_ylabel("Beta Reduction (%)")
    fig.colorbar(scatter, ax=ax, label="Slippage (bps)")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _save_daily_trends(frame: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    ax.plot(frame["trade_date"], frame["avg_slippage_bps"], label="Avg Slippage (bps)", color="#244c7d", linewidth=2.1)
    ax.plot(frame["trade_date"], frame["avg_beta_reduction"], label="Avg Beta Reduction (%)", color="#0f766e", linewidth=2.1)
    ax.set_title("Daily Execution And Hedge Trends")
    ax.legend(frameon=False)
    ax.grid(alpha=0.18)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
