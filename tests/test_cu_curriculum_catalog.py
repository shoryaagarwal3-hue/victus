import hashlib
import io
import json
from collections import Counter
from email.message import Message
from pathlib import Path

from fpdf import FPDF
import pytest

from backend import cu_curriculum_catalog as catalog
from backend.models import CourseSubject
from backend.parser import parse_html, parse_syllabus


CATALOG_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "cu_cse_curriculum_catalog.json"
)


def _catalog_records(tmp_path: Path) -> list[catalog.CurriculumSource]:
    return catalog.load_catalog(
        CATALOG_PATH,
        database_path=tmp_path / "curriculum.sqlite3",
    )


def test_catalog_records_are_cse_only_and_use_official_cu_urls(tmp_path: Path) -> None:
    records = _catalog_records(tmp_path)

    assert len(records) == 36
    assert all(record.department == "Computer Science and Engineering" for record in records)
    assert all(record.verified for record in records)
    assert all(record.status in {"VERIFIED", "UNCLEAR"} for record in records)
    assert all(
        catalog.urlsplit(url).hostname in catalog.ALLOWED_DOMAINS
        for record in records
        for url in (record.official_source_page, record.direct_pdf_url)
        if url
    )
    assert Counter(record.source_type for record in records) == {
        "OFFICIAL_PDF": 9,
        "OFFICIAL_HTML": 27,
    }
    assert len({record.direct_pdf_url for record in records if record.direct_pdf_url}) == 6


def test_regular_general_cse_batches_and_verified_specialization_sources(
    tmp_path: Path,
) -> None:
    records = _catalog_records(tmp_path)
    by_id = {record.id: record for record in records}
    general_batches = {
        record.batch
        for record in records
        if record.specialization == "General CSE"
        and record.entry_type == "REGULAR"
        and record.institute == "University Institute of Engineering (UIE)"
    }

    assert general_batches == {
        "2018-22",
        "2019-23",
        "2020-24",
        "2021-25",
        "2022-26",
        "2023-27",
        "2024-28",
        "2025-29",
    }
    assert by_id["uie-cse-2025-29"].curriculum_year is None
    assert by_id["uie-cse-2025-29"].curriculum_year_status == "UNCLEAR"
    assert by_id["uie-full-stack-2026"].source_type == "OFFICIAL_PDF"
    assert by_id["uie-cse-csbs-2025"].source_type == "OFFICIAL_PDF"
    assert by_id["apex-ibm-data-science-2026"].source_type == "OFFICIAL_PDF"
    assert by_id["apex-ibm-aiml-2026"].source_type == "OFFICIAL_PDF"
    assert by_id["apex-ibm-cyber-security-2025"].specialization == "IBM Cyber Security"


def test_lateral_entry_and_unclear_years_remain_explicit(tmp_path: Path) -> None:
    records = _catalog_records(tmp_path)
    lateral = [record for record in records if record.entry_type == "LATERAL_ENTRY"]
    unclear_year_ids = {
        "apex-information-security",
        "apex-iot",
        "apex-blockchain",
        "apex-devops",
    }

    assert len(lateral) == 7
    assert len(records) - len(lateral) == 29
    assert sum(record.status == "UNCLEAR" for record in records) == 17
    assert all(record.curriculum_year is None for record in records if record.id in unclear_year_ids)
    assert all(
        next(record for record in records if record.id == record_id).curriculum_year_status
        == "UNCLEAR"
        for record_id in unclear_year_ids
    )
    gaming = next(record for record in records if record.id == "uie-gaming-graphics-2021")
    assert gaming.curriculum_year == 2021
    assert gaming.batch is None
    assert gaming.batch_status == "UNCLEAR"
    assert not any(record.batch == "2021-25" for record in records if record.id == gaming.id)


def test_duplicate_or_external_catalog_urls_are_rejected(tmp_path: Path) -> None:
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    raw[0]["direct_pdf_url"] = "https://not-cuchd.example/fabricated.pdf"
    raw[0]["source_type"] = "OFFICIAL_PDF"
    bad_path = tmp_path / "bad-catalog.json"
    bad_path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError):
        catalog.load_catalog(bad_path)


def test_redirect_handler_rejects_hosts_outside_cu_allowlist() -> None:
    handler = catalog._AllowedRedirectHandler()
    request = catalog.Request("https://www.cuchd.in/page")

    with pytest.raises(ValueError, match="HTTPS on cuchd.in"):
        handler.redirect_request(
            request,
            io.BytesIO(),
            302,
            "Found",
            Message(),
            "https://evil.example/steal",
        )


class _FakeResponse:
    def __init__(self, content: bytes, content_type: str, url: str) -> None:
        self._content = content
        self._url = url
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def getcode(self) -> int:
        return 200

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        return self._content[:size]


def _small_pdf() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(
        0,
        8,
        "Course Code: CS501\nCourse Name: Network Security\nCredits: 4\n"
        "Semester: 5\nUNIT I: Secure Networks",
    )
    return bytes(pdf.output())

