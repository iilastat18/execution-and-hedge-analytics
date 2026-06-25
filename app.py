from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.analytics import execution_path, hedge_summary, load_execution_data, top_line_metrics, urgency_summary, venue_summary, worst_orders
from src.generate_data import build_execution_dataset
from src.ui import apply_theme, close_surface, fmt_bps, fmt_money, fmt_pct, render_surface_header


st.set_page_config(page_title="Execution And Hedge Analytics", page_icon=":bar_chart:", layout="wide")
apply_theme()


@st.cache_data
def load_frame() -> pd.DataFrame:
    root = Path(__file__).resolve().parent
    data_path = root / "data" / "synthetic_execution_data.csv"
    if not data_path.exists():
        data_path.parent.mkdir(parents=True, exist_ok=True)
        build_execution_dataset().to_csv(data_path, index=False)
    return load_execution_data(data_path)


def themed(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#93a6b8",
            titleColor="#93a6b8",
            gridColor="rgba(117, 139, 163, 0.14)",
            domainColor="rgba(117, 139, 163, 0.22)",
            tickColor="rgba(117, 139, 163, 0.22)",
        )
        .configure_legend(labelColor="#edf3f8", titleColor="#93a6b8")
    )


frame = load_frame()

st.markdown(
    (
        "<div class='hero'>"
        "<div class='hero-kicker'>Portfolio Project 06</div>"
        "<div class='hero-title'>Execution And Hedge Analytics</div>"
        "<div class='hero-copy'>"
        "A post-trade analytics project focused on implementation shortfall, urgency, execution quality, and hedge effectiveness. "
        "It is designed to complement a trader-front-end system by showing what happens after the trade is sent."
        "</div>"
        "<div class='hero-pills'>"
        "<span class='pill'>execution analytics</span>"
        "<span class='pill'>hedge review</span>"
        "<span class='pill'>urgency analysis</span>"
        "<span class='pill'>synthetic trade data</span>"
        "<span class='pill'>post-trade workflow</span>"
        "</div>"
        "</div>"
    ),
    unsafe_allow_html=True,
)

filter_cols = st.columns([0.95, 0.95, 0.95, 0.8], gap="small")
with filter_cols[0]:
    region_filter = st.multiselect("Region", sorted(frame["region"].unique()), default=sorted(frame["region"].unique()))
with filter_cols[1]:
    urgency_filter = st.multiselect("Urgency", sorted(frame["urgency"].unique()), default=sorted(frame["urgency"].unique()))
with filter_cols[2]:
    basket_filter = st.multiselect("Hedge Basket", sorted(frame["hedge_basket"].unique()), default=sorted(frame["hedge_basket"].unique()))
with filter_cols[3]:
    min_completion = st.slider("Min Completion %", min_value=80, max_value=100, value=85, step=1)

filtered = frame.loc[
    frame["region"].isin(region_filter)
    & frame["urgency"].isin(urgency_filter)
    & frame["hedge_basket"].isin(basket_filter)
    & (frame["completion_rate_pct"] >= min_completion)
].reset_index(drop=True)

if filtered.empty:
    filtered = frame.copy()

metrics = top_line_metrics(filtered)
urgency = urgency_summary(filtered)
hedges = hedge_summary(filtered)
venues = venue_summary(filtered)
bad_orders = worst_orders(filtered, n=10)

metric_cols = st.columns(6)
metric_cols[0].metric("Orders", f"{int(metrics['orders'])}")
metric_cols[1].metric("Notional", fmt_money(metrics["total_notional"]))
metric_cols[2].metric("Avg Slippage", fmt_bps(metrics["avg_slippage_bps"]))
metric_cols[3].metric("Avg Completion", fmt_pct(metrics["avg_completion_rate"]))
metric_cols[4].metric("Avg Beta Reduction", fmt_pct(metrics["avg_beta_reduction"]))
metric_cols[5].metric("Total Shortfall", fmt_money(metrics["total_shortfall_usd"]))

left, right = st.columns([1.18, 0.82], gap="large")

