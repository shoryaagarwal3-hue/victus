"""Interactive Impact × Effort quadrant chart for Action Plan tab."""
from html import escape
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.ui_components import quadrant_badge
from frontend.ui_theme import TOKENS


def _parse_quadrant(quadrant: str) -> tuple[int, int]:
    quad_lower = quadrant.lower()
    impact = 2
    effort = 2
    if "high impact" in quad_lower:
        impact = 3
    elif "low impact" in quad_lower:
        impact = 1
    if "high effort" in quad_lower:
        effort = 3
    elif "low effort" in quad_lower:
        effort = 1
    return impact, effort


def _build_plot_data(action_items: list[dict[str, Any]]) -> pd.DataFrame:
    plot_data = []
    for it in action_items:
        impact_val, effort_val = _parse_quadrant(it.get("impact_effort_quadrant", "HIGH IMPACT / LOW EFFORT"))
        plot_data.append({
            "x": effort_val,
            "y": impact_val,
            "subject": it.get("affected_subject_or_skill", ""),
            "action": it.get("action_type", "Revision"),
            "reason": it.get("reason", ""),
            "horizon": it.get("horizon", "NOW"),
            "evidence": it.get("evidence", ""),
            "expected_impact": it.get("expected_impact", ""),
            "effort_label": it.get("effort", "MEDIUM"),
            "impact_label": "HIGH" if impact_val == 3 else ("LOW" if impact_val == 1 else "MEDIUM"),
        })
    return pd.DataFrame(plot_data)


def render_action_plan_quadrant(action_items: list[dict[str, Any]]) -> None:
    """Render an interactive impact-effort plot with evidence-backed item details."""
    plot_data = _build_plot_data(action_items)
    colors = {
        "NOW": TOKENS["danger"],
        "NEXT": TOKENS["info"],
        "LATER": TOKENS["muted"],
    }
    figure = go.Figure()
    for horizon in ("NOW", "NEXT", "LATER"):
        horizon_data = plot_data[plot_data["horizon"] == horizon]
        if horizon_data.empty:
            continue
        custom_data = horizon_data[
            ["action", "reason", "evidence", "expected_impact", "effort_label", "impact_label"]
        ].to_numpy()
        figure.add_trace(
            go.Scatter(
                x=horizon_data["x"],
                y=horizon_data["y"],
                mode="markers+text",
                name=horizon,
                text=horizon_data["subject"],
                textposition="top center",
                customdata=custom_data,
                marker={
                    "color": colors[horizon],
                    "size": 14,
                    "line": {"color": TOKENS["text"], "width": 1},
                },
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "%{customdata[0]} · %{customdata[5]} impact / %{customdata[4]} effort"
                    "<br>Horizon: " + horizon +
                    "<br>%{customdata[1]}<br>Evidence: %{customdata[2]}"
                    "<br>Expected impact: %{customdata[3]}<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor=TOKENS["background"],
        plot_bgcolor=TOKENS["background"],
        height=440,
        margin={"l": 50, "r": 25, "t": 25, "b": 55},
        xaxis={
            "title": "EFFORT",
            "range": [0.5, 3.5],
            "tickmode": "array",
            "tickvals": [1, 2, 3],
            "ticktext": ["LOW", "MEDIUM", "HIGH"],
            "gridcolor": TOKENS["border"],
        },
        yaxis={
            "title": "IMPACT",
            "range": [0.5, 3.5],
            "tickmode": "array",
            "tickvals": [1, 2, 3],
            "ticktext": ["LOW", "MEDIUM", "HIGH"],
            "gridcolor": TOKENS["border"],
        },
        legend={"title": "ACTION HORIZON", "orientation": "h", "y": 1.12},
        font={"color": TOKENS["text"]},
    )
    figure.add_vline(x=2, line_color=TOKENS["border"], line_dash="dot")
    figure.add_hline(y=2, line_color=TOKENS["border"], line_dash="dot")
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})

    for item in action_items:
        subject = escape(str(item.get("affected_subject_or_skill", "")))
        action = escape(str(item.get("action_type", "Revision")))
        horizon = escape(str(item.get("horizon", "NOW")))
        reason = escape(str(item.get("reason", "")))
        evidence = escape(str(item.get("evidence", "")))
        expected_impact = escape(str(item.get("expected_impact", "")))
        badge = quadrant_badge(
            str(item.get("impact_effort_quadrant", "HIGH IMPACT / LOW EFFORT"))
        )
        st.markdown(
            f'<div class="console-card">'
            f'<strong>{subject}</strong>: {action} [{horizon}] {badge}<br/>'
            f'<strong>Rationale:</strong> {reason}<br/>'
            f'<strong>Evidence:</strong> {evidence} · '
            f'<strong>Impact:</strong> {expected_impact}'
            f'</div>',
            unsafe_allow_html=True,
        )