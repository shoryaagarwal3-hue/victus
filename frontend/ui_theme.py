"""Stitch Design System Theme & Stylesheet Definition.
Implements the 'VICTUS Analytics Command' visual language:
Technical Minimalist / Precision Workstation aesthetic with subtle CSS animations.
"""
from typing import Dict
import streamlit as st

TOKENS: Dict[str, str] = {
    "background": "#0B0E14",
    "surface": "#141922",
    "surface_alt": "#10141D",
    "border": "#232937",
    "border_focus": "#8AC8FF",
    "stable": "#3DDC97",
    "danger": "#FF5C5C",
    "warning": "#FFB86C",
    "info": "#8AC8FF",
    "purple": "#B28DFF",
    "text": "#E6E9EF",
    "muted": "#8A93A6",
}


def inject_css() -> None:
    """Inject the centralized Stitch design system CSS rules into the Streamlit DOM."""
    st.markdown(
        f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
    
    :root {{
        --bg: {TOKENS['background']};
        --surface: {TOKENS['surface']};
        --surface-alt: {TOKENS['surface_alt']};
        --border: {TOKENS['border']};
        --border-focus: {TOKENS['border_focus']};
        --stable: {TOKENS['stable']};
        --danger: {TOKENS['danger']};
        --warning: {TOKENS['warning']};
        --info: {TOKENS['info']};
        --purple: {TOKENS['purple']};
        --text: {TOKENS['text']};
        --muted: {TOKENS['muted']};
        
        --font-primary: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'Space Mono', monospace;
    }}
    
    /* Animation Keyframes */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes slideUp {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .animate-fade-in {{
        animation: fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    .animate-slide-up {{
        animation: slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    
    /* Base Application Canvas */
    .stApp {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: var(--font-primary) !important;
        -webkit-font-smoothing: antialiased;
    }}
    
    /* Sidebar Command Rail */
    [data-testid="stSidebar"] {{
        background-color: var(--surface-alt) !important;
        border-right: 1px solid var(--border) !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding: 1.5rem 1rem 2rem !important;
    }}
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stMarkdown {{
        color: var(--muted) !important;
    }}
    
    /* Layout Container & Grid Density */
    .block-container {{
        max-width: 1480px !important;
        padding: 2rem 2.5rem 4rem !important;
        animation: fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    
    /* Strict Technical Typography Hierarchy */
    h1, h2, h3, h4, h5, h6 {{
        font-family: var(--font-primary) !important;
        color: var(--text) !important;
        letter-spacing: -0.02em !important;
        font-weight: 600 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.75rem !important;
    }}
    h1 {{
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        line-height: 1.25 !important;
    }}
    h2 {{
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
    }}
    h3 {{
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }}
    h4 {{
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        color: var(--muted) !important;
    }}
    p, li, span {{
        color: var(--text);
        font-size: 0.92rem;
        line-height: 1.55;
    }}
    
    /* Monospace Utility Classes */
    .mono {{
        font-family: var(--font-mono) !important;
        font-variant-numeric: tabular-nums;
    }}
    
    /* Header Console Header */
    .console-header {{
        border-bottom: 1px solid var(--border);
        padding: 0 0 1.25rem;
        margin-bottom: 1.5rem;
    }}
    .console-eyebrow {{
        color: var(--stable);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }}
    .console-subtitle {{
        color: var(--muted);
        font-size: 0.92rem;
        margin-top: 0.35rem;
        max-width: 900px;
        line-height: 1.5;
    }}
    
    /* Telemetry Audit Strip */
    .audit-strip {{
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1.25rem;
        border: 1px solid var(--border);
        background: var(--surface-alt);
        padding: 0.65rem 1.1rem;
        margin: 1rem 0 0.5rem;
        border-radius: 4px;
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.04em;
    }}
    .audit-strip span {{
        color: var(--muted);
        margin-right: 0.25rem;
    }}
    .audit-strip strong {{
        color: var(--text);
        font-weight: 700;
    }}
    
    /* Technical Data Cards */
    .console-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 4px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.15s ease, transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.15s ease;
    }}
    .console-card:hover, .animate-card-hover:hover {{
        border-color: #2E384D;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    
    /* High-Density KPI Cards */
    .kpi {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-top: 2px solid var(--kpi-color, var(--border));
        padding: 1rem 1.15rem;
        border-radius: 4px;
        min-height: 98px;
        transition: transform 0.15s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.15s ease, box-shadow 0.15s ease;
    }}
    .kpi:hover {{
        transform: translateY(-2px);
        border-color: #2E384D;
        border-top-color: var(--kpi-color, var(--border));
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    .kpi-label {{
        color: var(--muted);
        font-family: var(--font-mono);
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .kpi-value {{
        font-family: var(--font-mono);
        font-size: 1.75rem;
        font-weight: 700;
        margin-top: 0.35rem;
        letter-spacing: -0.02em;
        font-variant-numeric: tabular-nums;
    }}
    
    /* Telemetry Badges & Status Chips */
    .status-badge {{
        display: inline-flex;
        align-items: center;
        padding: 3px 8px;
        font-family: var(--font-mono);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        border-radius: 2px;
        white-space: nowrap;
        line-height: 1;
    }}
    .badge-verified {{
        background: rgba(61, 220, 151, 0.10);
        color: #3DDC97;
        border: 1px solid rgba(61, 220, 151, 0.35);
    }}
    .badge-derived {{
        background: rgba(138, 200, 255, 0.10);
        color: #8AC8FF;
        border: 1px solid rgba(138, 200, 255, 0.35);
    }}
    .badge-ai {{
        background: rgba(178, 141, 255, 0.10);
        color: #B28DFF;
        border: 1px solid rgba(178, 141, 255, 0.35);
    }}
    .badge-insufficient {{
        background: rgba(255, 184, 108, 0.10);
        color: #FFB86C;
        border: 1px solid rgba(255, 184, 108, 0.35);
    }}
    .badge-simulated {{
        background: rgba(138, 147, 166, 0.10);
        color: #8A93A6;
        border: 1px solid rgba(138, 147, 166, 0.35);
    }}
    .badge-critical {{
        background: rgba(255, 92, 92, 0.12);
        color: #FF5C5C;
        border: 1px solid rgba(255, 92, 92, 0.35);
    }}
    .badge-high {{
        background: rgba(255, 184, 108, 0.12);
        color: #FFB86C;
        border: 1px solid rgba(255, 184, 108, 0.35);
    }}
    .badge-medium {{
        background: rgba(138, 200, 255, 0.12);
        color: #8AC8FF;
        border: 1px solid rgba(138, 200, 255, 0.35);
    }}
    .badge-low {{
        background: rgba(61, 220, 151, 0.12);
        color: #3DDC97;
        border: 1px solid rgba(61, 220, 151, 0.35);
    }}
    
    /* Interactive Button Styling */
    .stButton > button {{
        font-family: var(--font-primary) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid var(--border) !important;
        background-color: var(--surface) !important;
        color: var(--text) !important;
    }}
    .stButton > button:hover {{
        border-color: var(--border-focus) !important;
        color: var(--border-focus) !important;
        background-color: rgba(138, 200, 255, 0.04) !important;
        transform: translateY(-1px);
    }}
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Primary CTA Buttons */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"],
    button[kind="primaryFormSubmit"] {{
        background-color: var(--stable) !important;
        color: #0B0E14 !important;
        font-weight: 700 !important;
        border: 1px solid var(--stable) !important;
    }}
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {{
        background-color: #32C283 !important;
        border-color: #32C283 !important;
        color: #0B0E14 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(61, 220, 151, 0.2);
    }}
    
    /* Streamlit Form Inputs & Controls */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div[data-baseweb="select"] {{
        background-color: var(--surface-alt) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 4px !important;
        font-family: var(--font-primary) !important;
        font-size: 0.9rem !important;
        transition: border-color 0.15s ease;
    }}
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {{
        border-color: var(--border-focus) !important;
        box-shadow: none !important;
    }}
    
    /* Tabs Component */
    [data-testid="stTabs"] [role="tablist"] {{
        border-bottom: 1px solid var(--border) !important;
        gap: 1.5rem !important;
        padding-bottom: 0.25rem !important;
    }}
    [data-testid="stTabs"] button {{
        font-family: var(--font-primary) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: var(--muted) !important;
        padding: 0.5rem 0.25rem !important;
        border: none !important;
        background: transparent !important;
        transition: color 0.15s ease;
    }}
    [data-testid="stTabs"] button:hover {{
        color: var(--text) !important;
    }}
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--text) !important;
        border-bottom: 2px solid var(--stable) !important;
    }}
    
    /* DataFrame & Table Precision Styling */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--border) !important;
        border-radius: 4px !important;
        background-color: var(--surface) !important;
    }}
    
    /* File Uploader Dropzone */
    [data-testid="stFileUploaderDropzone"] {{
        background-color: var(--surface-alt) !important;
        border: 1px dashed #2A3346 !important;
        border-radius: 4px !important;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }}
    [data-testid="stFileUploaderDropzone"]:hover {{
        border-color: var(--stable) !important;
        background-color: rgba(61, 220, 151, 0.02) !important;
    }}
    
    /* Alert Boxes */
    .stAlert {{
        border-radius: 4px !important;
        border: 1px solid var(--border) !important;
        background-color: var(--surface) !important;
    }}
    
    /* Progress Bars */
    .stProgress > div > div > div > div {{
        background-color: var(--stable) !important;
    }}
    
    /* Radio Navigation in Sidebar */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        padding: 0.35rem 0.5rem !important;
        border-radius: 4px !important;
        transition: background-color 0.15s ease, color 0.15s ease;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
        background-color: rgba(255, 255, 255, 0.03) !important;
        color: var(--text) !important;
    }}
    
    /* Custom Scrollbar for Workstation Precision */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--bg);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #394354;
    }}
    </style>""",
        unsafe_allow_html=True,
    )
