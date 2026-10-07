"""Tests for the expanded curriculum catalog (AI & ML and Cloud Computing)."""
from pathlib import Path
import json
import pytest
from urllib.parse import urlsplit

from backend.cu_curriculum_catalog import CurriculumSource, load_catalog

BASE = Path(__file__).resolve().parents[1]
CATALOG_PATH = BASE / "data" / "cu_cse_curriculum_catalog.json"
ALLOWED_DOMAINS = {"cuchd.in", "www.cuchd.in"}

ORIGINAL_34_IDS = [
    "uie-cse-2018-22",
    "uie-cse-2019-23",
    "uie-cse-2020-24",
    "uie-cse-2021-25",
    "uie-cse-2022-26",
    "uie-cse-2023-27",
    "uie-cse-2024-28",
    "uie-cse-2025-29",
    "uie-full-stack-2026",
    "uie-cse-csbs-2025",
    "uie-cse-ai-microsoft",
    "uie-full-stack-lateral",
    "uie-cse-lateral",
    "uie-gaming-graphics-2021",
    "apex-ibm-cyber-security-2025",
    "apex-ibm-data-science-2026",
    "apex-ibm-aiml-2026",
    "apex-ibm-iot-ai",
    "apex-ibm-cloud",
    "apex-aiml-lateral",
    "apex-cloud-regular",
    "apex-information-security",
    "apex-iot",
    "apex-blockchain",
    "apex-devops",
    "ibm-data-science-2026",
    "ibm-aiml-2026",
    "ibm-cyber-security",
    "ibm-iot-ai",
    "ibm-cyber-security-lateral",
    "ibm-aiml-lateral",
    "ibm-iot-lateral",
    "cse-ai-lateral",
    "uie-full-stack-program-2026",
]

NEW_IDS = [
    "uie-cse-ai-ml-2025",
    "uie-cse-cloud-computing-2025",
]


def test_catalog_schema_validation():
    """Catalog JSON validates against CurriculumSource schema without errors."""
    records = load_catalog(CATALOG_PATH)
    assert len(records) == 36, f"Expected 36 records, got {len(records)}"
    for r in records:
        assert isinstance(r, CurriculumSource)


def test_original_records_unaltered():
    """All 34 original record IDs are preserved in order with no modifications."""
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    raw_ids = [item["id"] for item in raw]
    assert len(raw_ids) == 36
    assert raw_ids[:34] == ORIGINAL_34_IDS, "Existing 34 records must remain unaltered in ID and order"


def test_new_records_cuchd_domain():
    """Both new records have official_source_page and direct_pdf_url on cuchd.in domain."""
    records = load_catalog(CATALOG_PATH)
    record_map = {r.id: r for r in records}

    for new_id in NEW_IDS:
        assert new_id in record_map, f"Missing new record {new_id}"
        rec = record_map[new_id]

        # Check official source page domain
        page_host = urlsplit(rec.official_source_page).hostname
        assert page_host in ALLOWED_DOMAINS, f"Invalid domain for source page: {page_host}"

        # Check direct PDF URL domain
        assert rec.direct_pdf_url is not None, f"Expected direct PDF URL for {new_id}"
        pdf_host = urlsplit(rec.direct_pdf_url).hostname
        assert pdf_host in ALLOWED_DOMAINS, f"Invalid domain for PDF URL: {pdf_host}"

        # Check source type and status
        assert rec.source_type == "OFFICIAL_PDF"
        assert rec.status == "VERIFIED"
        assert rec.verified is True


def test_new_specializations_content():
    """Verify specializations match AI & ML and Cloud Computing requirements."""
    records = load_catalog(CATALOG_PATH)
    record_map = {r.id: r for r in records}

    ai_rec = record_map["uie-cse-ai-ml-2025"]
    assert ai_rec.specialization == "Artificial Intelligence and Machine Learning"
    assert "artificial-intelligence" in ai_rec.official_source_page
    assert "be-cse-ai-curriculum-2025.pdf" in ai_rec.direct_pdf_url

    cloud_rec = record_map["uie-cse-cloud-computing-2025"]
    assert cloud_rec.specialization == "Cloud Computing"
    assert "cloud-computing" in cloud_rec.official_source_page
    assert "be-cse-cc-curriculum-2025.pdf" in cloud_rec.direct_pdf_url


def test_downloaded_sample_pdfs_exist():
    """Verify downloaded PDFs exist in data/sample_syllabus/ and are valid PDFs."""
    sample_dir = BASE / "data" / "sample_syllabus"

    ai_pdf = sample_dir / "chandigarh_university_ai_ml_2025.pdf"
    assert ai_pdf.exists(), "AI ML syllabus PDF must exist in data/sample_syllabus/"
    assert ai_pdf.stat().st_size > 100_000
    assert ai_pdf.read_bytes().startswith(b"%PDF-")

    cloud_pdf = sample_dir / "chandigarh_university_cloud_computing_2025.pdf"
    assert cloud_pdf.exists(), "Cloud Computing syllabus PDF must exist in data/sample_syllabus/"
    assert cloud_pdf.stat().st_size > 100_000
    assert cloud_pdf.read_bytes().startswith(b"%PDF-")