def test_verified_pdf_is_hashed_cached_and_passed_to_existing_parser(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "curriculum.sqlite3"
    records = catalog.load_catalog(CATALOG_PATH, database_path=database)
    record = next(item for item in records if item.id == "uie-full-stack-2026")
    content = _small_pdf()
    monkeypatch.setattr(
        catalog,
        "_open_url",
        lambda request, timeout: _FakeResponse(
            content, "application/pdf", record.direct_pdf_url or ""
        ),
    )

    document = catalog.fetch_curriculum(
        record,
        cache_dir=tmp_path / "cache",
        database_path=database,
    )
    parsed = parse_syllabus(io.BytesIO(document.content))

    assert document.sha256 == hashlib.sha256(content).hexdigest()
    assert document.cache_path.exists()
    assert parsed.subjects
    assert any(isinstance(subject, CourseSubject) for subject in parsed.subjects)
    assert any(subject.course_code == "CS501" for subject in parsed.subjects)


def test_same_bytes_from_distinct_official_pdf_urls_share_sha_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "curriculum.sqlite3"
    records = catalog.load_catalog(CATALOG_PATH, database_path=database)
    first = next(item for item in records if item.id == "uie-full-stack-2026")
    second = first.model_copy(
        update={
            "id": "synthetic-same-bytes",
            "direct_pdf_url": "https://www.cuchd.in/test/same-document.pdf",
            "title": "Synthetic duplicate-content test",
        }
    )
    content = b"%PDF-1.7\nminimal test fixture\n%%EOF\n"
    catalog.sync_catalog_records([second], database)
    calls = 0

    def open_url(request: catalog.Request, timeout: int) -> _FakeResponse:
        nonlocal calls
        calls += 1
        return _FakeResponse(content, "application/pdf", request.full_url)

    monkeypatch.setattr(catalog, "_open_url", open_url)
    cache_dir = tmp_path / "cache"

    first_document = catalog.fetch_curriculum(
        first, cache_dir=cache_dir, database_path=database
    )
    second_document = catalog.fetch_curriculum(
        second, cache_dir=cache_dir, database_path=database
    )

    assert calls == 2
    assert first_document.sha256 == second_document.sha256
    assert first_document.cache_path == second_document.cache_path
    assert len(list(cache_dir.glob("*.pdf"))) == 1


def test_non_pdf_content_is_rejected_and_failure_status_is_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "curriculum.sqlite3"
    records = catalog.load_catalog(CATALOG_PATH, database_path=database)
    record = next(item for item in records if item.id == "uie-full-stack-2026")
    monkeypatch.setattr(
        catalog,
        "_open_url",
        lambda request, timeout: _FakeResponse(
            b"not a pdf", "text/plain", record.direct_pdf_url or ""
        ),
    )

    with pytest.raises(catalog.CurriculumFetchError, match="did not return a PDF"):
        catalog.fetch_curriculum(
            record, cache_dir=tmp_path / "cache", database_path=database
        )

    with catalog._database_connection(database) as connection:
        state = connection.execute(
            "SELECT retrieval_status FROM curriculum_sources WHERE id = ?",
            (record.id,),
        ).fetchone()
    assert state["retrieval_status"] == "PARTIAL"


def test_official_html_flows_through_existing_deterministic_parser() -> None:
    html = """
    <html><head><script>ignore fake course</script></head><body>
      <h1>Official Curriculum</h1>
      <p>Course Code: CS401</p><p>Course Name: Operating Systems</p>
      <p>Credits: 3</p><p>UNIT I: Process Scheduling</p>
    </body></html>
    """

    corpus = parse_html(html, source_name="official_cse.html")

    assert corpus.source_name == "official_cse.html"
    assert any(subject.course_code == "CS401" for subject in corpus.subjects)
    assert any(subject.course_name == "Operating Systems" for subject in corpus.subjects)


def test_html_curriculum_table_is_scoped_to_the_selected_batch() -> None:
    html = """
    <h2>Scheme for BE (CSE) - Batch 2025-29</h2>
    <h3>Semester - 1st</h3>
    <table>
      <tr><th>Course Code</th><th>Course Name</th><th>L</th><th>T</th>
          <th>P</th><th>S</th><th>C</th><th>CH</th></tr>
      <tr><td>25CSH-101</td><td>Logical Thinking and Problem Solving</td>
          <td>0</td><td>2</td><td>4</td><td>0</td><td>4</td><td>6</td></tr>
    </table>
    <h2>Scheme for BE (CSE) - Batch 2024-28</h2>
    <h3>Semester - 1st</h3>
    <table>
      <tr><th>Course Code</th><th>Course Name</th><th>L</th><th>T</th>
          <th>P</th><th>S</th><th>C</th><th>CH</th></tr>
      <tr><td>24CSH-101</td><td>Old Batch Subject</td>
          <td>0</td><td>2</td><td>4</td><td>0</td><td>3</td><td>6</td></tr>
    </table>
    """

    corpus = parse_html(
        html,
        source_name="official_cse.html",
        curriculum_batch="2025-29",
    )

    assert len(corpus.subjects) == 1
    assert corpus.subjects[0].course_code == "25CSH-101"
    assert corpus.subjects[0].course_name == "Logical Thinking and Problem Solving"
    assert corpus.subjects[0].credits == 4.0
    assert corpus.subjects[0].semester == "Semester 1"
