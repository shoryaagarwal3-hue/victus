"""VICTUS DATA SCIENCE CAREER INTELLIGENCE & RESUME ANALYSIS SYSTEM
Production Decision-Support Engine for Resume Parsing, Skill Gap Prioritization,
Market Evidence Integration, Actionable Learning Roadmaps, and Audit Reporting.
Implements the Stitch 'VICTUS Analytics Command' Design System.
"""
from datetime import datetime
import html
import io
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from frontend.ui_theme import inject_css, TOKENS
from frontend.ui_components import kpi, badge, quadrant_badge, executive_banner
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
st.sidebar.markdown(
    """
    <div style="padding:0 0 1rem; border-bottom:1px solid #232937; margin-bottom:1rem;">
        <div style="color:#3DDC97; font-family:'Space Mono',monospace; font-size:0.75rem; font-weight:700; letter-spacing:0.12em;">VICTUS ANALYTICS COMMAND</div>
        <div style="color:#E6E9EF; font-family:'Space Grotesk',sans-serif; font-size:1.15rem; font-weight:700; margin-top:0.25rem;">Career Intelligence Console</div>
    </div>
    """,
    unsafe_allow_html=True,
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
st.sidebar.markdown(
    """
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#8A93A6; line-height:1.7;">
        <div><b>ENGINE:</b> Deterministic V3.0</div>
        <div><b>DATASETS:</b> 4 Official SAS Files</div>
        <div><b>MARKET SCOPE:</b> 17,443 Postings</div>
        <div><b>AUTHENTICATION:</b> Offline / Local</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------------------
# GLOBAL HEADER
# -----------------------------------------------------------------------------------------
st.markdown(
    """
    <div class="console-header">
        <div class="console-eyebrow">VICTUS DATA SCIENCE CAREER INTELLIGENCE & DECISION-SUPPORT SYSTEM</div>
        <h1 style="margin:0.25rem 0 0.5rem; color:#E6E9EF;">Evidence-Grounded Resume Analysis & Career Navigation</h1>
        <div class="console-subtitle">
            Deterministic extraction, 5-factor requirement matching, SAS market evidence integration, and actionable learning roadmaps.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
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
# PAGE 1: RESUME SCANNER & PARSER
# -----------------------------------------------------------------------------------------
if nav_selection == "Resume Scanner & Parser":
    st.markdown("### RESUME UPLOAD & DOCUMENT EXTRACTION")
    st.markdown(
        "Upload a candidate resume to extract structured technical skills, benchmark against industry roles, "
        "evaluate SAS market frequencies and career-outcome evidence, and generate an actionable learning roadmap."
    )
    
    # Active Resume Indicator Banner
    active_name = st.session_state.get("active_resume_name", "")
    active_source = st.session_state.get("active_resume_source", "")
    
    if active_name:
        if active_source == "uploaded":
            st.markdown(
                f"""
                <div style="background: rgba(61, 220, 151, 0.08); border: 1px solid #3DDC97; border-radius: 4px; padding: 0.85rem 1.25rem; margin: 0.75rem 0 1.25rem;">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <span style="color: #3DDC97; font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;">ACTIVE RESUME</span>
                            <div style="color: #E6E9EF; font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 700; margin-top: 0.15rem;">[LOADED] {html.escape(active_name)}</div>
                        </div>
                        <div style="background: #141922; border: 1px solid #3DDC97; color: #3DDC97; font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 2px;">
                            STATUS: VERIFIED & ANALYZED
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background: rgba(138, 200, 255, 0.08); border: 1px solid #8AC8FF; border-radius: 4px; padding: 0.85rem 1.25rem; margin: 0.75rem 0 1.25rem;">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                        <div>
                            <span style="color: #8AC8FF; font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;">ACTIVE DEMO SAMPLE</span>
                            <div style="color: #E6E9EF; font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 700; margin-top: 0.15rem;">[SAMPLE] {html.escape(active_name)}</div>
                        </div>
                        <div style="background: #141922; border: 1px solid #8AC8FF; color: #8AC8FF; font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 2px;">
                            DEMO BENCHMARK
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div style="background: rgba(255, 92, 92, 0.08); border: 1px solid #FF5C5C; border-radius: 4px; padding: 0.85rem 1.25rem; margin: 0.75rem 0 1.25rem;">
                <span style="color: #FF5C5C; font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700;">NO ACTIVE RESUME</span>
                <div style="color: #8A93A6; font-size: 0.95rem; margin-top: 0.15rem;">Please upload and load your resume below, or select a demo sample to begin.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2 Column layout: Left = Resume Upload & Samples | Right = Custom JD & Analysis Trigger
    col_upload, col_role = st.columns([3, 2], gap="large")
    
    with col_upload:
        st.markdown("#### CANDIDATE RESUME SOURCE")
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF, DOCX, or TXT)",
            type=["pdf", "docx", "txt"],
            key="resume_uploader_widget",
            help="Deterministic parser extracts contact info, education, experience, projects, and skills without external LLM calls.",
        )
        
        if uploaded_file is not None:
            file_bytes_raw = uploaded_file.getvalue()
            file_size_kb = round(len(file_bytes_raw) / 1024, 1)
            
            st.markdown(
                f"""
                <div style="background: #141922; border: 1px solid #232937; border-radius: 4px; padding: 0.85rem 1rem; margin-bottom: 0.75rem;">
                    <div style="color: #3DDC97; font-family: 'Space Mono', monospace; font-size: 0.72rem; font-weight: 700;">[FILE READY]</div>
                    <div style="color: #E6E9EF; font-weight: 600; margin-top: 0.2rem;">{html.escape(uploaded_file.name)}</div>
                    <div style="color: #8A93A6; font-family: 'Space Mono', monospace; font-size: 0.78rem; margin-top: 0.1rem;">Size: {file_size_kb} KB</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            if st.button("LOAD UPLOADED RESUME", type="primary", use_container_width=True, key="btn_load_real_resume"):
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
            st.caption("Supported formats: **PDF** | **DOCX** | **TXT** (Deterministic parsing | 100% Offline)")
            
        st.markdown("---")
        st.markdown("#### REFERENCE DEMO PROFILES")
        st.caption("Inspect the system immediately using pre-loaded reference profiles:")
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("Load Sample: Junior Data Scientist", use_container_width=True, key="btn_load_sample_jds"):
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
            if st.button("Load Sample: Business Analytics Specialist", use_container_width=True, key="btn_load_sample_analyst"):
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
        st.markdown("#### TARGET ROLE & JOB DESCRIPTION")
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
        btn_label = "ANALYZE RESUME" if st.session_state.get("analysis_bundle") is None else "RE-ANALYZE ACTIVE RESUME"
        
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
            if uploaded_file is not None:
                st.info("File selected. Click **LOAD UPLOADED RESUME** on the left to load before analyzing.")
            else:
                st.info("Please upload and load a resume, or select a demo sample to enable analysis.")

    st.markdown("---")
    
    # Overview of Extracted Profile
    res = bundle.parsed_resume
    st.markdown(f"#### EXTRACTED PROFILE: **{res.contact.name}**")
    
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi("Resume Match Score", bundle.match_result.overall_match_score, TOKENS["stable"], "%")
    with k2:
        kpi("Extracted Skills", float(len(res.extracted_skills)), TOKENS["info"], " skills")
    with k3:
        kpi("Projects Evidenced", float(len(res.projects)), TOKENS["purple"], " projects")
    with k4:
        kpi("Detected Experience", res.total_experience_years, TOKENS["warning"], " yrs")
    with k5:
        kpi("Missing Core Gaps", float(bundle.match_result.missing_required_count), TOKENS["danger"], " gaps")

    # Extracted Details Tabs
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
                st.markdown(f"**{exp.role}** at *{exp.organization}* ({exp.duration})")
                for r in exp.responsibilities:
                    st.markdown(f"- {r}")
        else:
            st.info("No employment history entries detected.")
            
    with t_proj:
        if res.projects:
            for p in res.projects:
                st.markdown(f"**[PROJECT] {p.title}**")
                st.markdown(f"{p.description}")
                if p.measurable_outcomes:
                    st.markdown(f"**Measurable Metrics:** `{', '.join(p.measurable_outcomes)}`")
                st.markdown("---")
        else:
            st.info("No projects detected.")
            
    with t_raw:
        st.text_area("Extracted Plain Text", res.raw_text, height=300)


# -----------------------------------------------------------------------------------------
# PAGE 2: JOB MATCH & REQUIREMENT FIT
# -----------------------------------------------------------------------------------------
elif nav_selection == "Job Match & Requirement Fit":
    match = bundle.match_result
    st.markdown(f"### RESUME-TO-ROLE MATCH ANALYSIS: **{match.target_role}**")
    
    m_col1, m_col2 = st.columns([2, 3])
    
    with m_col1:
        st.markdown("#### COMPOSITE MATCH BREAKDOWN")
        for dim, score in match.scoring_formula_breakdown.items():
            if "Composite" in dim:
                st.markdown(f"**{dim}**: <span style='color:#3DDC97; font-family:Space Mono; font-size:1.4rem; font-weight:700;'>{score:.1f}%</span>", unsafe_allow_html=True)
            else:
                st.progress(score / 100.0, text=f"{dim}: {score:.1f}%")
                
        st.markdown(
            """
            > **Auditable Scoring Standard**:
            > $$\text{Score} = 0.50 \times \text{Req} + 0.20 \times \text{Pref} + 0.15 \times \text{Proj} + 0.10 \times \text{Exp} + 0.05 \times \text{Edu}$$
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
            line_color="#3DDC97",
            fillcolor="rgba(61, 220, 151, 0.20)",
        ))
        
        fig_radar.update_layout(
            polar=dict(
                bgcolor="#10141D",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#232937", tickfont=dict(family="Space Mono", color="#8A93A6")),
                angularaxis=dict(gridcolor="#232937", tickfont=dict(family="Space Grotesk", color="#E6E9EF"))
            ),
            showlegend=False,
            margin=dict(l=40, r=40, t=30, b=30),
            paper_bgcolor="#141922",
            font_color="#E6E9EF",
            height=320,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")
    st.markdown("#### SKILL-BY-SKILL REQUIREMENT COMPARISON")
    
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
    st.markdown("### MULTI-FACTOR SKILL GAP PRIORITIZATION")
    st.markdown(
        "Gaps are prioritized into **HIGH**, **MEDIUM**, and **LOW** based on Role Requirements, "
        "SAS Market Postings (N=17,443), and JDS Statistical Salary-Hike Significance."
    )
    
    if not gaps:
        st.success("No critical skill gaps detected for this role specification.")
    else:
        for g in gaps:
            badge_type = "critical" if g.priority_level == "HIGH" else ("high" if g.priority_level == "MEDIUM" else "low")
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="border:1px solid #232937; background:#141922; border-radius:4px; padding:1.25rem; margin-bottom:1rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                            <div style="font-size:1.15rem; font-weight:700; color:#E6E9EF; font-family:'Space Grotesk',sans-serif;">
                                {g.skill_name} <span style="font-size:0.8rem; color:#8A93A6; font-family:'Space Mono',monospace;">({g.category})</span>
                            </div>
                            <div>{badge(f"PRIORITY: {g.priority_level}", badge_type)}</div>
                        </div>
                        <div style="margin-top:0.6rem; font-size:0.92rem; color:#E6E9EF;">
                            <b>Primary Justification:</b> {g.primary_reason}
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:1rem; margin-top:0.75rem; font-size:0.82rem; color:#8A93A6; border-top:1px solid #232937; padding-top:0.75rem;">
                            <div><b>Role Requirement:</b><br><span style="color:#E6E9EF;">{g.job_requirement_evidence}</span></div>
                            <div><b>Market Evidence:</b><br><span style="color:#E6E9EF;">{g.market_demand_evidence}</span></div>
                            <div><b>JDS Career Evidence:</b><br><span style="color:#E6E9EF;">{g.jds_career_outcome_evidence}</span></div>
                        </div>
                        <div style="margin-top:0.6rem; font-size:0.82rem; color:#3DDC97; font-family:'Space Mono',monospace;">
                            ESTIMATED LEARNING EFFORT: {g.estimated_learning_effort}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# -----------------------------------------------------------------------------------------
# PAGE 4: ACTIONABLE LEARNING ROADMAP
# -----------------------------------------------------------------------------------------
elif nav_selection == "Actionable Learning Roadmap":
    roadmaps = bundle.learning_roadmaps
    st.markdown("### ACTIONABLE STEP-BY-STEP LEARNING ROADMAPS")
    st.markdown(
        "Structured learning pathways designed to close each identified skill deficit through "
        "**Foundational Study -> Guided Practice -> Enterprise Portfolio Project -> Validation**."
    )
    
    if not roadmaps:
        st.info("No skill gaps requiring roadmaps.")
    else:
        for idx, rm in enumerate(roadmaps):
            with st.expander(f"Phase {idx+1}: Mastery Roadmap for {rm.skill_name} [{rm.priority} Priority]", expanded=(idx == 0)):
                st.markdown(f"**Why This Matters:** {rm.why_it_matters}")
                st.markdown(f"**Prerequisites:** `{', '.join(rm.prerequisites)}`")
                
                c_topics1, c_topics2, c_topics3 = st.columns(3)
                with c_topics1:
                    st.markdown("**1. Foundation Phase**")
                    for t in rm.foundation_topics:
                        st.markdown(f"- {t}")
                with c_topics2:
                    st.markdown("**2. Intermediate Phase**")
                    for t in rm.intermediate_topics:
                        st.markdown(f"- {t}")
                with c_topics3:
                    st.markdown("**3. Advanced / Production Phase**")
                    for t in rm.advanced_topics:
                        st.markdown(f"- {t}")
                        
                st.markdown("---")
                p_col1, p_col2 = st.columns(2)
                with p_col1:
                    st.markdown("##### Guided Practice Tasks")
                    for pt in rm.practice_tasks:
                        st.markdown(f"- {pt}")
                    st.markdown(f"**Mini-Project:** {rm.mini_project}")
                with p_col2:
                    st.markdown("##### Main Portfolio Capstone Project")
                    st.markdown(f"**Project Concept:** {rm.main_portfolio_project}")
                    st.markdown(f"**Validation Milestone:** `{rm.validation_milestone}`")
                    
                st.markdown("##### Target Resume Bullet Point Template")
                st.code(rm.resume_bullet_template, language="markdown")


# -----------------------------------------------------------------------------------------
# PAGE 5: RESUME IMPROVEMENT TIPS
# -----------------------------------------------------------------------------------------
elif nav_selection == "Resume Improvement Tips":
    tips = bundle.resume_improvement_tips
    st.markdown("### CONCRETE RESUME BULLET & CONTENT IMPROVEMENTS")
    st.markdown("Actionable recommendations to enhance resume impact, evidence clarity, and ATS keyword visibility.")
    
    for tip in tips:
        with st.container():
            st.markdown(
                f"""
                <div style="border:1px solid #232937; background:#141922; border-radius:4px; padding:1.25rem; margin-bottom:1.25rem;">
                    <div style="font-size:1.05rem; font-weight:700; color:#3DDC97; font-family:'Space Grotesk',sans-serif;">Section: {tip.section}</div>
                    <div style="color:#E6E9EF; margin-top:0.4rem;"><b>Observation:</b> {tip.finding_observation}</div>
                    <div style="color:#8AC8FF; margin-top:0.4rem;"><b>Actionable Advice:</b> {tip.actionable_advice}</div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:0.8rem; background:#10141D; padding:0.8rem; border-radius:4px; border:1px solid #232937;">
                        <div>
                            <span style="color:#FF5C5C; font-weight:700; font-family:'Space Mono',monospace; font-size:0.75rem;">[BEFORE - WEAK / VAGUE]</span>
                            <div style="color:#8A93A6; font-size:0.88rem; margin-top:0.3rem;">"{tip.before_example}"</div>
                        </div>
                        <div>
                            <span style="color:#3DDC97; font-weight:700; font-family:'Space Mono',monospace; font-size:0.75rem;">[AFTER - HIGH IMPACT / QUANTIFIED]</span>
                            <div style="color:#E6E9EF; font-size:0.88rem; margin-top:0.3rem;">"{tip.after_example}"</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# -----------------------------------------------------------------------------------------
# PAGE 6: SAS MARKET INTELLIGENCE
# -----------------------------------------------------------------------------------------
elif nav_selection == "SAS Market Intelligence":
    mkt = sas_data.market_summary
    st.markdown("### MACROECONOMIC ANALYTICS JOB MARKET LANDSCAPE")
    st.markdown(
        f"Empirical distributions derived from **{mkt.total_postings_analyzed:,} job postings** across "
        f"**{mkt.unique_companies} leading organizations** (Years 2024-2025)."
    )
    
    col_comp, col_skills = st.columns(2)
    
    with col_comp:
        st.markdown("#### Top Hiring Companies by Postings")
        comp_df = pd.DataFrame(list(mkt.top_hiring_companies.items()), columns=["Company", "Posting Count"])
        fig_comp = px.bar(comp_df, x="Posting Count", y="Company", orientation="h", color_discrete_sequence=["#8AC8FF"])
        fig_comp.update_layout(
            yaxis=dict(autorange="reversed", gridcolor="#232937", tickfont=dict(family="Space Grotesk")),
            xaxis=dict(gridcolor="#232937", tickfont=dict(family="Space Mono")),
            paper_bgcolor="#141922",
            plot_bgcolor="#10141D",
            font_color="#E6E9EF",
            height=350,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
    with col_skills:
        st.markdown("#### Most Frequent In-Demand Skill Mentions")
        skill_mkt_df = pd.DataFrame(list(mkt.top_key_skills.items())[:12], columns=["Skill", "Mentions"])
        fig_skill = px.bar(skill_mkt_df, x="Mentions", y="Skill", orientation="h", color_discrete_sequence=["#3DDC97"])
        fig_skill.update_layout(
            yaxis=dict(autorange="reversed", gridcolor="#232937", tickfont=dict(family="Space Grotesk")),
            xaxis=dict(gridcolor="#232937", tickfont=dict(family="Space Mono")),
            paper_bgcolor="#141922",
            plot_bgcolor="#10141D",
            font_color="#E6E9EF",
            height=350,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_skill, use_container_width=True)

    col_loc, col_exp = st.columns(2)
    with col_loc:
        st.markdown("#### Top Tech Employment Clusters")
        loc_df = pd.DataFrame(list(mkt.top_locations.items()), columns=["Location", "Postings"])
        fig_loc = px.pie(loc_df, names="Location", values="Postings", hole=0.45, color_discrete_sequence=["#3DDC97", "#8AC8FF", "#B28DFF", "#FFB86C", "#94CCFF"])
        fig_loc.update_layout(
            paper_bgcolor="#141922",
            plot_bgcolor="#141922",
            font_color="#E6E9EF",
            height=300,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_loc, use_container_width=True)
        
    with col_exp:
        st.markdown("#### Required Experience Distribution")
        exp_df = pd.DataFrame(list(mkt.experience_bands.items()), columns=["Experience Band", "Jobs"])
        fig_exp = px.bar(exp_df, x="Experience Band", y="Jobs", color_discrete_sequence=["#B28DFF"])
        fig_exp.update_layout(
            yaxis=dict(gridcolor="#232937", tickfont=dict(family="Space Mono")),
            xaxis=dict(gridcolor="#232937", tickfont=dict(family="Space Grotesk")),
            paper_bgcolor="#141922",
            plot_bgcolor="#10141D",
            font_color="#E6E9EF",
            height=300,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig_exp, use_container_width=True)


# -----------------------------------------------------------------------------------------
# PAGE 7: JDS TECHNICAL SKILL ANALYTICS
# -----------------------------------------------------------------------------------------
elif nav_selection == "JDS Technical Skill Analytics":
    st.markdown("### JUNIOR DATA SCIENTIST TECHNICAL SKILL & SALARY-HIKE ANALYTICS")
    st.markdown(
        "Empirical investigation of N=139 Junior Data Scientists evaluating statistical association "
        "between 5 technical skill dimensions (1-5 scale) and binary performance salary-hike outcomes."
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
        marker_color="#FF5C5C",
    ))
    fig_jds.add_trace(go.Bar(
        x=[s["Technical Skill Dimension"] for s in stat_table],
        y=[s["High Hike Mean (1)"] for s in stat_table],
        name="High Salary Hike (1)",
        marker_color="#3DDC97",
    ))
    fig_jds.update_layout(
        barmode="group",
        yaxis=dict(title="Average Skill Score (1 - 5)", gridcolor="#232937", tickfont=dict(family="Space Mono")),
        xaxis=dict(gridcolor="#232937", tickfont=dict(family="Space Grotesk")),
        paper_bgcolor="#141922",
        plot_bgcolor="#10141D",
        font_color="#E6E9EF",
        height=350,
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig_jds, use_container_width=True)


# -----------------------------------------------------------------------------------------
# PAGE 8: SDS PERSONALITY ANALYTICS
# -----------------------------------------------------------------------------------------
elif nav_selection == "SDS Personality Analytics":
    st.markdown("### SENIOR DATA SCIENTIST PERSONALITY TRAIT ANALYTICS")
    st.markdown(
        "Investigation of N=161 Senior and Customer-Facing Data Scientists examining the association "
        "between Big Five personality dimensions (OCEAN normalized 0-100) and organizational success outcomes."
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
    st.markdown("### SUPERVISED MACHINE LEARNING BENCHMARKS & VALIDATION")
    st.markdown(
        "Rigorous comparative evaluation of classification models predicting junior salary progression "
        "using **Stratified 5-Fold Cross-Validation** and odds-ratio explainability."
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
    
    col_feat, col_cm = st.columns([3, 2])
    lr_model = next((m for m in sas_data.jds_models if "Logistic Regression" in m.model_name), None)
    
    with col_feat:
        st.markdown("#### Logistic Regression Odds Ratios")
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
        st.markdown("#### Test Confusion Matrix")
        if lr_model:
            cm = lr_model.confusion_matrix
            cm_df = pd.DataFrame(
                [[cm.true_negatives, cm.false_positives], [cm.false_negatives, cm.true_positives]],
                columns=["Pred: Low Hike (0)", "Pred: High Hike (1)"],
                index=["Actual: Low (0)", "Actual: High (1)"],
            )
            st.dataframe(cm_df, use_container_width=True)
            st.markdown(f"**Specificity:** `{cm.specificity*100:.1f}%` | **Negative Predictive Value:** `{cm.negative_predictive_value*100:.1f}%`")


# -----------------------------------------------------------------------------------------
# PAGE 10: AUDIT REPORT & PDF EXPORT
# -----------------------------------------------------------------------------------------
elif nav_selection == "Audit Report & PDF Export":
    st.markdown("### FORMAL AUDIT REPORT & DOCUMENT EXPORT")
    st.markdown("Generate and download the complete 28-section Career Intelligence Audit Report.")
    
    c_rep1, c_rep2 = st.columns(2)
    
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
        
    st.markdown("---")
    st.markdown("#### Audit Report Live Preview")
    st.markdown(report_md)


# -----------------------------------------------------------------------------------------
# PAGE 11: SETTINGS & SYSTEM HEALTH
# -----------------------------------------------------------------------------------------
elif nav_selection == "Settings & System Health":
    st.markdown("### SYSTEM SETTINGS & DATA VERIFICATION")
    
    st.markdown("#### SAS Datasets Verification")
    for name, prof in sas_data.data_quality_audit.dataset_profiles.items():
        st.markdown(
            f"- **{name}** ({prof.file_type}): `{prof.row_count:,} rows`, `{prof.column_count} columns` | "
            f"Quality Score: **{prof.data_quality_score}/100**"
        )
        
    st.markdown("---")
    st.markdown("#### Session & Cache Management")
    if st.button("Reset Active Resume Analysis Session", type="secondary"):
        st.session_state.pop("analysis_bundle", None)
        st.success("Session reset. Reloading default baseline.")
        st.rerun()
