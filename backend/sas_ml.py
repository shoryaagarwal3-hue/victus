"""Supervised Machine Learning Service for SAS Datasets.
Implements:
1. Logistic Regression (interpretable baseline with Odds Ratios & 95% CIs)
2. Decision Tree Classifier (rule-based)
3. Random Forest Classifier (ensemble feature importance)
4. Stratified 5-Fold Cross-Validation
5. Confusion Matrix & Error Analysis (False Positives & False Negatives)
"""
from typing import Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_validate
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    balanced_accuracy_score,
    confusion_matrix,
    log_loss,
)

from .sas_models import (
    ClassificationMetrics,
    ConfusionMatrixData,
    CrossValidationResult,
    ErrorAnalysisCase,
    FeatureImportanceItem,
    ModelResult,
)


def _compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None = None) -> ClassificationMetrics:
    """Compute standard classification evaluation metrics."""
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    
    auc = None
    ll = None
    if y_prob is not None and len(np.unique(y_true)) > 1:
        try:
            auc = float(roc_auc_score(y_true, y_prob))
            ll = float(log_loss(y_true, y_prob))
        except Exception:
            pass
            
    return ClassificationMetrics(
        accuracy=round(acc, 4),
        precision=round(prec, 4),
        recall=round(rec, 4),
        f1_score=round(f1, 4),
        roc_auc=round(auc, 4) if auc is not None else None,
        log_loss_value=round(ll, 4) if ll is not None else None,
        balanced_accuracy=round(bal_acc, 4),
    )


def _compute_confusion_matrix_data(y_true: np.ndarray, y_pred: np.ndarray) -> ConfusionMatrixData:
    """Compute confusion matrix and derivative metrics (Specificity, NPV)."""
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])
    
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    
    return ConfusionMatrixData(
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        true_positives=tp,
        specificity=round(float(spec), 4),
        negative_predictive_value=round(float(npv), 4),
    )


