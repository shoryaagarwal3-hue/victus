"""Google ADK Workflow Orchestrator for Curriculum Recommendations.
Handles AI model invocation, provider configuration (Gemini/ADK/Local),
error handling (429, timeouts, malformed JSON), and output validation.
"""
import asyncio
import os
import re
import json
import logging
import time
import urllib.request
import urllib.error
from typing import Any

from google.genai.errors import APIError

from .models import (
    CourseSubject,
    RecommendationResponse,
    PatchBundle,
    ElectiveModule,
    FacultyEnablement,
    COPOMapping,
)
from .ai_config import (
    gemini_fallback_model_name,
    gemini_model_name,
    local_endpoint_url,
    local_model_name,
)
from .audit_service import (
    set_active_audit,
    clear_active_audit,
    build_deterministic_recommendations,
)
from agents.curriculum_audit.agent import create_curriculum_agent

LOGGER = logging.getLogger(__name__)
ADK_APP_NAME = "curriculum_drift_audit"
RETRY_BACKOFF_SECONDS = 1.0

RECOMMENDATION_PROMPT = """You are the Senior Curriculum Alignment Specialist and Technical Auditor for NBA/NAAC accredited institutions.
You have been provided deterministic audit metrics and their market-data provenance.
Your task is AI-ASSISTED CURRICULUM PRIORITIZATION: answer "What should the curriculum team work on first based on the available evidence?"

AUDIT EVIDENCE (CHECK PROVENANCE BEFORE CLAIMING MARKET VALIDATION):
- Institution: {college}
- Target Role: {role}
- Stability Index: {stability_index}%
- Drift Rate: {drift_rate}%
- Composite Health Score: {health_score}%
- Detected Skill Coverage Gaps: {missing_tools}
- Extracted Syllabus Subjects ({subject_count}): {subjects_summary}
- Deterministic Priority Register: {priority_summary}
- Market metrics and provenance: {market_summary}
- Accredited Certifications in Catalog: {cert_summary}

CONSTRAINTS & RULES:
1. Output ONLY valid JSON matching the schema below. No markdown fences or explanatory text outside the JSON.
2. DO NOT invent course codes, credits, market statistics, percentages, or certifications. Treat each
   metric according to supplied provenance; insufficient provenance does not verify market demand.
3. Review every extracted subject using KEEP, UPDATE, MERGE, RECONSIDER, or INSUFFICIENT_EVIDENCE.
   Do not discard foundational subjects merely because a role-specific tool is absent.
4. Recommend a new elective only when a concrete, verified skill gap cannot fit within existing subjects.
5. Organize the Action Plan into NOW, NEXT, and LATER horizons with an explicit impact/effort quadrant:
   HIGH IMPACT / LOW EFFORT, HIGH IMPACT / HIGH EFFORT, LOW IMPACT / LOW EFFORT, or LOW IMPACT / HIGH EFFORT.
6. Prepare faculty for teaching adopted subject and tool updates; do not prescribe separate exercises or environments.
7. Map Course Outcomes to NBA Program Outcomes (PO1 to PO12), using only outcomes grounded in the syllabus
   or recommended subject content.

SCHEMA:
{{
  "prioritization_summary": "Direct executive answer to: What should the curriculum team work on first based on the available evidence?",
  "subject_reviews": [
    {{
      "course_code": "string",
      "course_name": "string",
      "action": "KEEP | UPDATE | MERGE | RECONSIDER | INSUFFICIENT_EVIDENCE",
      "reason": "string",
      "target_role": "string",
      "missing_skills": ["string"],
      "foundational_importance": "string",
      "confidence": 0.85
    }}
  ],
  "new_subjects": [
    {{
      "title": "string",
      "reason": "string",
      "target_role": "string",
      "missing_skills": ["string"],
      "market_evidence": "string",
      "affected_gap": "string",
      "prerequisites": ["string"],
      "credits": 3,
      "units_topics": [{{"unit_no": 1, "title": "string", "topics": ["string"]}}],
      "learning_outcomes": ["string"],
      "effort": "LOW | MEDIUM | HIGH",
      "priority": "CRITICAL | HIGH | MEDIUM | LOW",
      "confidence": 0.85
    }}
  ],
  "action_plan": [
    {{
      "horizon": "NOW | NEXT | LATER",
      "affected_subject_or_skill": "string",
      "action_type": "string",
      "reason": "string",
      "evidence": "string",
      "expected_impact": "string",
      "effort": "LOW | MEDIUM | HIGH",
      "impact_effort_quadrant": "HIGH IMPACT / LOW EFFORT | HIGH IMPACT / HIGH EFFORT | LOW IMPACT / LOW EFFORT | LOW IMPACT / HIGH EFFORT",
      "confidence": 0.85
    }}
  ],
  "faculty_enablement": {{
    "steps": ["string"],
    "implementation_notes": "string",
    "reference_docs": ["string"]
  }},
  "copo_mapping": [
    {{
      "course_outcome": "string",
      "mapped_pos": [{{"po": "PO1", "strength": 3, "justification": "string"}}]
    }}
  ]
}}
"""


