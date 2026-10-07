"""UI components and visual telemetry helpers implementing the Stitch design system."""
from html import escape
import streamlit as st


def kpi(label: str, value: float, color: str, unit: str = "%") -> None:
    """Render a high-density, technical KPI metric card."""
    safe_color = escape(color, quote=True)
    st.markdown(
        f'<div class="kpi" style="--kpi-color:{safe_color}">'
        f'<div class="kpi-label">{escape(label)}</div>'
        f'<div class="kpi-value" style="color:{safe_color}">{value:.1f}{escape(unit)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def badge(text: str, badge_type: str = "VERIFIED") -> str:
    """Return inline HTML for status and priority telemetry badges."""
    badge_type_lower = badge_type.lower()
    if "verified" in badge_type_lower:
        cls = "badge-verified"
    elif "derived" in badge_type_lower:
        cls = "badge-derived"
    elif "ai" in badge_type_lower or "assisted" in badge_type_lower or "ml" in badge_type_lower:
        cls = "badge-ai"
    elif "insufficient" in badge_type_lower:
        cls = "badge-insufficient"
    elif "simulated" in badge_type_lower or "demo" in badge_type_lower:
        cls = "badge-simulated"
    elif "critical" in badge_type_lower:
        cls = "badge-critical"
    elif "high" in badge_type_lower:
        cls = "badge-high"
    elif "medium" in badge_type_lower:
        cls = "badge-medium"
    elif "low" in badge_type_lower:
        cls = "badge-low"
    else:
        cls = "badge-derived"
    return f'<span class="status-badge {cls}">{escape(text)}</span>'


def render_badge(text: str, badge_type: str = "VERIFIED") -> None:
    """Render an inline telemetry badge directly into the Streamlit output."""
    st.markdown(badge(text, badge_type), unsafe_allow_html=True)


def quadrant_badge(quadrant: str) -> str:
    """Return inline HTML for quadrant classification badges."""
    quad_lower = quadrant.lower()
    if "high impact / low effort" in quad_lower:
        return '<span class="status-badge badge-critical">QUICK WIN | HIGH IMPACT</span>'
    elif "high impact / high effort" in quad_lower:
        return '<span class="status-badge badge-high">STRATEGIC | HIGH EFFORT</span>'
    elif "low impact / low effort" in quad_lower:
        return '<span class="status-badge badge-low">PATCH | LOW EFFORT</span>'
    else:
        return '<span class="status-badge badge-simulated">DEPRIORITIZE</span>'


def executive_banner(lead_title: str, text: str, badge_label: str = "ANALYTICAL SYNTHESIS") -> None:
    """Render a technical executive banner with telemetry badge."""
    st.markdown(
        f'<div class="executive-banner">'
        f'<div class="executive-banner-title">{escape(lead_title)} {badge(badge_label, "DERIVED")}</div>'
        f'<div class="executive-banner-text">{escape(text)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
