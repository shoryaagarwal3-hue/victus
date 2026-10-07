"""Hardened PDF audit report generator.
Handles Unicode, long strings, token wrapping, empty fields, and new structured audit sections.
Ensures zero uncaught errors on export.
"""
from datetime import date
import re
import unicodedata
from typing import Any
from fpdf import FPDF
from fpdf.enums import XPos, YPos


def _safe_text(value: Any) -> str:
    """Return Helvetica-safe text while preserving readable generated content."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2026": "...",
        "\u2022": "-", "\u00a0": " ", "\u2192": "->", "\u2190": "<-",
        "\u2265": ">=", "\u2264": "<=", "\u2713": "[Y]", "\u2717": "[N]",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Encode to latin-1 and ignore or replace characters outside range
    return text.encode("latin-1", "replace").decode("latin-1")


def _wrap_unbroken_tokens(text: str, chunk_size: int = 42) -> str:
    """Insert break opportunities so long URLs and identifiers cannot overflow page width."""
    parts = re.split(r"(\s+)", text)
    wrapped: list[str] = []
    for part in parts:
        if part.isspace() or len(part) <= chunk_size:
            wrapped.append(part)
            continue
        wrapped.append(" ".join(part[i : i + chunk_size] for i in range(0, len(part), chunk_size)))
    return "".join(wrapped)


def _safe_multi_cell(pdf: FPDF, text: Any, line_height: float = 5.5) -> None:
    """Write multi-line text safely respecting margins."""
    content = _wrap_unbroken_tokens(_safe_text(text))
    if not content:
        pdf.ln(line_height)
        return
    width = pdf.w - pdf.l_margin - pdf.r_margin
    if width <= 0:
        width = 180.0
    pdf.multi_cell(width, line_height, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _safe_cell(pdf: FPDF, text: Any, line_height: float = 6.5) -> None:
    """Write single-line text cell safely."""
    content = _wrap_unbroken_tokens(_safe_text(text))
    width = pdf.w - pdf.l_margin - pdf.r_margin
    if width <= 0:
        width = 180.0
    pdf.cell(width, line_height, content, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def build_pdf(
    college: str | None,
    role: str | None,
    scores: dict[str, Any] | None,
    patches: dict[str, Any] | None = None,
) -> bytes:
    """Compile comprehensive BOS/NAAC Alignment Audit Report into PDF bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 1. Header
    pdf.set_font("Helvetica", "B", 16)
    _safe_cell(pdf, "BOS/NAAC CURRICULUM DRIFT & MARKET-ALIGNMENT AUDIT")
    pdf.set_font("Helvetica", size=9)
    college_str = _safe_text(college or "Unknown Institution")
    role_str = _safe_text(role or "General Track")
    _safe_cell(pdf, f"Institution: {college_str} | Target Role: {role_str} | Date: {date.today().isoformat()}")
    pdf.ln(3)

    # 2. Key Quantitative Metrics
    pdf.set_font("Helvetica", "B", 11)
    market_evidence_available = bool((scores or {}).get("market_evidence_available", True))
    metrics_label = (
        "1. QUANTITATIVE ALIGNMENT METRICS [DETERMINISTIC AUDIT OUTPUT]"
        if market_evidence_available
        else "1. SYLLABUS / PROFILE COMPARISON [MARKET EVIDENCE INSUFFICIENT]"
    )
    _safe_cell(pdf, metrics_label)
    pdf.set_font("Helvetica", size=9)
    market_provenance = (scores or {}).get("profile", {}).get("provenance", {})
    if market_provenance:
        _safe_multi_cell(
            pdf,
            "Market evidence: "
            f"{market_provenance.get('source_type', 'INSUFFICIENT EVIDENCE')} | "
            f"Metric: {market_provenance.get('metric', 'undocumented')} | "
            f"Source: {market_provenance.get('source', 'undocumented')} | "
            f"Date: {market_provenance.get('date', 'undocumented')} | "
            f"Denominator: {market_provenance.get('denominator', 'not provided')}",
        )
    if not market_evidence_available:
        _safe_multi_cell(
            pdf,
            "Market demand, CPS priority rankings, and market drift are withheld because "
            "the role profile lacks verified market provenance. Any syllabus/profile "
            "comparisons below are not claims about market demand.",
        )
    
    stability = scores.get("stability_index", 0.0) if scores else 0.0
    drift = scores.get("drift_rate", 0.0) if scores else 0.0
    health = scores.get("health_score", 0.0) if scores else 0.0
    _safe_cell(pdf, f"Stability Index (Foundational Concepts): {float(stability or 0):.1f}%")
    _safe_cell(pdf, f"Curriculum Drift Rate (Toolchains): {float(drift or 0):.1f}%")
    _safe_cell(pdf, f"Composite Health Score: {float(health or 0):.1f}%")

    missing = scores.get("missing_tools", []) if scores else []
    if not isinstance(missing, (list, tuple)):
        missing = [missing]
    _safe_cell(pdf, f"Missing Toolchains ({len(missing)}): {', '.join(_safe_text(m) for m in missing) or 'None'}")
    pdf.ln(3)

    # 3. Executive Prioritization (What should we work on first?)
    summary_text = ""
    if patches and isinstance(patches, dict) and patches.get("prioritization_summary"):
        summary_text = patches["prioritization_summary"]
    elif scores and scores.get("deterministic_summary"):
        summary_text = scores["deterministic_summary"]

    if summary_text:
        pdf.set_font("Helvetica", "B", 11)
        provenance = patches.get("evidence_provenance", "AI-ASSISTED") if patches else "DETERMINISTIC"
        _safe_cell(pdf, f"2. WHAT SHOULD WE WORK ON FIRST? [{_safe_text(provenance)}]")
        pdf.set_font("Helvetica", size=9)
        _safe_multi_cell(pdf, summary_text)
        pdf.ln(3)

    # 4. Priority Register
    priorities = scores.get("priority_register", []) if scores else []
    if priorities:
        pdf.set_font("Helvetica", "B", 11)
        _safe_cell(pdf, "3. DETERMINISTIC PRIORITY REGISTER [DETERMINISTIC FORMULA]")
        pdf.set_font("Helvetica", size=8)
        for p in priorities[:8]:
            item_name = p.get("item_name", "Unknown")
            lvl = p.get("priority_level", "MEDIUM")
            score_val = p.get("priority_score", 0.0)
            quad = p.get("impact_effort_category", "")
            _safe_multi_cell(pdf, f"- [{lvl}] {item_name}: Priority Score {score_val:.1f} | Category: {quad}")
        pdf.ln(3)

    # 5. Subject Reviews
    subj_reviews = patches.get("subject_reviews", []) if isinstance(patches, dict) else []
    if subj_reviews:
        pdf.set_font("Helvetica", "B", 11)
        _safe_cell(pdf, "4. SYLLABUS SUBJECT REVIEWS [EVALUATION MATRIX]")
        pdf.set_font("Helvetica", size=8)
        for sr in subj_reviews[:10]:
            code = sr.get("course_code", "N/A")
            name = sr.get("course_name", "Subject")
            act = sr.get("action", "KEEP")
            rsn = sr.get("reason", "")
            _safe_multi_cell(pdf, f"* [{act}] {code}: {name} - {rsn}")
        pdf.ln(3)

    # 6. New Subjects / Electives
    new_subjs = patches.get("new_subjects", []) if isinstance(patches, dict) else []
    if not new_subjs and isinstance(patches, dict) and patches.get("elective_module"):
        el = patches.get("elective_module", {})
        if el and el.get("title"):
            new_subjs = [{
                "title": el.get("title"),
                "credits": el.get("credits", 2),
                "reason": "Proposed bridge elective for curriculum alignment.",
                "units_topics": el.get("units", []),
                "learning_outcomes": el.get("course_outcomes", []),
            }]
            
    if new_subjs:
        pdf.set_font("Helvetica", "B", 11)
        _safe_cell(pdf, "5. RECOMMENDED NEW SUBJECTS / ELECTIVES")
        pdf.set_font("Helvetica", size=8)
        for ns in new_subjs:
            _safe_multi_cell(pdf, f"Elective: {ns.get('title')} ({ns.get('credits', 3)} Credits)")
            if ns.get("reason"):
                _safe_multi_cell(pdf, f"  Rationale: {ns.get('reason')}")
            for u in ns.get("units_topics", []):
                u_no = u.get("unit_no", "")
                u_title = u.get("title", "")
                topics = ", ".join(u.get("topics", []))
                _safe_multi_cell(pdf, f"  - Unit {u_no} ({u_title}): {topics}")
        pdf.ln(3)

    # 6. Action Plan (NOW / NEXT / LATER)
    action_plan = patches.get("action_plan", []) if isinstance(patches, dict) else []
    if action_plan:
        pdf.set_font("Helvetica", "B", 11)
        _safe_cell(pdf, "6. CURRICULUM ACTION PLAN [NOW / NEXT / LATER]")
        pdf.set_font("Helvetica", size=8)
        for act in action_plan:
            h = act.get("horizon", "NOW")
            subj_skill = act.get("affected_subject_or_skill", "")
            rsn = act.get("reason", "")
            quad = act.get("impact_effort_quadrant", "")
            _safe_multi_cell(pdf, f"[{h}] {subj_skill} ({quad}): {rsn}")
        pdf.ln(3)

    # 7. Faculty Enablement & Accreditation CO-PO
    if isinstance(patches, dict):
        faculty = patches.get("faculty_enablement", {})
        if faculty and isinstance(faculty, dict):
            pdf.set_font("Helvetica", "B", 11)
            _safe_cell(pdf, "7. FACULTY ENABLEMENT & ACCREDITATION READINESS")
            pdf.set_font("Helvetica", size=8)
            for step in faculty.get("steps", []):
                _safe_multi_cell(pdf, f"* Faculty preparation: {step}")
            if faculty.get("implementation_notes"):
                _safe_multi_cell(pdf, f"* Implementation: {faculty.get('implementation_notes')}")

    certifications = (scores or {}).get("certification_options", {})
    if certifications:
        pdf.set_font("Helvetica", "B", 11)
        _safe_cell(pdf, "8. CERTIFICATION CATALOG OPTIONS")
        pdf.set_font("Helvetica", size=8)
        for tool, options in certifications.items():
            if not options:
                _safe_multi_cell(pdf, f"{tool}: No catalog entry available.")
                continue
            for cert in options:
                _safe_multi_cell(
                    pdf,
                    f"{tool}: {cert.get('cert_name', '')} | {cert.get('issuer', '')} | {cert.get('level', '')}",
                )

    copo_mappings = patches.get("copo_mapping", []) if isinstance(patches, dict) else []
    po_definitions = (scores or {}).get("po_definitions", {})
    if copo_mappings:
        pdf.set_font("Helvetica", "B", 11)
        _safe_cell(pdf, "9. AI-SUGGESTED CO-PO MAPPINGS [VERIFY BEFORE ADOPTION]")
        pdf.set_font("Helvetica", size=8)
        for mapping in copo_mappings:
            _safe_multi_cell(pdf, f"CO: {mapping.get('course_outcome', '')}")
            for item in mapping.get("mapped_pos", []):
                po_code = item.get("po", "")
                po_description = po_definitions.get(po_code, "Definition unavailable")
                _safe_multi_cell(
                    pdf,
                    f"  {po_code} — {po_description} | Strength: {item.get('strength', '')} | "
                    f"{item.get('justification', '')}",
                )

    return bytes(pdf.output())
