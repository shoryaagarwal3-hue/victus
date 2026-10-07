import streamlit as st

TOKENS = {
    "background": "#0B0E14",
    "surface": "#141922",
    "surface_alt": "#10141D",
    "border": "#232937",
    "stable": "#3DDC97",
    "danger": "#FF5C5C",
    "warning": "#FFB86C",
    "info": "#8AC8FF",
    "purple": "#B28DFF",
    "text": "#E6E9EF",
    "muted": "#8A93A6",
}


def inject_css() -> None:
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    :root {{
        --bg:{TOKENS['background']};
        --surface:{TOKENS['surface']};
        --surface-alt:{TOKENS['surface_alt']};
        --border:{TOKENS['border']};
        --stable:{TOKENS['stable']};
        --danger:{TOKENS['danger']};
        --warning:{TOKENS['warning']};
        --info:{TOKENS['info']};
        --purple:{TOKENS['purple']};
        --text:{TOKENS['text']};
        --muted:{TOKENS['muted']};
    }}
    .stApp {{ background:var(--bg); color:var(--text); font-family:'Space Grotesk',sans-serif; }}
    [data-testid="stSidebar"] {{ background:var(--surface-alt); border-right:1px solid var(--border); }}
    [data-testid="stSidebar"] > div:first-child {{ padding-top:1.25rem; }}
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {{ color:var(--muted); }}
    .block-container {{ max-width:1520px; padding:2rem 3rem 4rem; }}
    h1, h2, h3, h4 {{ letter-spacing:-.025em; }}
    h1 {{ font-size:2rem !important; font-weight:600 !important; }}
    h2 {{ font-size:1.25rem !important; text-transform:uppercase; letter-spacing:.06em; }}
    h3 {{ font-size:1rem !important; letter-spacing:.04em; }}
    
    .console-header {{ border-bottom:1px solid var(--border); padding:0 0 1.25rem; margin-bottom:1.5rem; }}
    .console-eyebrow {{ color:var(--stable); font:600 .72rem 'IBM Plex Mono',monospace; letter-spacing:.14em; }}
    .console-subtitle {{ color:var(--muted); font-size:.9rem; margin-top:.35rem; }}
    
    .audit-strip {{
        display:flex;
        flex-wrap:wrap;
        gap:1.5rem;
        border:1px solid var(--border);
        background:var(--surface-alt);
        padding:.75rem 1.25rem;
        margin:1rem 0 1.5rem;
        font:500 .72rem 'IBM Plex Mono',monospace;
        text-transform:uppercase;
        letter-spacing:.06em;
    }}
    .audit-strip span {{ color:var(--muted); margin-right:0.25rem; }}
    .audit-strip strong {{ color:var(--text); font-weight:600; }}
    
    .executive-banner {{
        background: linear-gradient(90deg, rgba(20,25,34,0.98) 0%, rgba(16,20,29,0.95) 100%);
        border: 1px solid var(--border);
        border-left: 4px solid var(--info);
        padding: 1.25rem 1.5rem;
        margin: 1.25rem 0 1.75rem;
        border-radius: 2px;
    }}
    .executive-banner-title {{
        font: 700 .85rem 'IBM Plex Mono', monospace;
        letter-spacing: .12em;
        text-transform: uppercase;
        color: var(--info);
        margin-bottom: .5rem;
        display: flex;
        align-items: center;
        gap: .75rem;
    }}
    .executive-banner-text {{
        font-size: .95rem;
        line-height: 1.5;
        color: var(--text);
    }}
    
    .kpi {{
        background:var(--surface);
        border:1px solid var(--border);
        border-top:2px solid var(--kpi-color, var(--border));
        padding:18px 20px;
        border-radius:2px;
        min-height:104px;
    }}
    .kpi-label {{ color:var(--muted); font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; }}
    .kpi-value {{ font:600 2rem 'IBM Plex Mono',monospace; margin-top:8px; }}
    .mono {{ font-family:'IBM Plex Mono',monospace; }}
    
    .status-badge {{
        display: inline-block;
        padding: 2px 7px;
        font: 600 .68rem 'IBM Plex Mono', monospace;
        letter-spacing: .08em;
        text-transform: uppercase;
        border-radius: 2px;
        white-space: nowrap;
    }}
    .badge-verified {{ background: rgba(61,220,151,0.12); color: #3DDC97; border: 1px solid #3DDC97; }}
    .badge-derived {{ background: rgba(138,200,255,0.12); color: #8AC8FF; border: 1px solid #8AC8FF; }}
    .badge-ai {{ background: rgba(178,141,255,0.12); color: #B28DFF; border: 1px solid #B28DFF; }}
    .badge-insufficient {{ background: rgba(255,184,108,0.12); color: #FFB86C; border: 1px solid #FFB86C; }}
    .badge-simulated {{ background: rgba(138,147,166,0.12); color: #8A93A6; border: 1px solid #8A93A6; }}
    
    .badge-critical {{ background: rgba(255,92,92,0.18); color: #FF5C5C; border: 1px solid #FF5C5C; }}
    .badge-high {{ background: rgba(255,140,0,0.18); color: #FF8C00; border: 1px solid #FF8C00; }}
    .badge-medium {{ background: rgba(229,192,123,0.18); color: #E5C07B; border: 1px solid #E5C07B; }}
    .badge-low {{ background: rgba(61,220,151,0.18); color: #3DDC97; border: 1px solid #3DDC97; }}
    
    .console-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        border-radius: 2px;
    }}
    
    .section-rule {{ border-top:1px solid var(--border); margin:1.75rem 0 1rem; }}
    .stButton > button {{
        border-radius:2px;
        border:1px solid #394354;
        background:#1a202c;
        color:var(--text);
        font-family:'IBM Plex Mono',monospace;
        letter-spacing:.04em;
    }}
    .stButton > button:hover {{ border-color:var(--stable); color:var(--stable); }}
    [data-testid="stSidebar"] .stButton > button {{
        background:var(--danger);
        border-color:var(--danger);
        color:#130d10;
        font-weight:700;
    }}
    [data-testid="stTabs"] [role="tablist"] {{ border-bottom:1px solid var(--border); gap:1.25rem; }}
    [data-testid="stTabs"] button {{ color:var(--muted); font-size:.82rem; }}
    [data-testid="stTabs"] button[aria-selected="true"] {{ color:var(--text); }}
    [data-testid="stDataFrame"] {{ border:1px solid var(--border); }}
    [data-testid="stFileUploaderDropzone"] {{ background:var(--surface-alt); border:1px dashed #394354; }}
    .stAlert {{ border-radius:2px; }}
    </style>""", unsafe_allow_html=True)