with left:
    render_surface_header(
        "Urgency And Cost",
        "The main post-trade question: how much execution quality deteriorates as urgency increases, and whether completion improves enough to justify it.",
        label="Cost",
    )
    urgency_chart = (
        alt.Chart(urgency)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("urgency:N", title=None, sort=["Patient", "Normal", "Urgent"]),
            y=alt.Y("avg_slippage_bps:Q", title="Avg slippage (bps)"),
            color=alt.Color(
                "urgency:N",
                scale=alt.Scale(domain=["Patient", "Normal", "Urgent"], range=["#63b3ed", "#2dd4bf", "#f59e0b"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("urgency:N", title="Urgency"),
                alt.Tooltip("avg_slippage_bps:Q", title="Slippage", format=".2f"),
                alt.Tooltip("avg_completion_rate:Q", title="Completion", format=".2f"),
                alt.Tooltip("avg_time_to_flat:Q", title="Flat time", format=".2f"),
            ],
        )
        .properties(height=290)
    )
    st.altair_chart(themed(urgency_chart), use_container_width=True)
    st.dataframe(urgency, width="stretch", hide_index=True, height=190)
    close_surface()

    render_surface_header(
        "Worst Orders",
        "Use this board the way a desk would use a post-trade exception list: find the expensive fills, poor hedge follow-through, and slow-to-flatten names.",
        label="Exceptions",
    )
    st.dataframe(bad_orders, width="stretch", hide_index=True, height=300)
    close_surface()

with right:
    render_surface_header(
        "Hedge Effectiveness",
        "Hedge baskets are compared on slippage, time-to-flat, and residual beta after the hedge is done.",
        label="Hedge",
    )
    hedge_chart = (
        alt.Chart(filtered)
        .mark_circle(size=88, opacity=0.76)
        .encode(
            x=alt.X("time_to_flat_min:Q", title="Time to flat (min)"),
            y=alt.Y("beta_reduction_pct:Q", title="Beta reduction (%)"),
            color=alt.Color("slippage_bps:Q", title="Slippage", scale=alt.Scale(range=["#2dd4bf", "#f59e0b"])),
            tooltip=[
                alt.Tooltip("order_id:N", title="Order"),
                alt.Tooltip("hedge_basket:N", title="Basket"),
                alt.Tooltip("region:N", title="Region"),
                alt.Tooltip("slippage_bps:Q", title="Slippage", format=".2f"),
                alt.Tooltip("beta_reduction_pct:Q", title="Beta reduction", format=".2f"),
            ],
        )
        .properties(height=250)
    )
    st.altair_chart(themed(hedge_chart), use_container_width=True)
    st.dataframe(hedges, width="stretch", hide_index=True, height=220)
    close_surface()

    render_surface_header(
        "Venue Quality",
        "Venue-level comparison for execution quality, completion, and overall synthetic fill quality score.",
        label="Venue",
    )
    st.dataframe(venues, width="stretch", hide_index=True, height=190)
    close_surface()

selected_order = st.selectbox("Replay Order", filtered["order_id"].tolist(), index=0)
order_row = filtered.loc[filtered["order_id"] == selected_order].iloc[0]
path = execution_path(order_row)

render_surface_header(
    "Order Replay",
    "A compact replay of one order's execution path so the project feels closer to a real review workflow than a static report.",
    label="Replay",
)
st.markdown(
    (
        "<div class='detail-grid'>"
        f"<div class='detail-card'><div class='detail-label'>Order</div><div class='detail-value'>{order_row['order_id']} · {order_row['symbol']}</div></div>"
        f"<div class='detail-card'><div class='detail-label'>Urgency</div><div class='detail-value'>{order_row['urgency']} / {order_row['strategy']}</div></div>"
        f"<div class='detail-card'><div class='detail-label'>Execution</div><div class='detail-value'>{order_row['side']} {int(order_row['filled_qty']):,} @ {order_row['avg_fill_price']:.2f}</div></div>"
        f"<div class='detail-card'><div class='detail-label'>Hedge Outcome</div><div class='detail-value'>{order_row['hedge_basket']} · {order_row['beta_reduction_pct']:.2f}% beta reduction</div></div>"
        "</div>"
    ),
    unsafe_allow_html=True,
)
replay = (
    alt.Chart(path)
    .mark_line(strokeWidth=2.4, interpolate="monotone", color="#63b3ed")
    .encode(
        x=alt.X("minute:Q", title="Minute"),
        y=alt.Y("execution_price:Q", title="Execution price", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("minute:Q", title="Minute", format=".1f"),
            alt.Tooltip("execution_price:Q", title="Price", format=".2f"),
            alt.Tooltip("cum_completion_pct:Q", title="Completion", format=".1f"),
        ],
    )
    .properties(height=230)
)
completion = (
    alt.Chart(path)
    .mark_bar(color="#2dd4bf", opacity=0.42)
    .encode(
        x=alt.X("minute:Q", title="Minute"),
        y=alt.Y("cum_completion_pct:Q", title="Completion %"),
    )
    .properties(height=90)
)
st.altair_chart(themed(alt.vconcat(replay, completion).resolve_scale(x="shared")), use_container_width=True)
st.markdown(
    f"<div class='note'>This replay is synthetic, but it helps tell the execution story: arrival price `{order_row['arrival_mid']:.2f}`, average fill `{order_row['avg_fill_price']:.2f}`, slippage `{order_row['slippage_bps']:.2f} bps`, and flatten time `{order_row['time_to_flat_min']:.2f}` minutes.</div>",
    unsafe_allow_html=True,
)
close_surface()
