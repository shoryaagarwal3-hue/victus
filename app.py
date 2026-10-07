"""VICTUS DATA SCIENCE CAREER INTELLIGENCE & RESUME ANALYSIS SYSTEM
Production Decision-Support Engine for Resume Parsing, Skill Gap Prioritization,
Market Evidence Integration, Actionable Learning Roadmaps, and Audit Reporting.
Implements the Stitch 'VICTUS Analytics Command' Design System.
"""
import os
from pathlib import Path
import sys

# Ensure repository root is in sys.path for robust frontend imports
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime
import html
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from frontend.ui_theme import inject_css, TOKENS
from frontend.ui_components import kpi, badge, quadrant_badge, executive_banner
from frontend.stitch_view import (
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
from backend.resume_models import CompleteResumeAnalysisBundle, ParsedResume, JobDescriptionRequirement
from backend.resume_pipeline import analyze_candidate_resume, get_cached_sas_pipeline_result
from backend.job_matcher import STANDARD_ROLES
from backend.resume_report_exporter import generate_resume_audit_report_markdown, build_pdf_audit_report
from backend.sas_pipeline import run_full_sas_pipeline
from backend.sas_report_generator import generate_full_approach_note_markdown

# Page Configuration
st.set_page_config(
    page_title="VICTUS | SAS Career Intelligence & Resume Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# Sample Resumes for 1-click evaluation
SAMPLE_RESUME_JDS = """Alex Chen
alex.chen@email.com | (555) 349-8201 | github.com/alexchen-ds | linkedin.com/in/alexchends

SUMMARY
Aspiring Junior Data Scientist with strong foundations in Python, Machine Learning, and SQL. Experienced in developing supervised classification models and building analytical Tableau dashboards.

WORK EXPERIENCE
Data Analytics Intern | RetailMetrics Inc. (June 2023 – Dec 2023)
- Built automated SQL extraction scripts querying 250K+ transactional records to support weekly reporting.
- Developed interactive Tableau dashboards tracking store sales performance and inventory turnover.
- Performed exploratory data analysis in Python using Pandas and Seaborn to identify regional demand spikes.

PROJECTS
Customer Churn Prediction Engine
- Developed an end-to-end churn classification pipeline in Python using Scikit-Learn and XGBoost.
- Achieved 87.5% F1-score across 5-fold Stratified Cross-Validation on a dataset of 50K telco subscribers.
- Engineered 12 novel customer engagement features and visualized feature importances.

E-Commerce Conversion Analysis
- Designed SQL queries with CTEs and window functions to compute cohort retention rates and conversion funnels.
- Visualized user drop-off stages in Plotly and presented insights to product stakeholders.

TECHNICAL SKILLS
- Programming: Python, SQL, R, Bash
- Machine Learning: Scikit-Learn, XGBoost, Regression, Classification, K-Means Clustering
- Quantitative & Stats: Statistics & Probability, Hypothesis Testing, A/B Testing
- Visualization: Tableau, Matplotlib, Seaborn, Plotly, Excel & Advanced Analytics
- Tools & Cloud: Git & GitHub, PostgreSQL, Docker, Jupyter

EDUCATION
B.Tech in Computer Science & Engineering | State Technical University (2020 – 2024)
- Relevant Coursework: Machine Learning, Database Management Systems, Probability & Statistics, Data Structures
"""

SAMPLE_RESUME_ANALYST = """Sarah Jenkins
sarah.jenkins@analytics.org | (555) 782-1920 | linkedin.com/in/sarahjenkins-bi

PROFESSIONAL EXPERIENCE
Business Intelligence Analyst | Global Logistics Co. (2022 – Present)
- Engineered enterprise Power BI dashboards tracking supply chain KPIs across 14 international fulfillment hubs.
- Wrote advanced SQL queries with multi-table joins, subqueries, and window functions on PostgreSQL.
- Automated quarterly executive PowerPoint reporting using advanced Excel macros and Power Query.

PROJECTS
Supply Chain Delivery Optimization Dashboard
- Created interactive Power BI reporting suite with drill-down capabilities for warehouse throughput metrics.
- Formulated business recommendations that reduced transit delay reporting turnaround by 40%.

SKILLS
SQL, Power BI, Excel & Advanced Analytics, Data Storytelling & Dashboards, PostgreSQL, Tableau, Statistics & Probability

EDUCATION
B.S. in Business Analytics & Information Systems (2018 – 2022)
"""


def get_active_sas_data():
    """Retrieve verified SAS dataset results from cache."""
    return get_cached_sas_pipeline_result()


# -----------------------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------------------
render_sidebar_html(
    """
    <div style="padding:0 0 1rem; border-bottom:1px solid #232937; margin-bottom:1rem;">
        <div style="color:#3DDC97; font-family:'Space Mono',monospace; font-size:0.75rem; font-weight:700; letter-spacing:0.12em;">VICTUS ANALYTICS COMMAND</div>
        <div style="color:#E6E9EF; font-family:'Space Grotesk',sans-serif; font-size:1.15rem; font-weight:700; margin-top:0.25rem;">Career Intelligence Console</div>
    </div>
    """
)

nav_selection = st.sidebar.radio(
    "NAVIGATION",
    [
        "Resume Scanner & Parser",
        "Job Match & Requirement Fit",
        "Skill Gap & Prioritization",
        "Actionable Learning Roadmap",
        "Resume Improvement Tips",
        "SAS Market Intelligence",
        "JDS Technical Skill Analytics",
        "SDS Personality Analytics",
        "ML Benchmarks & Validation",
        "Audit Report & PDF Export",
        "Settings & System Health",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("**TARGET ROLE BENCHMARK**")
role_options = list(STANDARD_ROLES.keys()) + ["Custom Job Description"]
selected_role = st.sidebar.selectbox("Select Benchmark Role", role_options, index=0)

st.sidebar.markdown("---")
render_sidebar_html(
    """
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#8A93A6; line-height:1.7;">
        <div><b>ENGINE:</b> Deterministic V3.0</div>
        <div><b>DATASETS:</b> 4 Official SAS Files</div>
        <div><b>MARKET SCOPE:</b> 17,443 Postings</div>
        <div><b>AUTHENTICATION:</b> Offline / Local</div>
    </div>
    """
)

# Initialize Session State
if "active_resume_name" not in st.session_state:
    st.session_state["active_resume_name"] = "Alex Chen (Junior Data Scientist Sample)"
    st.session_state["active_resume_bytes"] = SAMPLE_RESUME_JDS.encode("utf-8")
    st.session_state["active_resume_source"] = "sample"

if "analysis_bundle" not in st.session_state:
    # Run default analysis on sample JDS resume so user sees instant results
    default_bundle = analyze_candidate_resume(
        file_bytes=st.session_state["active_resume_bytes"],
        file_name=st.session_state["active_resume_name"],
        target_role_title=selected_role if selected_role != "Custom Job Description" else "Junior Data Scientist",
    )
    st.session_state["analysis_bundle"] = default_bundle

bundle: CompleteResumeAnalysisBundle = st.session_state["analysis_bundle"]
sas_data = get_active_sas_data()

# -----------------------------------------------------------------------------------------
# GLOBAL HEADER
# -----------------------------------------------------------------------------------------
render_shell_header(
    eyebrow="VICTUS DATA SCIENCE CAREER INTELLIGENCE & DECISION-SUPPORT SYSTEM",
    title="Evidence-Grounded Resume Analysis & Career Navigation",
    subtitle="Deterministic extraction, 5-factor requirement matching, SAS market evidence integration, and actionable learning roadmaps.",
    telemetry_items=[
        ("ACTIVE TARGET ROLE", selected_role),
        ("ENGINE", "Deterministic V3.0"),
        ("DATASETS", "4 Official SAS Files (N=17,443)"),
        ("RUNTIME", "100% Deterministic Local"),
    ],
)



# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# PAGE 1: RESUME SCANNER & PARSER
# -----------------------------------------------------------------------------------------
if nav_selection == "Resume Scanner & Parser":
    render_analytical_panel_header(
        title="RESUME UPLOAD & DOCUMENT EXTRACTION WORKSTATION",
        subtitle="Deterministic extraction, 5-factor requirement matching, SAS market evidence integration, and actionable learning roadmaps.",
        badge_text="ENGINE: DETERMINISTIC V3.0",
        badge_type="VERIFIED",
    )
    
    # Active Resume Indicator Card
    active_name = st.session_state.get("active_resume_name", "Alex Chen (Junior Data Scientist Sample)")
    active_source = st.session_state.get("active_resume_source", "sample")
    active_bytes = st.session_state.get("active_resume_bytes")
    file_size_kb = round(len(active_bytes) / 1024, 1) if active_bytes else None
    
    res = bundle.parsed_resume
    render_active_profile_card(
        name=active_name,
        source_type=active_source,
        file_size_kb=file_size_kb,
        total_skills=len(res.extracted_skills),
        total_projects=len(res.projects),
        total_exp_years=res.total_experience_years,
        match_score=bundle.match_result.overall_match_score,
        core_gaps=bundle.match_result.missing_required_count,
    )

    # 2 Column layout: Left = Resume Upload & Samples | Right = Custom JD & Analysis Trigger
    col_upload, col_role = st.columns([3, 2], gap="large")
    
    with col_upload:
        render_html(
            f"""
            <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: {TOKENS['info']}; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem;">
                [WORKSTATION INPUT] CANDIDATE RESUME SOURCE
            </div>
            """
        )
        uploaded_file = st.file_uploader(
            "Upload Resume Document (PDF, DOCX, or TXT)",
            type=["pdf", "docx", "txt"],
            key="resume_uploader_widget",
            help="Deterministic parser extracts contact info, education, experience, projects, and skills without external LLM calls.",
        )
        
        if uploaded_file is not None:
            file_bytes_raw = uploaded_file.getvalue()
            f_size_kb = round(len(file_bytes_raw) / 1024, 1)
            
            render_html(
                f"""
                <div style="background: {TOKENS['surface_alt']}; border: 1px solid {TOKENS['stable']}; border-radius: 4px; padding: 0.85rem 1rem; margin-bottom: 0.75rem;">
                    <div style="color: {TOKENS['stable']}; font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700;">[FILE READY FOR ANALYSIS]</div>
                    <div style="color: {TOKENS['text']}; font-weight: 700; margin-top: 0.2rem; font-family: 'Space Grotesk', sans-serif;">{html.escape(uploaded_file.name)}</div>
                    <div style="color: {TOKENS['muted']}; font-family: 'Space Mono', monospace; font-size: 0.75rem; margin-top: 0.1rem;">Size: {f_size_kb} KB | Deterministic Parser Armed</div>
                </div>
                """
            )
            
            if st.button("LOAD & ANALYZE UPLOADED RESUME", type="primary", use_container_width=True, key="btn_load_real_resume"):
                try:
                    st.session_state["active_resume_bytes"] = file_bytes_raw
                    st.session_state["active_resume_name"] = uploaded_file.name
                    st.session_state["active_resume_source"] = "uploaded"
                    
                    target_title = selected_role if selected_role != "Custom Job Description" else "Junior Data Scientist"
                    custom_jd_val = st.session_state.get("custom_jd_input_text", "")
                    
                    st.session_state["analysis_bundle"] = analyze_candidate_resume(
                        file_bytes=file_bytes_raw,
                        file_name=uploaded_file.name,
                        target_role_title=target_title,
                        custom_jd_text=custom_jd_val,
                    )
                    st.success(f"Successfully loaded and analyzed: {uploaded_file.name}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Unable to load this resume: {exc}. Please try another file.")
        else:
            st.caption("Supported formats: **PDF** | **DOCX** | **TXT** (Deterministic parsing | 100% Offline Local)")
            
        render_html(
            f"""
            <div style="margin: 1.25rem 0 0.5rem; border-top: 1px solid {TOKENS['border']}; padding-top: 1rem;">
                <div style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: {TOKENS['muted']}; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">
                    [ONE-CLICK BENCHMARKS] REFERENCE DEMO PROFILES
                </div>
            </div>
            """
        )
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("Load JDS Sample Profile", use_container_width=True, key="btn_load_sample_jds"):
                sample_bytes = SAMPLE_RESUME_JDS.encode("utf-8")
                st.session_state["active_resume_bytes"] = sample_bytes
                st.session_state["active_resume_name"] = "Alex Chen (Junior Data Scientist Sample)"
                st.session_state["active_resume_source"] = "sample"
                
                target_title = selected_role if selected_role != "Custom Job Description" else "Junior Data Scientist"
                custom_jd_val = st.session_state.get("custom_jd_input_text", "")
                
                st.session_state["analysis_bundle"] = analyze_candidate_resume(
                    file_bytes=sample_bytes,
                    file_name="alex_chen_jds_sample.txt",
                    target_role_title=target_title,
                    custom_jd_text=custom_jd_val,
                )
                st.success("Loaded Junior Data Scientist sample profile.")
                st.rerun()
                
        with c_btn2:
            if st.button("Load Analyst Sample Profile", use_container_width=True, key="btn_load_sample_analyst"):
                sample_bytes = SAMPLE_RESUME_ANALYST.encode("utf-8")
                st.session_state["active_resume_bytes"] = sample_bytes
                st.session_state["active_resume_name"] = "Sarah Jenkins (Business Analytics Sample)"
                st.session_state["active_resume_source"] = "sample"
                
                target_title = selected_role if selected_role != "Custom Job Description" else "Data Analyst / Business Analytics Specialist"
                custom_jd_val = st.session_state.get("custom_jd_input_text", "")
                
                st.session_state["analysis_bundle"] = analyze_candidate_resume(
                    file_bytes=sample_bytes,
                    file_name="sarah_jenkins_analyst_sample.txt",
                    target_role_title=target_title,
                    custom_jd_text=custom_jd_val,
                )
                st.success("Loaded Business Analytics Specialist sample profile.")
                st.rerun()

    with col_role:
        render_html(
            f"""
            <div style="font-family: 'Space Mono', monospace; font-size: 0.75rem; color: {TOKENS['info']}; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem;">
                [TARGET SPECIFICATION] ROLE & JD BENCHMARK
            </div>
            """
        )
        st.markdown(f"**Target Role Benchmark:** `{selected_role}`")
        
        custom_jd = st.text_area(
            "Custom Job Description (Optional)",
            value=st.session_state.get("custom_jd_input_text", ""),
            placeholder="Paste custom job posting qualifications, responsibilities, and required tools to benchmark against...",
            height=135,
            key="custom_jd_textarea_widget",
        )
        st.session_state["custom_jd_input_text"] = custom_jd
        
        has_active_resume = st.session_state.get("active_resume_bytes") is not None
        btn_label = "RE-EVALUATE ACTIVE RESUME" if has_active_resume else "ANALYZE RESUME"
        
        if has_active_resume:
            if st.button(btn_label, type="primary", use_container_width=True, key="btn_analyze_action"):
                target_title = selected_role if selected_role != "Custom Job Description" else "Custom Role"
                try:
                    st.session_state["analysis_bundle"] = analyze_candidate_resume(
                        file_bytes=st.session_state["active_resume_bytes"],
                        file_name=st.session_state["active_resume_name"],
                        target_role_title=target_title,
                        custom_jd_text=custom_jd,
                    )
                    st.success(f"Analysis refreshed against {target_title}.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Analysis error: {exc}")
        else:
            st.info("Please upload and load a resume, or select a demo sample to enable analysis.")

    # Extracted Details Tabs
    render_analytical_panel_header(
        title=f"EXTRACTED RESUME EVIDENCE: {res.contact.name}",
        subtitle="Structured telemetry parsed deterministically from candidate resume.",
        badge_text="PARSER: DETERMINISTIC",
        badge_type="DERIVED",
    )
    
    t_skills, t_exp, t_proj, t_raw = st.tabs(["Extracted Skills", "Work Experience", "Projects Portfolio", "Raw Text View"])
    
    with t_skills:
        skill_df = pd.DataFrame([
            {
                "Canonical Skill": s.normalized_name,
                "Category": s.category,
                "Source Section": s.source_section,
                "Demonstrated in Projects/Work": "DEMONSTRATED" if s.is_demonstrated else "MENTIONED ONLY",
                "Context Snippet": s.context_snippet,
            }
            for s in res.extracted_skills
        ])
        st.dataframe(skill_df, use_container_width=True, hide_index=True)
        
    with t_exp:
        if res.experience:
            for exp in res.experience:
                render_html(
                    f"""
                    <div class="console-card" style="border-left: 3px solid {TOKENS['info']}; margin-bottom: 0.75rem;">
                        <div style="font-size: 1.05rem; font-weight: 700; color: {TOKENS['text']}; font-family: 'Space Grotesk', sans-serif;">
                            {html.escape(exp.role)} <span style="color: {TOKENS['muted']}; font-size: 0.85rem; font-weight: 400;">at {html.escape(exp.organization)} ({html.escape(exp.duration)})</span>
                        </div>
                        <ul style="margin: 0.5rem 0 0 1.25rem; padding: 0; font-size: 0.88rem; color: {TOKENS['text']}; line-height: 1.5;">
                            {''.join(f'<li>{html.escape(r)}</li>' for r in exp.responsibilities)}
                        </ul>
                    </div>
                    """
                )
        else:
            st.info("No employment history entries detected.")
            
    with t_proj:
        if res.projects:
            for p in res.projects:
                render_html(
                    f"""
                    <div class="console-card" style="border-left: 3px solid {TOKENS['purple']}; margin-bottom: 0.75rem;">
                        <div style="font-size: 1.05rem; font-weight: 700; color: {TOKENS['text']}; font-family: 'Space Grotesk', sans-serif;">
                            [PROJECT] {html.escape(p.title)}
                        </div>
                        <div style="color: {TOKENS['text']}; font-size: 0.88rem; margin: 0.4rem 0 0.5rem; line-height: 1.5;">
                            {html.escape(p.description)}
                        </div>
                        {'<div style="font-family: \'Space Mono\', monospace; font-size: 0.78rem; color: ' + TOKENS['stable'] + ';"><strong>Measurable Outcomes:</strong> ' + html.escape(', '.join(p.measurable_outcomes)) + '</div>' if p.measurable_outcomes else ''}
                    </div>
                    """
                )
        else:
            st.info("No projects detected.")
            
    with t_raw:
        st.text_area("Extracted Plain Text", res.raw_text, height=300)


# -----------------------------------------------------------------------------------------
# PAGE 2: JOB MATCH & REQUIREMENT FIT
# -----------------------------------------------------------------------------------------
elif nav_selection == "Job Match & Requirement Fit":
    match = bundle.match_result
    render_analytical_panel_header(
        title=f"RESUME-TO-ROLE 5-FACTOR MATCH: {match.target_role}",
        subtitle="Deterministic multi-factor scoring against industry qualifications and empirical SAS market demands.",
        badge_text="5-FACTOR WEIGHTED",
        badge_type="VERIFIED",
    )
    
    m_col1, m_col2 = st.columns([2, 3], gap="large")
    
    with m_col1:
        render_html(
            f"""
            <div class="console-card">
                <div style="font-family: 'Space Mono', monospace; font-size: 0.72rem; color: {TOKENS['muted']}; font-weight: 700; text-transform: uppercase;">
                    [COMPOSITE SCORING FORMULA]
                </div>
                <div style="font-size: 2.25rem; font-weight: 700; color: {TOKENS['stable']}; font-family: 'Space Mono', monospace; margin: 0.35rem 0 1rem;">
                    {match.overall_match_score:.1f}%
                </div>
                <div style="font-size: 0.85rem; color: {TOKENS['muted']}; line-height: 1.6; border-top: 1px solid {TOKENS['border']}; padding-top: 0.75rem;">
                    <div>Required Skills (50%): <strong style="color:{TOKENS['text']};">{match.required_skill_match_pct:.1f}%</strong></div>
                    <div>Preferred Skills (20%): <strong style="color:{TOKENS['text']};">{match.preferred_skill_match_pct:.1f}%</strong></div>
                    <div>Project Evidence (15%): <strong style="color:{TOKENS['text']};">{match.project_evidence_score:.1f}%</strong></div>
                    <div>Experience Fit (10%): <strong style="color:{TOKENS['text']};">{match.experience_fit_score:.1f}%</strong></div>
                    <div>Education Fit (5%): <strong style="color:{TOKENS['text']};">{match.education_fit_score:.1f}%</strong></div>
                </div>
            </div>
            """
        )

    with m_col2:
        # Radar Chart of 5 Fit Dimensions
        fig_radar = go.Figure()
        categories = ["Required Skills", "Preferred Skills", "Project Evidence", "Experience Fit", "Education Fit"]
        values = [
            match.required_skill_match_pct,
            match.preferred_skill_match_pct,
            match.project_evidence_score,
            match.experience_fit_score,
            match.education_fit_score,
        ]
        
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name="Candidate Fit",
            line_color=TOKENS["stable"],
            fillcolor="rgba(61, 220, 151, 0.18)",
        ))
        
        fig_radar.update_layout(
            polar=dict(
                bgcolor=TOKENS["surface_alt"],
                radialaxis=dict(visible=True, range=[0, 100], gridcolor=TOKENS["border"], tickfont=dict(family="Space Mono", color=TOKENS["muted"])),
                angularaxis=dict(gridcolor=TOKENS["border"], tickfont=dict(family="Space Grotesk", color=TOKENS["text"]))
            ),
            showlegend=False,
            margin=dict(l=40, r=40, t=30, b=30),
            paper_bgcolor=TOKENS["surface"],
            font_color=TOKENS["text"],
            height=320,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    render_analytical_panel_header(
        title="SKILL-BY-SKILL REQUIREMENT COMPARISON MATRIX",
        subtitle="Individual evaluation of every core requirement against candidate profile evidence.",
        badge_text="FULL AUDIT",
        badge_type="DERIVED",
    )
    
    match_table_data = []
    for d in match.all_skill_details:
        match_table_data.append({
            "Skill Name": d.skill_name,
            "Requirement Tier": d.importance_tier,
            "Candidate Status": "DEMONSTRATED" if d.status == "PRESENT_DEMONSTRATED" else ("MENTIONED ONLY" if d.status == "PRESENT_MENTIONED" else "MISSING"),
            "Market Demand Level": d.market_demand_tier,
            "SAS JDS Career Outcome Evidence": d.jds_association_note if d.jds_association_note else "Baseline competency",
            "Evidence Source": d.evidence_source,
        })
    st.dataframe(pd.DataFrame(match_table_data), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------------------
# PAGE 3: SKILL GAP & PRIORITIZATION
# -----------------------------------------------------------------------------------------
elif nav_selection == "Skill Gap & Prioritization":
    gaps = bundle.priority_gaps
    render_analytical_panel_header(
        title="MULTI-FACTOR SKILL GAP DIAGNOSTICS & PRIORITIZATION",
        subtitle="Gaps prioritized into High, Medium, and Low using SAS Market demand (N=17,443) and statistical JDS salary-hike significance.",
        badge_text=f"{len(gaps)} DEFICITS IDENTIFIED",
        badge_type="CRITICAL" if len(gaps) > 3 else "HIGH",
    )
    
    if not gaps:
        st.success("No critical skill gaps detected for this role specification.")
    else:
        for g in gaps:
            render_priority_gap_card(
                skill_name=g.skill_name,
                category=g.category,
                priority=g.priority_level,
                primary_reason=g.primary_reason,
                job_req_evidence=g.job_requirement_evidence,
                market_evidence=g.market_demand_evidence,
                jds_evidence=g.jds_career_outcome_evidence,
                learning_effort=g.estimated_learning_effort,
            )


# -----------------------------------------------------------------------------------------
# PAGE 4: ACTIONABLE LEARNING ROADMAP
# -----------------------------------------------------------------------------------------
elif nav_selection == "Actionable Learning Roadmap":
    roadmaps = bundle.learning_roadmaps
    render_analytical_panel_header(
        title="ACTIONABLE STEP-BY-STEP LEARNING ROADMAPS",
        subtitle="Structured learning pathways designed to close each identified deficit through Foundational Study -> Guided Practice -> Enterprise Portfolio Project -> Validation.",
        badge_text="DETERMINISTIC CURRICULUM",
        badge_type="DERIVED",
    )
    
    if not roadmaps:
        st.info("No skill gaps requiring roadmaps.")
    else:
        for idx, rm in enumerate(roadmaps):
            render_roadmap_phase_card(
                phase_num=idx + 1,
                skill_name=rm.skill_name,
                priority=rm.priority,
                why_it_matters=rm.why_it_matters,
                prerequisites=rm.prerequisites,
                foundation_topics=rm.foundation_topics,
                intermediate_topics=rm.intermediate_topics,
                advanced_topics=rm.advanced_topics,
                practice_tasks=rm.practice_tasks,
                mini_project=rm.mini_project,
                capstone_project=rm.main_portfolio_project,
                validation_milestone=rm.validation_milestone,
                resume_bullet_template=rm.resume_bullet_template,
            )


# -----------------------------------------------------------------------------------------
# PAGE 5: RESUME IMPROVEMENT TIPS
# -----------------------------------------------------------------------------------------
elif nav_selection == "Resume Improvement Tips":
    tips = bundle.resume_improvement_tips
    render_analytical_panel_header(
        title="CONCRETE RESUME BULLET & CONTENT OPTIMIZATION",
        subtitle="Actionable recommendations to enhance resume impact, evidence clarity, and ATS keyword visibility with quantified before/after examples.",
        badge_text="AUDIT OPTIMIZATION",
        badge_type="DERIVED",
    )
    
    for tip in tips:
        render_resume_tip_card(
            section=tip.section,
            finding=tip.finding_observation,
            action=tip.actionable_advice,
            before_text=tip.before_example,
            after_text=tip.after_example,
        )


# -----------------------------------------------------------------------------------------
# PAGE 6: SAS MARKET INTELLIGENCE
# -----------------------------------------------------------------------------------------
elif nav_selection == "SAS Market Intelligence":
    mkt = sas_data.market_summary
    render_analytical_panel_header(
        title="MACROECONOMIC ANALYTICS JOB MARKET LANDSCAPE",
        subtitle=f"Empirical distributions derived from {mkt.total_postings_analyzed:,} job postings across {mkt.unique_companies} leading organizations (Years 2024-2025).",
        badge_text=f"N={mkt.total_postings_analyzed:,} POSTINGS",
        badge_type="VERIFIED",
    )
    
    col_comp, col_skills = st.columns(2, gap="large")
    
    with col_comp:
        st.markdown("#### Top Hiring Organizations by Posting Volume")
        comp_df = pd.DataFrame(list(mkt.top_hiring_companies.items()), columns=["Company", "Posting Count"])
        fig_comp = px.bar(comp_df, x="Posting Count", y="Company", orientation="h", color_discrete_sequence=[TOKENS["info"]])
        fig_comp.update_layout(
            yaxis=dict(autorange="reversed", gridcolor=TOKENS["border"], tickfont=dict(family="Space Grotesk", color=TOKENS["text"])),
            xaxis=dict(gridcolor=TOKENS["border"], tickfont=dict(family="Space Mono", color=TOKENS["muted"])),
            paper_bgcolor=TOKENS["surface"],
            plot_bgcolor=TOKENS["surface_alt"],
            font_color=TOKENS["text"],
            height=350,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
    with col_skills:
        st.markdown("#### Most Frequent In-Demand Skill Mentions")
        skill_mkt_df = pd.DataFrame(list(mkt.top_key_skills.items())[:12], columns=["Skill", "Mentions"])
        fig_skill = px.bar(skill_mkt_df, x="Mentions", y="Skill", orientation="h", color_discrete_sequence=[TOKENS["stable"]])
        fig_skill.update_layout(
            yaxis=dict(autorange="reversed", gridcolor=TOKENS["border"], tickfont=dict(family="Space Grotesk", color=TOKENS["text"])),
            xaxis=dict(gridcolor=TOKENS["border"], tickfont=dict(family="Space Mono", color=TOKENS["muted"])),
            paper_bgcolor=TOKENS["surface"],
            plot_bgcolor=TOKENS["surface_alt"],
            font_color=TOKENS["text"],
            height=350,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_skill, use_container_width=True)

    col_loc, col_exp = st.columns(2, gap="large")
    with col_loc:
        st.markdown("#### Top Tech Employment Clusters")
        loc_df = pd.DataFrame(list(mkt.top_locations.items()), columns=["Location", "Postings"])
        fig_loc = px.pie(loc_df, names="Location", values="Postings", hole=0.45, color_discrete_sequence=[TOKENS["stable"], TOKENS["info"], TOKENS["purple"], TOKENS["warning"], "#94CCFF"])
        fig_loc.update_layout(
            paper_bgcolor=TOKENS["surface"],
            plot_bgcolor=TOKENS["surface"],
            font_color=TOKENS["text"],
            height=300,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_loc, use_container_width=True)
        
    with col_exp:
        st.markdown("#### Required Experience Distribution")
        exp_df = pd.DataFrame(list(mkt.experience_bands.items()), columns=["Experience Band", "Jobs"])
        fig_exp = px.bar(exp_df, x="Experience Band", y="Jobs", color_discrete_sequence=[TOKENS["purple"]])
        fig_exp.update_layout(
            yaxis=dict(gridcolor=TOKENS["border"], tickfont=dict(family="Space Mono", color=TOKENS["muted"])),
            xaxis=dict(gridcolor=TOKENS["border"], tickfont=dict(family="Space Grotesk", color=TOKENS["text"])),
            paper_bgcolor=TOKENS["surface"],
            plot_bgcolor=TOKENS["surface_alt"],
            font_color=TOKENS["text"],
            height=300,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_exp, use_container_width=True)


# -----------------------------------------------------------------------------------------
# PAGE 7: JDS TECHNICAL SKILL ANALYTICS
# -----------------------------------------------------------------------------------------
elif nav_selection == "JDS Technical Skill Analytics":
    render_analytical_panel_header(
        title="JUNIOR DATA SCIENTIST TECHNICAL SKILL & SALARY-HIKE ANALYTICS",
        subtitle="Empirical investigation of N=139 Junior Data Scientists evaluating statistical association between 5 technical skill dimensions (1-5 scale) and binary salary-hike outcomes.",
        badge_text="N=139 COHORT",
        badge_type="VERIFIED",
    )
    
    jds_stats = [t for t in sas_data.statistical_results if "salary_hike" in t.test_id]
    
    stat_table = []
    for s in jds_stats:
        stat_table.append({
            "Technical Skill Dimension": s.variable_name,
            "Low Hike Mean (0)": s.group_low_mean,
            "High Hike Mean (1)": s.group_high_mean,
            "Mean Lift": round(s.group_high_mean - s.group_low_mean, 2),
            "Mann-Whitney U": s.test_statistic,
            "p-value": f"{s.p_value:.4f}",
            "Cohen's d Effect Size": s.effect_size_value,
            "Statistical Significance": "SIGNIFICANT (p < 0.05)" if s.is_statistically_significant else "NOT SIGNIFICANT",
        })
    st.dataframe(pd.DataFrame(stat_table), use_container_width=True, hide_index=True)
    
    # Skill comparison bar chart
    fig_jds = go.Figure()
    fig_jds.add_trace(go.Bar(
        x=[s["Technical Skill Dimension"] for s in stat_table],
        y=[s["Low Hike Mean (0)"] for s in stat_table],
        name="Low Salary Hike (0)",
        marker_color=TOKENS["danger"],
    ))
    fig_jds.add_trace(go.Bar(
        x=[s["Technical Skill Dimension"] for s in stat_table],
        y=[s["High Hike Mean (1)"] for s in stat_table],
        name="High Salary Hike (1)",
        marker_color=TOKENS["stable"],
    ))
    fig_jds.update_layout(
        barmode="group",
        yaxis=dict(title="Average Skill Score (1 - 5)", gridcolor=TOKENS["border"], tickfont=dict(family="Space Mono", color=TOKENS["muted"])),
        xaxis=dict(gridcolor=TOKENS["border"], tickfont=dict(family="Space Grotesk", color=TOKENS["text"])),
        paper_bgcolor=TOKENS["surface"],
        plot_bgcolor=TOKENS["surface_alt"],
        font_color=TOKENS["text"],
        height=350,
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_jds, use_container_width=True)


# -----------------------------------------------------------------------------------------
# PAGE 8: SDS PERSONALITY ANALYTICS
# -----------------------------------------------------------------------------------------
elif nav_selection == "SDS Personality Analytics":
    render_analytical_panel_header(
        title="SENIOR DATA SCIENTIST PERSONALITY TRAIT ANALYTICS",
        subtitle="Investigation of N=161 Senior and Customer-Facing Data Scientists examining association between Big Five personality traits (OCEAN normalized 0-100) and organizational success outcomes.",
        badge_text="N=161 COHORT",
        badge_type="VERIFIED",
    )
    
    sds_stats = [t for t in sas_data.statistical_results if "success_classification" in t.test_id]
    
    sds_table = []
    for s in sds_stats:
        sds_table.append({
            "Big Five Trait Dimension": s.variable_name,
            "Low Success Mean (0)": s.group_low_mean,
            "High Success Mean (1)": s.group_high_mean,
            "Mann-Whitney U": s.test_statistic,
            "p-value": f"{s.p_value:.4f}",
            "Cohen's d": s.effect_size_value,
            "Statistical Significance": "SIGNIFICANT (p < 0.05)" if s.is_statistically_significant else "NOT SIGNIFICANT",
        })
    st.dataframe(pd.DataFrame(sds_table), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------------------
# PAGE 9: ML BENCHMARKS & VALIDATION
# -----------------------------------------------------------------------------------------
elif nav_selection == "ML Benchmarks & Validation":
    render_analytical_panel_header(
        title="SUPERVISED MACHINE LEARNING BENCHMARKS & VALIDATION",
        subtitle="Rigorous comparative evaluation of classification models predicting junior salary progression using Stratified 5-Fold Cross-Validation and odds-ratio explainability.",
        badge_text="5-FOLD CV RIGOR",
        badge_type="VERIFIED",
    )
    
    ml_rows = []
    for m in sas_data.jds_models:
        cv_acc = f"{m.cv_results.mean_accuracy*100:.1f}% (+/- {m.cv_results.std_accuracy*100:.1f}%)" if m.cv_results else "N/A"
        cv_auc = f"{m.cv_results.mean_roc_auc:.3f}" if m.cv_results and m.cv_results.mean_roc_auc else "N/A"
        ml_rows.append({
            "Model Architecture": m.model_name,
            "Train Accuracy": f"{m.train_metrics.accuracy*100:.1f}%",
            "Test Accuracy": f"{m.test_metrics.accuracy*100:.1f}%",
            "5-Fold CV Accuracy": cv_acc,
            "5-Fold CV ROC-AUC": cv_auc,
            "F1-Score": f"{m.test_metrics.f1_score:.3f}",
            "Balanced Accuracy": f"{m.test_metrics.balanced_accuracy*100:.1f}%",
        })
    st.dataframe(pd.DataFrame(ml_rows), use_container_width=True, hide_index=True)
    
    col_feat, col_cm = st.columns([3, 2], gap="large")
    lr_model = next((m for m in sas_data.jds_models if "Logistic Regression" in m.model_name), None)
    
    with col_feat:
        st.markdown("#### Logistic Regression Odds Ratios (Effect Size per +1 Skill Score)")
        if lr_model and lr_model.feature_importances:
            fi_df = pd.DataFrame([
                {
                    "Rank": fi.rank,
                    "Skill Feature": fi.feature_name,
                    "Odds Ratio": f"{fi.odds_ratio:.2f}x",
                    "95% Confidence Interval": f"[{fi.odds_ratio_ci_95[0]:.2f}, {fi.odds_ratio_ci_95[1]:.2f}]" if fi.odds_ratio_ci_95 else "",
                    "Standardized Coef": fi.importance_value,
                }
                for fi in lr_model.feature_importances
            ])
            st.dataframe(fi_df, use_container_width=True, hide_index=True)
            
    with col_cm:
        st.markdown("#### Test Confusion Matrix (N=28 Holdout)")
        if lr_model:
            cm = lr_model.confusion_matrix
            cm_df = pd.DataFrame(
                [[cm.true_negatives, cm.false_positives], [cm.false_negatives, cm.true_positives]],
                columns=["Pred: Low Hike (0)", "Pred: High Hike (1)"],
                index=["Actual: Low (0)", "Actual: High (1)"],
            )
            st.dataframe(cm_df, use_container_width=True)
            render_html(
                f"""
                <div style="font-family: 'Space Mono', monospace; font-size: 0.78rem; color: {TOKENS['muted']}; margin-top: 0.5rem;">
                    <div>Specificity: <strong style="color: {TOKENS['text']};">{cm.specificity*100:.1f}%</strong></div>
                    <div>NPV: <strong style="color: {TOKENS['text']};">{cm.negative_predictive_value*100:.1f}%</strong></div>
                </div>
                """
            )


# -----------------------------------------------------------------------------------------
# PAGE 10: AUDIT REPORT & PDF EXPORT
# -----------------------------------------------------------------------------------------
elif nav_selection == "Audit Report & PDF Export":
    render_analytical_panel_header(
        title="FORMAL AUDIT REPORT & DOCUMENT EXPORT",
        subtitle="Generate, preview, and download the complete 28-section auditable Career Intelligence Audit Report.",
        badge_text="28 SECTIONS",
        badge_type="VERIFIED",
    )
    
    c_rep1, c_rep2 = st.columns(2, gap="large")
    
    report_md = generate_resume_audit_report_markdown(bundle, sas_data)
    pdf_bytes = build_pdf_audit_report(bundle)
    
    with c_rep1:
        st.download_button(
            label="DOWNLOAD AUDIT REPORT (.MD)",
            data=report_md,
            file_name=f"SAS_Career_Audit_Report_{bundle.parsed_resume.contact.name.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
            type="primary",
        )
    with c_rep2:
        st.download_button(
            label="DOWNLOAD OFFICIAL PDF AUDIT REPORT (.PDF)",
            data=pdf_bytes,
            file_name=f"SAS_Career_Audit_Report_{bundle.parsed_resume.contact.name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        
    render_analytical_panel_header(
        title="LIVE AUDIT REPORT PREVIEW",
        subtitle="Complete Markdown rendering of the generated report.",
        badge_text="MARKDOWN PREVIEW",
        badge_type="DERIVED",
    )
    st.markdown(report_md)


# -----------------------------------------------------------------------------------------
# PAGE 11: SETTINGS & SYSTEM HEALTH
# -----------------------------------------------------------------------------------------
elif nav_selection == "Settings & System Health":
    render_analytical_panel_header(
        title="SYSTEM SETTINGS & DATASET VERIFICATION",
        subtitle="Official SAS dataset audit profiles, integrity checks, and cache controls.",
        badge_text="SYSTEM HEALTH: 100%",
        badge_type="VERIFIED",
    )
    
    st.markdown("#### Official SAS Datasets Verification")
    for name, prof in sas_data.data_quality_audit.dataset_profiles.items():
        render_dataset_profile_card(
            name=name,
            file_type=prof.file_type,
            row_count=prof.row_count,
            col_count=prof.column_count,
            quality_score=prof.data_quality_score,
        )
        
    render_analytical_panel_header(
        title="SESSION & CACHE MANAGEMENT",
        subtitle="Reset active session memory and restore default benchmark state.",
        badge_text="MAINTENANCE",
        badge_type="DERIVED",
    )
    if st.button("Reset Active Resume Analysis Session", type="secondary"):
        st.session_state.pop("analysis_bundle", None)
        st.success("Session reset. Reloading default baseline.")
        st.rerun()
