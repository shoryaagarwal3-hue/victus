"""Patch and Recommendation Generator.
Integrates Google ADK / Gemini workflows for structured curriculum modernization.
Preserves backwards compatibility with legacy generate_patches while offering full
RecommendationResponse generation.
"""
import json
import os
import re
import hashlib
import logging
from typing import Any
from .ai_config import gemini_model_name
from .models import PatchBundle, RecommendationResponse
from .adk_workflow import run_curriculum_audit_workflow, convert_recommendations_to_patch_bundle

LOGGER = logging.getLogger(__name__)

PROMPT = """You are a curriculum design assistant for Indian technical education,
familiar with NBA/NAAC accreditation formats. Output ONLY valid JSON matching this
schema, with no markdown fences or prose:
{"elective_module":{"title":str,"credits":2,"units":[{"unit_no":int,"topics":[str]}],
"course_outcomes":[str]},
"faculty_enablement":{"steps":[str],"implementation_notes":str,"reference_docs":[str]},
"copo_mapping":[{"course_outcome":str,"mapped_pos":[{"po":"PO1","strength":1,
"justification":str}]}]}
Constraints: zero exam-structure disruption; align adopted topics with verified skill gaps;
do not invent outcomes or course codes.
Input missing_tools={missing_tools}, role_track={role_track}, corpus_context={corpus_context}"""


def patch_fingerprint(missing_tools: list[str], role_track: str, corpus_context: str) -> str:
    value = f"{role_track}\n{','.join(sorted(missing_tools))}\n{corpus_context[:4000]}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _json_payload(text: str) -> dict[str, object]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("AI response must be a JSON object")
    return payload


def generate_patches(missing_tools: list[str], role_track: str, corpus_context: str = "") -> PatchBundle:
    """Call Gemini when configured; errors are raised so UI can show a real failure state."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured; AI patches are unavailable.")
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(gemini_model_name())
        LOGGER.info("GEMINI_CALL feature=patches")
        prompt = (
            PROMPT.replace("{missing_tools}", ", ".join(missing_tools))
            .replace("{role_track}", role_track)
            .replace("{corpus_context}", corpus_context[:4000])
        )
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = model.generate_content(
                    prompt if attempt == 0 else prompt
                    + "\nReturn ONLY valid JSON, no markdown fences.")
                return PatchBundle.model_validate(_json_payload(response.text))
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                last_error = exc
        raise RuntimeError(f"Gemini returned invalid patch JSON: {last_error}") from last_error
    except Exception as exc:
        if "429" in str(exc) or "quota" in str(exc).lower():
            raise RuntimeError("AI recommendations unavailable because the Gemini quota is currently exhausted. Deterministic analysis is still available.") from exc
        raise RuntimeError(f"Gemini patch generation failed: {exc}") from exc


def generate_full_recommendations(
    college: str,
    role: str,
    result: dict[str, Any],
    subjects: list[Any] | None = None,
    cert_catalog: dict[str, Any] | None = None,
    po_definitions: dict[str, Any] | None = None,
) -> RecommendationResponse:
    """Invoke Google ADK workflow for complete curriculum review and action planning."""
    return run_curriculum_audit_workflow(college, role, result, subjects, cert_catalog, po_definitions)