def _perform_stratified_cv(model: Any, X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> CrossValidationResult:
    """Run Stratified K-Fold Cross Validation across standard classification metrics."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    acc_scores = []
    f1_scores = []
    auc_scores = []
    
    for train_idx, val_idx in skf.split(X, y):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        
        m = model.__class__(**model.get_params())
        m.fit(X_tr, y_tr)
        val_pred = m.predict(X_val)
        
        acc_scores.append(float(accuracy_score(y_val, val_pred)))
        f1_scores.append(float(f1_score(y_val, val_pred, zero_division=0)))
        
        if hasattr(m, "predict_proba") and len(np.unique(y_val)) > 1:
            try:
                val_prob = m.predict_proba(X_val)[:, 1]
                auc_scores.append(float(roc_auc_score(y_val, val_prob)))
            except Exception:
                pass
                
    return CrossValidationResult(
        cv_folds=n_splits,
        strategy="StratifiedKFold(n_splits=5, shuffle=True, random_state=42)",
        accuracy_scores=[round(s, 4) for s in acc_scores],
        f1_scores=[round(s, 4) for s in f1_scores],
        roc_auc_scores=[round(s, 4) for s in auc_scores],
        mean_accuracy=round(float(np.mean(acc_scores)), 4),
        std_accuracy=round(float(np.std(acc_scores)), 4),
        mean_f1=round(float(np.mean(f1_scores)), 4),
        std_f1=round(float(np.std(f1_scores)), 4),
        mean_roc_auc=round(float(np.mean(auc_scores)), 4) if auc_scores else None,
        std_roc_auc=round(float(np.std(auc_scores)), 4) if auc_scores else None,
    )


def train_and_evaluate_jds_models(jds_df: pd.DataFrame) -> list[ModelResult]:
    """Train, validate, and extract feature importances for JDS models."""
    feature_cols = [
        "big_data_skills",
        "maths-stats_skills",
        "coding_skills",
        "ai_and_ml_skills",
        "dashboard_and_storytelling_skills",
    ]
    target_col = "salary_hike_high_or_low"
    
    X = jds_df[feature_cols].values
    y = jds_df[target_col].values
    ids = jds_df["id"].values if "id" in jds_df.columns else np.arange(len(jds_df))
    
    # 80/20 Stratified train/test split
    X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
        X, y, ids, test_size=0.20, random_state=42, stratify=y
    )
    
    results = []
    
    # 1. Logistic Regression Baseline
    log_reg = LogisticRegression(random_state=42, max_iter=1000, C=1.0)
    log_reg.fit(X_train, y_train)
    
    y_train_pred = log_reg.predict(X_train)
    y_train_prob = log_reg.predict_proba(X_train)[:, 1]
    y_test_pred = log_reg.predict(X_test)
    y_test_prob = log_reg.predict_proba(X_test)[:, 1]
    
    lr_train_metrics = _compute_classification_metrics(y_train, y_train_pred, y_train_prob)
    lr_test_metrics = _compute_classification_metrics(y_test, y_test_pred, y_test_prob)
    lr_cm = _compute_confusion_matrix_data(y_test, y_test_pred)
    lr_cv = _perform_stratified_cv(log_reg, X, y, n_splits=5)
    
    # Calculate Odds Ratios: exp(beta)
    odds_ratios = np.exp(log_reg.coef_[0])
    coefs = log_reg.coef_[0]
    
    # Standard errors approximation for logistic coefficients
    # Using Hessian inverse approximation
    p_hat = y_train_prob * (1 - y_train_prob)
    W = np.diag(p_hat)
    X_design = np.hstack([np.ones((X_train.shape[0], 1)), X_train])
    try:
        cov_matrix = np.linalg.inv(X_design.T @ W @ X_design)
        se = np.sqrt(np.diag(cov_matrix)[1:])  # exclude intercept
    except Exception:
        se = np.ones_like(coefs) * 0.1
        
    lr_importances = []
    # Rank by absolute coefficient
    ranks = np.argsort(-np.abs(coefs))
    for rank_idx, feat_idx in enumerate(ranks):
        f_name = feature_cols[feat_idx]
        c_val = float(coefs[feat_idx])
        or_val = float(odds_ratios[feat_idx])
        se_val = float(se[feat_idx]) if feat_idx < len(se) else 0.1
        ci_low = float(np.exp(c_val - 1.96 * se_val))
        ci_high = float(np.exp(c_val + 1.96 * se_val))
        
        lr_importances.append(
            FeatureImportanceItem(
                feature_name=f_name,
                importance_metric="Odds Ratio (Logistic Regression)",
                importance_value=round(c_val, 4),
                std_error=round(se_val, 4),
                odds_ratio=round(or_val, 4),
                odds_ratio_ci_95=(round(ci_low, 3), round(ci_high, 3)),
                rank=rank_idx + 1,
                interpretation=(
                    f"A 1-unit increase in '{f_name}' is associated with an estimated "
                    f"{or_val:.2f}x odds of receiving a high salary hike (95% CI: [{ci_low:.2f}, {ci_high:.2f}])."
                ),
            )
        )
        
    # Error Analysis for test set
    lr_errors = []
    for i, (actual, pred, prob, rec_id) in enumerate(zip(y_test, y_test_pred, y_test_prob, ids_test)):
        if actual != pred:
            err_type = "FALSE_POSITIVE" if pred == 1 else "FALSE_NEGATIVE"
            profile = {feature_cols[j]: float(X_test[i, j]) for j in range(len(feature_cols))}
            factors = (
                f"Predicted {prob:.2f} probability for high hike. "
                f"Candidate profile has coding={profile.get('coding_skills', 0):.1f}, "
                f"maths={profile.get('maths-stats_skills', 0):.1f}, ai_ml={profile.get('ai_and_ml_skills', 0):.1f}."
            )
            lr_errors.append(
                ErrorAnalysisCase(
                    record_id=int(rec_id),
                    true_label=int(actual),
                    predicted_label=int(pred),
                    predicted_probability=round(float(prob), 4),
                    error_type=err_type,
                    skill_profile=profile,
                    contributing_factors=factors,
                )
            )
            
    results.append(
        ModelResult(
            model_name="Logistic Regression (Interpretable Baseline)",
            target_variable=target_col,
            features_used=feature_cols,
            train_size=len(X_train),
            test_size=len(X_test),
            train_metrics=lr_train_metrics,
            test_metrics=lr_test_metrics,
            cv_results=lr_cv,
            confusion_matrix=lr_cm,
            feature_importances=lr_importances,
            error_analysis=lr_errors,
            model_stability_notes=(
                f"5-Fold CV Mean Accuracy: {lr_cv.mean_accuracy*100:.1f}% (+/- {lr_cv.std_accuracy*100:.1f}%). "
                f"Mean ROC-AUC: {lr_cv.mean_roc_auc if lr_cv.mean_roc_auc else 0.0:.3f}."
            ),
            hyperparameters={"C": 1.0, "solver": "lbfgs", "random_state": 42},
        )
    )
    
    # 2. Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42, min_samples_leaf=2)
    rf.fit(X_train, y_train)
    
    rf_train_pred = rf.predict(X_train)
    rf_train_prob = rf.predict_proba(X_train)[:, 1]
    rf_test_pred = rf.predict(X_test)
    rf_test_prob = rf.predict_proba(X_test)[:, 1]
    
    rf_train_metrics = _compute_classification_metrics(y_train, rf_train_pred, rf_train_prob)
    rf_test_metrics = _compute_classification_metrics(y_test, rf_test_pred, rf_test_prob)
    rf_cm = _compute_confusion_matrix_data(y_test, rf_test_pred)
    rf_cv = _perform_stratified_cv(rf, X, y, n_splits=5)
    
    rf_importances = []
    rf_ranks = np.argsort(-rf.feature_importances_)
    for rank_idx, feat_idx in enumerate(rf_ranks):
        f_name = feature_cols[feat_idx]
        imp_val = float(rf.feature_importances_[feat_idx])
        rf_importances.append(
            FeatureImportanceItem(
                feature_name=f_name,
                importance_metric="Gini Importance (Random Forest)",
                importance_value=round(imp_val, 4),
                rank=rank_idx + 1,
                interpretation=f"Contributes {imp_val*100:.1f}% of total Gini impurity reduction across 100 decision trees.",
            )
        )
        
    results.append(
        ModelResult(
            model_name="Random Forest Classifier (Ensemble)",
            target_variable=target_col,
            features_used=feature_cols,
            train_size=len(X_train),
            test_size=len(X_test),
            train_metrics=rf_train_metrics,
            test_metrics=rf_test_metrics,
            cv_results=rf_cv,
            confusion_matrix=rf_cm,
            feature_importances=rf_importances,
            error_analysis=[],
            model_stability_notes=(
                f"5-Fold CV Mean Accuracy: {rf_cv.mean_accuracy*100:.1f}% (+/- {rf_cv.std_accuracy*100:.1f}%). "
                f"Mean F1: {rf_cv.mean_f1:.3f}."
            ),
            hyperparameters={"n_estimators": 100, "max_depth": 3, "min_samples_leaf": 2, "random_state": 42},
        )
    )
    
    # 3. Decision Tree (Max Depth 3)
    dt = DecisionTreeClassifier(max_depth=3, random_state=42, min_samples_leaf=3)
    dt.fit(X_train, y_train)
    dt_train_pred = dt.predict(X_train)
    dt_test_pred = dt.predict(X_test)
    dt_test_prob = dt.predict_proba(X_test)[:, 1] if hasattr(dt, "predict_proba") else None
    
    dt_train_metrics = _compute_classification_metrics(y_train, dt_train_pred)
    dt_test_metrics = _compute_classification_metrics(y_test, dt_test_pred, dt_test_prob)
    dt_cm = _compute_confusion_matrix_data(y_test, dt_test_pred)
    dt_cv = _perform_stratified_cv(dt, X, y, n_splits=5)
    
    dt_importances = []
    dt_ranks = np.argsort(-dt.feature_importances_)
    for rank_idx, feat_idx in enumerate(dt_ranks):
        f_name = feature_cols[feat_idx]
        imp_val = float(dt.feature_importances_[feat_idx])
        dt_importances.append(
            FeatureImportanceItem(
                feature_name=f_name,
                importance_metric="Feature Importance (Decision Tree)",
                importance_value=round(imp_val, 4),
                rank=rank_idx + 1,
                interpretation=f"Contributes {imp_val*100:.1f}% of decision tree split information gain.",
            )
        )
        
    results.append(
        ModelResult(
            model_name="Decision Tree (Interpretable Partitions)",
            target_variable=target_col,
            features_used=feature_cols,
            train_size=len(X_train),
            test_size=len(X_test),
            train_metrics=dt_train_metrics,
            test_metrics=dt_test_metrics,
            cv_results=dt_cv,
            confusion_matrix=dt_cm,
            feature_importances=dt_importances,
            error_analysis=[],
            model_stability_notes=f"5-Fold CV Mean Accuracy: {dt_cv.mean_accuracy*100:.1f}%.",
            hyperparameters={"max_depth": 3, "min_samples_leaf": 3, "random_state": 42},
        )
    )
    
    return results


def train_and_evaluate_sds_models(sds_df: pd.DataFrame) -> list[ModelResult]:
    """Train baseline models on SDS Big Five personality traits."""
    feature_cols = [
        "neuroticism",
        "extraversion",
        "openness_to_experience",
        "agreeableness",
        "conscientiousness",
    ]
    target_col = "success_classification_high_low"
    
    X = sds_df[feature_cols].values
    y = sds_df[target_col].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    lr = LogisticRegression(random_state=42, max_iter=1000)
    lr.fit(X_train, y_train)
    
    y_test_pred = lr.predict(X_test)
    y_test_prob = lr.predict_proba(X_test)[:, 1]
    
    train_metrics = _compute_classification_metrics(y_train, lr.predict(X_train))
    test_metrics = _compute_classification_metrics(y_test, y_test_pred, y_test_prob)
    cm = _compute_confusion_matrix_data(y_test, y_test_pred)
    cv = _perform_stratified_cv(lr, X, y, n_splits=5)
    
    coefs = lr.coef_[0]
    odds_ratios = np.exp(coefs)
    importances = []
    ranks = np.argsort(-np.abs(coefs))
    for rank_idx, feat_idx in enumerate(ranks):
        f_name = feature_cols[feat_idx]
        c_val = float(coefs[feat_idx])
        or_val = float(odds_ratios[feat_idx])
        importances.append(
            FeatureImportanceItem(
                feature_name=f_name,
                importance_metric="Odds Ratio (Logistic Regression)",
                importance_value=round(c_val, 4),
                odds_ratio=round(or_val, 4),
                rank=rank_idx + 1,
                interpretation=f"Estimated {or_val:.2f}x odds of high success outcome per 1-unit increase in standardized score.",
            )
        )
        
    return [
        ModelResult(
            model_name="SDS Logistic Regression (Personality Baseline)",
            target_variable=target_col,
            features_used=feature_cols,
            train_size=len(X_train),
            test_size=len(X_test),
            train_metrics=train_metrics,
            test_metrics=test_metrics,
            cv_results=cv,
            confusion_matrix=cm,
            feature_importances=importances,
            error_analysis=[],
            model_stability_notes=f"5-Fold CV Mean Accuracy: {cv.mean_accuracy*100:.1f}%.",
            hyperparameters={"C": 1.0, "solver": "lbfgs", "random_state": 42},
        )
    ]