def _clean_json_response(raw_text: str) -> dict[str, Any]:
    """Clean markdown code fences and parse JSON safely."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    # Try finding first { and last }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace : last_brace + 1]
    return json.loads(cleaned)


def _call_local_endpoint(prompt: str, endpoint: str) -> str:
    """Query optional OpenAI-compatible local endpoint (e.g. http://127.0.0.1:8081/v1/chat/completions)."""
    url = endpoint.rstrip("/")
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"
    payload = json.dumps({
        "model": local_model_name(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 3000,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except urllib.error.URLError as exc:
        raise RuntimeError("Local LLM endpoint connection failed.") from exc


def _run_adk_agent(prompt: str, model_name: str | None = None) -> str:
    """Invoke the primary curriculum_recommender through Google ADK."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    session_service = InMemorySessionService()
    runner = Runner(
        agent=create_curriculum_agent(model_name=model_name or gemini_model_name()),
        app_name=ADK_APP_NAME,
        session_service=session_service,
    )
    user_id = "curriculum_audit"

    async def invoke() -> str:
        session = await session_service.create_session(
            app_name=ADK_APP_NAME,
            user_id=user_id,
        )
        final_text: list[str] = []
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)],
                ),
            ):
                if not event.is_final_response() or event.content is None:
                    continue
                final_text.extend(
                    part.text
                    for part in event.content.parts or []
                    if part.text
                )
        finally:
            await runner.close()

        if not final_text:
            raise RuntimeError("Google ADK returned no final recommendation content.")
        return "\n".join(final_text)

    return asyncio.run(invoke())


def _validate_recommendation_evidence(
    response: RecommendationResponse,
    result: dict[str, Any],
    role: str,
    subjects: list[CourseSubject],
    po_definitions: dict[str, Any],
) -> RecommendationResponse:
    """Reject references that cannot be tied back to the deterministic audit."""
    subject_keys = {
        (subject.course_code.strip().casefold(), subject.course_name.strip().casefold())
        for subject in subjects
    }
    returned_subject_keys = [
        (review.course_code.strip().casefold(), review.course_name.strip().casefold())
        for review in response.subject_reviews
    ]
    if any(key not in subject_keys for key in returned_subject_keys):
        raise ValueError("Recommendation response referenced a subject not extracted from this syllabus.")
    if len(returned_subject_keys) != len(set(returned_subject_keys)):
        raise ValueError("Recommendation response contains duplicate subject reviews.")
    if set(returned_subject_keys) != subject_keys:
        raise ValueError("Recommendation response did not evaluate every extracted syllabus subject.")

    missing_tools = {str(tool).casefold() for tool in result.get("missing_tools", [])}
    actual_subject_names = {
        value
        for code, name in subject_keys
        for value in (code, name)
        if value and value != "n/a"
    }
    new_outcomes = {
        outcome.strip().casefold()
        for new_subject in response.new_subjects
        for outcome in new_subject.learning_outcomes
    }
    source_outcomes = {
        outcome.strip().casefold()
        for subject in subjects
        for outcome in subject.learning_outcomes
    }
    priority_by_skill = {
        str(item.get("item_name", "")).casefold(): item
        for item in result.get("priority_register", [])
        if item.get("item_name")
    }
    market_source_type = (
        result.get("profile", {}).get("provenance", {}).get("source_type", "INSUFFICIENT EVIDENCE")
    )

    for review in response.subject_reviews:
        if review.target_role.strip().casefold() != role.strip().casefold():
            raise ValueError("Subject recommendation targets a role different from the active audit.")
        if any(skill.casefold() not in missing_tools for skill in review.missing_skills):
            raise ValueError("Subject recommendation included a skill absent from the verified audit gaps.")

    for recommendation in response.new_subjects:
        if recommendation.target_role.strip().casefold() != role.strip().casefold():
            raise ValueError("New-subject recommendation targets a role different from the active audit.")
        if not recommendation.missing_skills or any(
            skill.casefold() not in missing_tools for skill in recommendation.missing_skills
        ):
            raise ValueError("New-subject recommendation is not linked to a verified missing skill.")
        evidence = [
            priority_by_skill[skill.casefold()].get("evidence_summary", "")
            for skill in recommendation.missing_skills
            if skill.casefold() in priority_by_skill
        ]
        if not evidence:
            raise ValueError("New-subject recommendation has no deterministic priority evidence.")
        recommendation.market_evidence = (
            f"Deterministic priority register ({market_source_type} market evidence): "
            + " ".join(evidence)
        )

    new_subject_titles = {
        new_subject.title.strip().casefold() for new_subject in response.new_subjects
    }
    subject_by_reference = {
        reference: subject
        for subject in subjects
        for reference in (
            subject.course_code.strip().casefold(),
            subject.course_name.strip().casefold(),
        )
    }
    for action in response.action_plan:
        target = action.affected_subject_or_skill.strip().casefold()
        if (
            target not in missing_tools
            and target not in actual_subject_names
            and target not in new_subject_titles
        ):
            raise ValueError("Action plan references an unknown subject or skill.")
        if target in priority_by_skill:
            action.evidence = priority_by_skill[target].get("evidence_summary", "")
        elif target in subject_by_reference:
            subject = subject_by_reference[target]
            action.evidence = (
                f"Syllabus extraction: {subject.course_code} {subject.course_name}; "
                f"source pages {subject.source_pages}; "
                f"extraction confidence {subject.extraction_confidence:.2f}."
            )
        elif target in new_subject_titles:
            action.evidence = "Proposed course only; no existing syllabus evidence is claimed."

    known_outcomes = source_outcomes | new_outcomes
    known_pos = {str(po).casefold() for po in po_definitions}
    for mapping in response.copo_mapping:
        if mapping.course_outcome.strip().casefold() not in known_outcomes:
            raise ValueError("CO-PO mapping references an outcome absent from the syllabus and recommendations.")
        for mapped_po in mapping.mapped_pos:
            po = str(mapped_po.get("po", "")).casefold()
            strength = mapped_po.get("strength")
            if po not in known_pos or not isinstance(strength, int) or not 1 <= strength <= 3:
                raise ValueError("CO-PO mapping contains an unknown PO or an invalid strength.")

    response.faculty_enablement.reference_docs = []
    return response


def run_curriculum_audit_workflow(
    college: str,
    role: str,
    result: dict[str, Any],
    subjects: list[CourseSubject] | None = None,
    cert_catalog: dict[str, Any] | None = None,
    po_definitions: dict[str, Any] | None = None,
) -> RecommendationResponse:
    """Execute the curriculum recommender and always clear request-local evidence."""
    set_active_audit(college, role, result, subjects, cert_catalog, po_definitions)
    try:
        return _run_curriculum_audit_workflow(
            college,
            role,
            result,
            subjects,
            cert_catalog,
            po_definitions,
        )
    finally:
        clear_active_audit()


def _run_curriculum_audit_workflow(
    college: str,
    role: str,
    result: dict[str, Any],
    subjects: list[CourseSubject] | None = None,
    cert_catalog: dict[str, Any] | None = None,
    po_definitions: dict[str, Any] | None = None,
) -> RecommendationResponse:
    """Execute AI recommendation workflow using Google ADK / Gemini with full error resilience.
    
    If AI fails, raises a clear RuntimeError so the UI can display error state without
    affecting the verified deterministic audit.
    """
    # 1. Build the verified context passed to the agent and its read-only tools
    extracted_subjects = subjects or (result.get("corpus").subjects if result.get("corpus") else [])
    subj_summary = "; ".join(f"{s.course_code}: {s.course_name} ({s.confidence_level} confidence)" for s in extracted_subjects[:10]) or "General Syllabus Corpus"
    missing_tools_str = ", ".join(result.get("missing_tools", [])) or "None"
    priority_summary = "; ".join(f"{p['item_name']}: {p['priority_level']} ({p['priority_score']})" for p in result.get("priority_register", [])[:5]) or "None"
    certs_summary = "; ".join(f"{t}: {len(cert_catalog.get(t, []))} certs" for t in result.get("missing_tools", []) if cert_catalog and t in cert_catalog) or "None in catalog"
    market_summary = json.dumps(
        {
            "provenance": result.get("profile", {}).get("provenance", {}),
            "toolchain": result.get("profile", {}).get("toolchain", []),
        },
        ensure_ascii=False,
        sort_keys=True,
    )

    prompt = RECOMMENDATION_PROMPT.format(
        college=college,
        role=role,
        stability_index=result.get("stability_index", 0.0),
        drift_rate=result.get("drift_rate", 0.0),
        health_score=result.get("health_score", 0.0),
        missing_tools=missing_tools_str,
        subject_count=len(extracted_subjects),
        subjects_summary=subj_summary,
        priority_summary=priority_summary,
        cert_summary=certs_summary,
        market_summary=market_summary,
    )

    # 2. Check for configured provider
    local_endpoint = local_endpoint_url()
    if local_endpoint:
        LOGGER.info("Executing recommendation workflow via configured local LLM endpoint.")
        try:
            raw_text = _call_local_endpoint(prompt, local_endpoint)
            payload = _clean_json_response(raw_text)
            response = RecommendationResponse.model_validate(payload)
            return _validate_recommendation_evidence(
                response, result, role, extracted_subjects, po_definitions or {}
            )
        except Exception as exc:
            LOGGER.warning(
                "Local endpoint failed (%s); checking Gemini fallback.",
                type(exc).__name__,
            )

    # 3. Google ADK curriculum_recommender
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise RuntimeError("GEMINI_API_KEY is not configured; AI recommendations are unavailable. Deterministic analysis is fully available.")

    try:
        last_error = None
        primary_model = gemini_model_name()
        fallback_model = gemini_fallback_model_name()
        models = [primary_model]
        if fallback_model != primary_model:
            models.append(fallback_model)
        for attempt, model_name in enumerate(models):
            try:
                LOGGER.info(
                    "Calling Google ADK curriculum_recommender with %s (attempt %d)",
                    model_name,
                    attempt + 1,
                )
                req_prompt = prompt if attempt == 0 else prompt + "\nCRITICAL: Return ONLY raw JSON without markdown code fences."
                payload = _clean_json_response(_run_adk_agent(req_prompt, model_name))
                response = RecommendationResponse.model_validate(payload)
                return _validate_recommendation_evidence(
                    response, result, role, extracted_subjects, po_definitions or {}
                )
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                last_error = exc
                LOGGER.warning("Attempt %d recommendation validation failed: %s", attempt + 1, exc)
            except (APIError, TimeoutError, ConnectionError, urllib.error.URLError) as exc:
                status_code = getattr(exc, "code", None)
                is_transient = (
                    isinstance(exc, (TimeoutError, ConnectionError, urllib.error.URLError))
                    or status_code in (408, 425, 429)
                    or (isinstance(status_code, int) and status_code >= 500)
                )
                if not is_transient:
                    raise
                last_error = exc
                LOGGER.warning(
                    "Attempt %d failed transiently for %s (%s); %s",
                    attempt + 1,
                    model_name,
                    type(exc).__name__,
                    "retrying with fallback model" if attempt + 1 < len(models) else "no further model configured",
                )
            if attempt + 1 < len(models):
                time.sleep(RETRY_BACKOFF_SECONDS)

        if isinstance(last_error, APIError):
            raise RuntimeError(
                f"Gemini API request failed after {len(models)} attempt(s): {last_error}"
            ) from last_error
        raise RuntimeError(f"Gemini returned malformed recommendation response: {last_error}") from last_error

    except Exception as exc:
        err_msg = str(exc)
        for secret in (gemini_key, os.getenv("GOOGLE_API_KEY", "")):
            if secret:
                err_msg = err_msg.replace(secret, "[REDACTED]")
        if "429" in err_msg or "quota" in err_msg.lower():
            raise RuntimeError("AI recommendations are temporarily unavailable because the API quota is exhausted (HTTP 429). The core deterministic audit remains fully active.") from exc
        if "401" in err_msg or "403" in err_msg or "invalid api key" in err_msg.lower() or "api_key_invalid" in err_msg.lower():
            raise RuntimeError("AI recommendations failed due to invalid or unauthorized GEMINI_API_KEY. Check your credentials.") from exc
        if "timeout" in err_msg.lower() or "deadline" in err_msg.lower():
            raise RuntimeError("AI recommendation request timed out. Please retry.") from exc
        raise RuntimeError(f"AI recommendation generation failed: {exc}") from exc


def convert_recommendations_to_patch_bundle(rec: RecommendationResponse) -> PatchBundle:
    """Convert RecommendationResponse to the retained subject/evidence bundle."""
    first_subj = rec.new_subjects[0] if rec.new_subjects else None
    elective = ElectiveModule(
        title=first_subj.title if first_subj else "Elective Blueprint",
        credits=first_subj.credits if first_subj else 2,
        units=first_subj.units_topics if first_subj else [],
        course_outcomes=first_subj.learning_outcomes if first_subj else [],
    )
    
    return PatchBundle(
        elective_module=elective,
        faculty_enablement=rec.faculty_enablement,
        copo_mapping=rec.copo_mapping,
    )
