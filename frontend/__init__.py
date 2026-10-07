"""Streamlit presentation layer."""
from .ui_theme import inject_css, TOKENS
from .ui_components import kpi, badge, quadrant_badge, executive_banner
from .stitch_view import (
    render_html,
    render_sidebar_html,
    render_shell_header,
    render_active_profile_card,
    render_analytical_panel_header,
    render_priority_gap_card,
    render_resume_tip_card,
    render_roadmap_phase_card,
    render_dataset_profile_card,
)

__all__ = [
    "inject_css",
    "TOKENS",
    "kpi",
    "badge",
    "quadrant_badge",
    "executive_banner",
    "render_html",
    "render_sidebar_html",
    "render_shell_header",
    "render_active_profile_card",
    "render_analytical_panel_header",
    "render_priority_gap_card",
    "render_resume_tip_card",
    "render_roadmap_phase_card",
    "render_dataset_profile_card",
]
