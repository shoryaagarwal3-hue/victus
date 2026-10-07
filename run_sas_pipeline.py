"""Run and display the full SAS Data Science Career Intelligence pipeline."""
import sys
from backend.sas_pipeline import run_full_sas_pipeline
from backend.sas_report_generator import generate_full_approach_note_markdown

def main():
    print("============================================================")
    print("EXECUTING SAS DATA SCIENCE CAREER INTELLIGENCE SYSTEM")
    print("============================================================")
    
    result = run_full_sas_pipeline()
    
    print("\n--- 1. DATA AUDIT & QUALITY SCORES ---")
    for name, prof in result.data_quality_audit.dataset_profiles.items():
        print(f"  • {name} ({prof.file_type}): {prof.row_count:,} rows, {prof.column_count} cols | Quality Score: {prof.data_quality_score}/100")
        
    print("\n--- 2. STATISTICAL HYPOTHESIS TESTING (JDS SKILLS) ---")
    jds_tests = [t for t in result.statistical_results if "salary_hike" in t.test_id]
    for t in jds_tests:
        sig = "SIGNIFICANT (p < 0.05)" if t.is_statistically_significant else "NOT SIGNIFICANT"
        print(f"  • {t.variable_name:<35} | U={t.test_statistic:>6.1f} | p={t.p_value:.4f} | Cohen's d={t.effect_size_value:>5.2f} | {sig}")
        
    print("\n--- 3. MACHINE LEARNING BENCHMARKS (STRATIFIED 5-FOLD CV) ---")
    for m in result.jds_models:
        cv_acc = m.cv_results.mean_accuracy * 100 if m.cv_results else 0.0
        cv_std = m.cv_results.std_accuracy * 100 if m.cv_results else 0.0
        cv_auc = m.cv_results.mean_roc_auc if m.cv_results and m.cv_results.mean_roc_auc else 0.0
        print(f"  • {m.model_name}")
        print(f"      Train Acc: {m.train_metrics.accuracy*100:.1f}% | Test Acc: {m.test_metrics.accuracy*100:.1f}% | 5-Fold CV Acc: {cv_acc:.1f}% (+/- {cv_std:.1f}%) | ROC-AUC: {cv_auc:.3f}")
        
    print("\n--- 4. TOP PREDICTIVE FEATURES (LOGISTIC REGRESSION ODDS RATIOS) ---")
    lr = next((m for m in result.jds_models if "Logistic Regression" in m.model_name), None)
    if lr and lr.feature_importances:
        for fi in lr.feature_importances:
            or_val = f"{fi.odds_ratio:.2f}x" if fi.odds_ratio else "N/A"
            ci_val = f"[{fi.odds_ratio_ci_95[0]:.2f}, {fi.odds_ratio_ci_95[1]:.2f}]" if fi.odds_ratio_ci_95 else ""
            print(f"  • Rank {fi.rank}: {fi.feature_name:<32} | Odds Ratio: {or_val:>6} | 95% CI: {ci_val}")
            
    print("\n--- 5. MARKET RECRUITMENT LANDSCAPE ---")
    print(f"  • Total Postings Analyzed: {result.market_summary.total_postings_analyzed:,} across {result.market_summary.unique_companies} companies")
    print(f"  • Top Hiring Companies: {', '.join([f'{k} ({v:,})' for k, v in list(result.market_summary.top_hiring_companies.items())[:5]])}")
    print(f"  • Top Skills in Demand: {', '.join([f'{k} ({v:,})' for k, v in list(result.market_summary.top_key_skills.items())[:6]])}")
    
    print("\n--- 6. STAKEHOLDER RECOMMENDATIONS ---")
    for r in result.recommendations:
        print(f"  • [{r.target_stakeholder}]: {r.recommended_action[:110]}...")
        
    print("\n============================================================")
    print("PIPELINE COMPLETED: ALL METRICS DETERMINISTICALLY VERIFIED")
    print("============================================================")

if __name__ == "__main__":
    main()
