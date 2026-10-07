"""Stitch Design System Presentation Layer Components.
Implements the 'VICTUS Analytics Command' Workstation Architecture:
High-density visual layouts, telemetry indicators, audit strips, and modular analytical panels.
"""
from html import escape
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st
from frontend.ui_theme import TOKENS


def render_shell_header(
    eyebrow: str = "VICTUS DATA SCIENCE CAREER INTELLIGENCE & DECISION-SUPPORT SYSTEM",
    title: str = "Evidence-Grounded Resume Analysis & Career Navigation",
    subtitle: str = "Deterministic extraction, 5-factor requirement matching, SAS market evidence integration, and actionable learning roadmaps.",
    telemetry_items: Optional[List[tuple[str, str]]] = None,
) -> None:
    """Render the master workstation header with telemetry strip."""
    telemetry_html = ""
    if telemetry_items:
        items_markup = "".join(
            f'<div class="audit-item"><span>{escape(k)}:</span> <strong>{escape(v)}</strong></div>'
            for k, v in telemetry_items
        )
        telemetry_html = f'<div class="audit-strip">{items_markup}</div>'
    
    st.markdown(
        f"""
        <div class="console-header animate-fade-in">
            <div class="console-eyebrow">{escape(eyebrow)}</div>
            <h1 style="margin: 0.25rem 0 0.4rem; color: {TOKENS['text']}; font-size: 1.85rem; font-weight: 700;">{escape(title)}</h1>
            <div class="console-subtitle">{escape(subtitle)}</div>
            {telemetry_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_active_profile_card(
    name: str,
    source_type: str = "uploaded",
    file_size_kb: Optional[float] = None,
    total_skills: int = 0,
    total_projects: int = 0,
    total_exp_years: float = 0.0,
    match_score: float = 0.0,
    core_gaps: int = 0,
) -> None:
    """Render the active resume command card with primary telemetry readouts."""
    is_upload = source_type == "uploaded"
    accent_color = TOKENS["stable"] if is_upload else TOKENS["info"]
    source_label = "USER RESUME UPLOAD" if is_upload else "DEMO BENCHMARK PROFILE"
    status_label = "VERIFIED & ANALYZED" if is_upload else "PRE-LOADED REFERENCE"
    
    size_str = f" | {file_size_kb:.1f} KB" if file_size_kb else ""
    
    st.markdown(
        f"""
        <div class="console-card animate-slide-up" style="border-left: 3px solid {accent_color}; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem; border-bottom: 1px solid {TOKENS['border']}; padding-bottom: 0.85rem; margin-bottom: 1rem;">
                <div>
                    <div style="color: {accent_color}; font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;">
                        [ACTIVE TARGET] {source_label}
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 700; color: {TOKENS['text']}; margin-top: 0.2rem; font-family: 'Space Grotesk', sans-serif;">
                        {escape(name)} <span style="font-family: 'Space Mono', monospace; font-size: 0.8rem; color: {TOKENS['muted']}; font-weight: 400;">{size_str}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <span class="status-badge badge-verified">{status_label}</span>
                    <span class="status-badge badge-derived">ENGINE: DETERMINISTIC V3.0</span>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem;">
                <div class="kpi" style="--kpi-color: {TOKENS['stable']};">
                    <div class="kpi-label">Resume Match Fit</div>
                    <div class="kpi-value" style="color: {TOKENS['stable']};">{match_score:.1f}%</div>
                </div>
                <div class="kpi" style="--kpi-color: {TOKENS['info']};">
                    <div class="kpi-label">Extracted Skills</div>
                    <div class="kpi-value" style="color: {TOKENS['info']};">{total_skills} <span style="font-size: 0.9rem; color: {TOKENS['muted']};">skills</span></div>
                </div>
                <div class="kpi" style="--kpi-color: {TOKENS['purple']};">
                    <div class="kpi-label">Evidenced Projects</div>
                    <div class="kpi-value" style="color: {TOKENS['purple']};">{total_projects} <span style="font-size: 0.9rem; color: {TOKENS['muted']};">projects</span></div>
                </div>
                <div class="kpi" style="--kpi-color: {TOKENS['warning']};">
                    <div class="kpi-label">Detected Tenure</div>
                    <div class="kpi-value" style="color: {TOKENS['warning']};">{total_exp_years:.1f} <span style="font-size: 0.9rem; color: {TOKENS['muted']};">yrs</span></div>
                </div>
                <div class="kpi" style="--kpi-color: {TOKENS['danger']};">
                    <div class="kpi-label">Priority Gaps</div>
                    <div class="kpi-value" style="color: {TOKENS['danger']};">{core_gaps} <span style="font-size: 0.9rem; color: {TOKENS['muted']};">deficits</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analytical_panel_header(title: str, subtitle: Optional[str] = None, badge_text: Optional[str] = None, badge_type: str = "DERIVED") -> None:
    """Render a standardized Stitch panel title with metadata."""
    badge_html = f'<span class="status-badge badge-{badge_type.lower()}">{escape(badge_text)}</span>' if badge_text else ""
    subtitle_html = f'<div style="color: {TOKENS["muted"]}; font-size: 0.88rem; margin-top: 0.25rem;">{escape(subtitle)}</div>' if subtitle else ""
    
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem; margin: 1.25rem 0 0.75rem; border-bottom: 1px solid {TOKENS['border']}; padding-bottom: 0.5rem;">
            <div>
                <div style="font-size: 1.15rem; font-weight: 700; color: {TOKENS['text']}; font-family: 'Space Grotesk', sans-serif;">{escape(title)}</div>
                {subtitle_html}
            </div>
            <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_priority_gap_card(
    skill_name: str,
    category: str,
    priority: str,
    primary_reason: str,
    job_req_evidence: str,
    market_evidence: str,
    jds_evidence: str,
    learning_effort: str,
) -> None:
    """Render a multi-dimensional gap diagnosis card with telemetry audit block."""
    priority_upper = priority.upper()
    badge_class = "badge-critical" if priority_upper == "HIGH" else ("badge-high" if priority_upper == "MEDIUM" else "badge-low")
    border_accent = TOKENS["danger"] if priority_upper == "HIGH" else (TOKENS["warning"] if priority_upper == "MEDIUM" else TOKENS["stable"])
    
    st.markdown(
        f"""
        <div class="console-card animate-card-hover" style="border-left: 3px solid {border_accent}; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; border-bottom: 1px solid {TOKENS['border']}; padding-bottom: 0.6rem; margin-bottom: 0.75rem;">
                <div style="font-size: 1.15rem; font-weight: 700; color: {TOKENS['text']}; font-family: 'Space Grotesk', sans-serif;">
                    {escape(skill_name)} <span style="font-family: 'Space Mono', monospace; font-size: 0.78rem; color: {TOKENS['muted']}; font-weight: 400;">({escape(category)})</span>
                </div>
                <div><span class="status-badge {badge_class}">PRIORITY: {escape(priority_upper)}</span></div>
            </div>
            
            <div style="font-size: 0.92rem; color: {TOKENS['text']}; margin-bottom: 0.85rem; line-height: 1.5;">
                <strong style="color: {TOKENS['border_focus']};">Diagnostic Rationale:</strong> {escape(primary_reason)}
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; background: {TOKENS['surface_alt']}; border: 1px solid {TOKENS['border']}; padding: 0.85rem 1rem; border-radius: 4px;">
                <div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['muted']}; font-weight: 700; text-transform: uppercase;">[ROLE SPECIFICATION]</div>
                    <div style="color: {TOKENS['text']}; font-size: 0.85rem; margin-top: 0.2rem;">{escape(job_req_evidence)}</div>
                </div>
                <div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['muted']}; font-weight: 700; text-transform: uppercase;">[SAS MARKET EVIDENCE]</div>
                    <div style="color: {TOKENS['text']}; font-size: 0.85rem; margin-top: 0.2rem;">{escape(market_evidence)}</div>
                </div>
                <div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['muted']}; font-weight: 700; text-transform: uppercase;">[JDS CAREER OUTCOME]</div>
                    <div style="color: {TOKENS['text']}; font-size: 0.85rem; margin-top: 0.2rem;">{escape(jds_evidence)}</div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem; font-family: 'Space Mono', monospace; font-size: 0.78rem; color: {TOKENS['stable']};">
                <span>ESTIMATED MASTERY EFFORT: <strong>{escape(learning_effort)}</strong></span>
                <span style="color: {TOKENS['muted']}; font-size: 0.7rem;">ACTIONABLE ROADMAP READY</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_resume_tip_card(
    section: str,
    finding: str,
    action: str,
    before_text: str,
    after_text: str,
) -> None:
    """Render a structured before/after resume transformation card."""
    st.markdown(
        f"""
        <div class="console-card animate-card-hover" style="border-left: 3px solid {TOKENS['info']}; margin-bottom: 1.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {TOKENS['border']}; padding-bottom: 0.5rem; margin-bottom: 0.75rem;">
                <div style="font-family: 'Space Mono', monospace; font-size: 0.82rem; font-weight: 700; color: {TOKENS['info']}; text-transform: uppercase;">
                    TARGET SECTION: {escape(section)}
                </div>
                <span class="status-badge badge-derived">AUDIT OPTIMIZATION</span>
            </div>
            
            <div style="color: {TOKENS['text']}; font-size: 0.92rem; margin-bottom: 0.4rem;">
                <strong>Observation:</strong> {escape(finding)}
            </div>
            <div style="color: {TOKENS['border_focus']}; font-size: 0.92rem; margin-bottom: 0.85rem;">
                <strong>Actionable Guidance:</strong> {escape(action)}
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.75rem; background: {TOKENS['surface_alt']}; padding: 0.85rem; border-radius: 4px; border: 1px solid {TOKENS['border']};">
                <div style="border-right: 1px solid {TOKENS['border']}; padding-right: 0.75rem;">
                    <div style="color: {TOKENS['danger']}; font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700;">[BEFORE - WEAK / VAGUE]</div>
                    <div style="color: {TOKENS['muted']}; font-size: 0.85rem; margin-top: 0.3rem; font-style: italic;">"{escape(before_text)}"</div>
                </div>
                <div style="padding-left: 0.25rem;">
                    <div style="color: {TOKENS['stable']}; font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700;">[AFTER - HIGH IMPACT & QUANTIFIED]</div>
                    <div style="color: {TOKENS['text']}; font-size: 0.85rem; margin-top: 0.3rem; font-weight: 600;">"{escape(after_text)}"</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_roadmap_phase_card(
    phase_num: int,
    skill_name: str,
    priority: str,
    why_it_matters: str,
    prerequisites: List[str],
    foundation_topics: List[str],
    intermediate_topics: List[str],
    advanced_topics: List[str],
    practice_tasks: List[str],
    mini_project: str,
    capstone_project: str,
    validation_milestone: str,
    resume_bullet_template: str,
) -> None:
    """Render a structured learning pathway phase matching Stitch workstation specifications."""
    priority_upper = priority.upper()
    accent = TOKENS["danger"] if priority_upper == "HIGH" else (TOKENS["warning"] if priority_upper == "MEDIUM" else TOKENS["stable"])
    badge_class = "badge-critical" if priority_upper == "HIGH" else ("badge-high" if priority_upper == "MEDIUM" else "badge-low")
    
    st.markdown(
        f"""
        <div class="console-card animate-slide-up" style="border-left: 3px solid {accent}; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; border-bottom: 1px solid {TOKENS['border']}; padding-bottom: 0.75rem; margin-bottom: 1rem;">
                <div>
                    <span style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: {accent}; font-weight: 700; text-transform: uppercase;">
                        PHASE {phase_num} • MASTERY PATHWAY
                    </span>
                    <div style="font-size: 1.25rem; font-weight: 700; color: {TOKENS['text']}; font-family: 'Space Grotesk', sans-serif; margin-top: 0.15rem;">
                        {escape(skill_name)}
                    </div>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <span class="status-badge {badge_class}">PRIORITY: {escape(priority_upper)}</span>
                    <span class="status-badge badge-derived">DETERMINISTIC CURRICULUM</span>
                </div>
            </div>
            
            <div style="font-size: 0.92rem; color: {TOKENS['text']}; margin-bottom: 0.85rem; line-height: 1.5;">
                <strong style="color: {TOKENS['border_focus']};">Market & Role Rationale:</strong> {escape(why_it_matters)}
            </div>
            
            <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: {TOKENS['muted']}; margin-bottom: 1rem;">
                PREREQUISITES: <strong style="color: {TOKENS['text']};">{escape(', '.join(prerequisites) if prerequisites else 'None')}</strong>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; margin-bottom: 1rem;">
                <div style="background: {TOKENS['surface_alt']}; border: 1px solid {TOKENS['border']}; padding: 0.85rem; border-radius: 4px;">
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['info']}; font-weight: 700;">STAGE 1: FOUNDATION</div>
                    <ul style="margin: 0.4rem 0 0 1rem; padding: 0; font-size: 0.82rem; color: {TOKENS['text']}; line-height: 1.4;">
                        {''.join(f'<li>{escape(t)}</li>' for t in foundation_topics)}
                    </ul>
                </div>
                <div style="background: {TOKENS['surface_alt']}; border: 1px solid {TOKENS['border']}; padding: 0.85rem; border-radius: 4px;">
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['warning']}; font-weight: 700;">STAGE 2: INTERMEDIATE</div>
                    <ul style="margin: 0.4rem 0 0 1rem; padding: 0; font-size: 0.82rem; color: {TOKENS['text']}; line-height: 1.4;">
                        {''.join(f'<li>{escape(t)}</li>' for t in intermediate_topics)}
                    </ul>
                </div>
                <div style="background: {TOKENS['surface_alt']}; border: 1px solid {TOKENS['border']}; padding: 0.85rem; border-radius: 4px;">
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['stable']}; font-weight: 700;">STAGE 3: PRODUCTION</div>
                    <ul style="margin: 0.4rem 0 0 1rem; padding: 0; font-size: 0.82rem; color: {TOKENS['text']}; line-height: 1.4;">
                        {''.join(f'<li>{escape(t)}</li>' for t in advanced_topics)}
                    </ul>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.75rem; background: {TOKENS['surface_alt']}; border: 1px solid {TOKENS['border']}; padding: 0.85rem 1rem; border-radius: 4px; margin-bottom: 0.85rem;">
                <div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['muted']}; font-weight: 700; text-transform: uppercase;">[GUIDED PRACTICE TASKS]</div>
                    <ul style="margin: 0.3rem 0 0.5rem 1rem; padding: 0; font-size: 0.82rem; color: {TOKENS['text']};">
                        {''.join(f'<li>{escape(pt)}</li>' for pt in practice_tasks)}
                    </ul>
                    <div style="font-size: 0.82rem; color: {TOKENS['muted']};"><strong style="color: {TOKENS['text']};">Mini-Project:</strong> {escape(mini_project)}</div>
                </div>
                <div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['muted']}; font-weight: 700; text-transform: uppercase;">[ENTERPRISE PORTFOLIO CAPSTONE]</div>
                    <div style="font-size: 0.85rem; color: {TOKENS['text']}; margin-top: 0.3rem; line-height: 1.4;"><strong>Project:</strong> {escape(capstone_project)}</div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: {TOKENS['stable']}; margin-top: 0.4rem;">
                        <strong>MILESTONE:</strong> {escape(validation_milestone)}
                    </div>
                </div>
            </div>
            
            <div>
                <div style="font-family: 'Space Mono', monospace; font-size: 0.7rem; color: {TOKENS['muted']}; font-weight: 700; text-transform: uppercase; margin-bottom: 0.35rem;">
                    [TARGET RESUME BULLET POINT TEMPLATE]
                </div>
                <div style="background: #0B0E14; border: 1px solid {TOKENS['border']}; padding: 0.65rem 0.85rem; border-radius: 4px; font-family: 'Space Mono', monospace; font-size: 0.8rem; color: {TOKENS['stable']};">
                    {escape(resume_bullet_template)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dataset_profile_card(name: str, file_type: str, row_count: int, col_count: int, quality_score: int) -> None:
    """Render a data quality profile card with precision telemetry."""
    score_color = TOKENS["stable"] if quality_score >= 95 else (TOKENS["warning"] if quality_score >= 80 else TOKENS["danger"])
    st.markdown(
        f"""
        <div class="console-card" style="border-left: 3px solid {score_color}; margin-bottom: 0.75rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <div style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: {TOKENS['muted']}; text-transform: uppercase;">
                        [OFFICIAL SAS DATASET] {escape(file_type)}
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 700; color: {TOKENS['text']}; font-family: 'Space Grotesk', sans-serif;">
                        {escape(name)}
                    </div>
                </div>
                <div style="display: flex; gap: 1rem; align-items: center; font-family: 'Space Mono', monospace; font-size: 0.8rem;">
                    <div><span style="color: {TOKENS['muted']};">ROWS:</span> <strong>{row_count:,}</strong></div>
                    <div><span style="color: {TOKENS['muted']};">COLS:</span> <strong>{col_count}</strong></div>
                    <div style="background: rgba(61, 220, 151, 0.1); border: 1px solid {score_color}; color: {score_color}; padding: 2px 8px; border-radius: 2px; font-weight: 700;">
                        SCORE: {quality_score}/100
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

