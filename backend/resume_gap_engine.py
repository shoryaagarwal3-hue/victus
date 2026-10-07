"""Skill Gap Analysis and Multi-Factor Prioritization Engine.
Ranks candidate skill deficits into HIGH, MEDIUM, and LOW priorities by fusing:
1. Role Requirement Tier (Required vs Preferred)
2. SAS Market Demand Frequency (Analytics & DataScience Jobs)
3. SAS JDS Career-Outcome Statistical Significance & Odds Ratios
4. Candidate Resume Evidence Depth (Absent vs Weakly Mentioned)
"""
from typing import Any
from .resume_models import (
    JobDescriptionRequirement,
    ParsedResume,
    PrioritySkillGap,
    ResumeMatchResult,
    SkillMatchDetail,
)
from .sas_models import StatisticalTestResult, ModelResult


def prioritize_skill_gaps(
    match_result: ResumeMatchResult,
    jds_stats: list[StatisticalTestResult] | None = None,
    jds_models: list[ModelResult] | None = None,
) -> list[PrioritySkillGap]:
    """Generate prioritized skill gaps with transparent, auditable justification."""
    gaps: list[PrioritySkillGap] = []
    
    # Pre-map JDS statistical results by variable name
    jds_stat_map = {t.variable_name: t for t in (jds_stats or [])}
    
    # Map skill names to JDS skill dimensions
    jds_skill_dim_map = {
        "Python": "coding_skills",
        "R": "coding_skills",
        "SQL": "coding_skills",
        "SAS": "coding_skills",
        "Machine Learning": "ai_and_ml_skills",
        "Deep Learning": "ai_and_ml_skills",
        "Scikit-Learn": "ai_and_ml_skills",
        "PyTorch": "ai_and_ml_skills",
        "TensorFlow": "ai_and_ml_skills",
        "Statistics & Probability": "maths-stats_skills",
        "Hypothesis Testing & A/B Testing": "maths-stats_skills",
        "Linear Algebra & Calculus": "maths-stats_skills",
        "Tableau": "dashboard_and_storytelling_skills",
        "Power BI": "dashboard_and_storytelling_skills",
        "Data Storytelling & Dashboards": "dashboard_and_storytelling_skills",
        "Excel & Advanced Analytics": "dashboard_and_storytelling_skills",
        "Apache Spark": "big_data_skills",
        "Hadoop & Hive": "big_data_skills",
        "Apache Kafka": "big_data_skills",
        "Databricks & Snowflake": "big_data_skills",
    }
    
    # Identify Logistic Regression Odds Ratios if available
    odds_ratio_map = {}
    if jds_models:
        lr = next((m for m in jds_models if "Logistic Regression" in m.model_name), None)
        if lr and lr.feature_importances:
            for fi in lr.feature_importances:
                if fi.odds_ratio:
                    odds_ratio_map[fi.feature_name] = fi.odds_ratio

    for item in match_result.all_skill_details:
        if item.status in ("PRESENT_DEMONSTRATED",):
            continue  # No gap
            
        is_missing_req = (item.status == "MISSING_REQUIRED")
        is_weak = (item.status == "PRESENT_MENTIONED")
        is_missing_pref = (item.status == "MISSING_PREFERRED")
        
        # Determine JDS career evidence
        jds_dim = jds_skill_dim_map.get(item.skill_name)
        jds_ev_text = "No direct dimension in JDS survey."
        jds_is_sig = False
        
        if jds_dim and jds_dim in jds_stat_map:
            st = jds_stat_map[jds_dim]
            or_val = odds_ratio_map.get(jds_dim, 1.0)
            or_str = f" (Odds Ratio: {or_val:.2f}x)" if or_val > 1.0 else ""
            jds_is_sig = st.is_statistically_significant
            sig_label = "Statistically significant" if jds_is_sig else "Observed baseline"
            jds_ev_text = f"{sig_label} driver of junior salary hike (Cohen's d={st.effect_size_value:.2f}, p={st.p_value:.4f}){or_str}."
            
        # Priority Decision Logic
        if is_missing_req or (is_weak and jds_is_sig):
            p_level = "HIGH"
            reason = f"Required competency for {match_result.target_role}; absent from or weakly evidenced in candidate resume."
            effort = "MEDIUM (3-6 Weeks)"
        elif is_missing_pref or is_weak:
            p_level = "MEDIUM"
            reason = f"Preferred industry skill with {item.market_demand_tier.lower()}; adds significant competitive edge."
            effort = "LOW (1-2 Weeks)"
        else:
            p_level = "LOW"
            reason = "Supporting skill; recommend building after core required proficiencies are verified."
            effort = "LOW (1-2 Weeks)"
            
        mkt_ev = f"{item.market_demand_tier} ({item.market_frequency:,} postings in 2024-2025 SAS market dataset)" if item.market_frequency > 0 else "Specialized toolchain; limited general market frequency."
        
        gaps.append(
            PrioritySkillGap(
                skill_name=item.skill_name,
                category=item.category,
                priority_level=p_level,
                primary_reason=reason,
                job_requirement_evidence=f"{item.importance_tier} skill for {match_result.target_role}",
                market_demand_evidence=mkt_ev,
                jds_career_outcome_evidence=jds_ev_text,
                current_resume_status="Weakly mentioned without project context" if is_weak else "Not detected in candidate profile",
                estimated_learning_effort=effort,
            )
        )
        
    # Sort: HIGH first, then MEDIUM, then LOW
    priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
    gaps.sort(key=lambda g: priority_order.get(g.priority_level, 4))
    return gaps
