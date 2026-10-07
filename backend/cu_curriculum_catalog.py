"""Verified Chandigarh University CSE curriculum sources and safe retrieval."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
from http.client import HTTPResponse
import json
import logging
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    OpenerDirector,
    Request,
    build_opener,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

LOGGER = logging.getLogger(__name__)
ALLOWED_DOMAINS = frozenset({"cuchd.in", "www.cuchd.in"})
MAX_PDF_BYTES = 40 * 1024 * 1024
MAX_HTML_BYTES = 16 * 1024 * 1024
FETCH_TIMEOUT_SECONDS = 30
HTML_CACHE_TTL = timedelta(hours=24)

VerificationStatus = Literal["VERIFIED", "PARTIAL", "UNCLEAR", "NOT_FOUND"]
RetrievalStatus = Literal[
    "NOT_ATTEMPTED", "VERIFIED", "PARTIAL", "UNCLEAR", "NOT_FOUND"
]
SourceType = Literal["OFFICIAL_PDF", "OFFICIAL_HTML"]


class CurriculumSource(BaseModel):
    """A source record whose asserted fields come from the supplied CU catalog."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, max_length=100)
    institute: str | None = Field(default=None, max_length=200)
    department: str = Field(min_length=1, max_length=200)
    degree: str | None = Field(default=None, max_length=200)
    program: str = Field(min_length=1, max_length=250)
    specialization: str = Field(min_length=1, max_length=200)
    entry_type: Literal["REGULAR", "LATERAL_ENTRY"]
    collaboration: str | None = Field(default=None, max_length=100)
    curriculum_year: int | None = Field(default=None, ge=2000, le=2100)
    batch: str | None = Field(default=None, max_length=20)
    title: str = Field(min_length=1, max_length=250)
    official_source_page: str
    direct_pdf_url: str | None = None
    source_type: SourceType
    verified: bool
    status: VerificationStatus
    verification_notes: str = Field(min_length=1, max_length=1000)

    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise ValueError("Catalog IDs must be lowercase kebab-case.")
        return value

    @field_validator("official_source_page", "direct_pdf_url")
    @classmethod
    def validate_official_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        validate_official_url(value)
        return value

    @field_validator("batch")
    @classmethod
    def validate_batch(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"20\d{2}-\d{2}", value):
            raise ValueError("Batch must use the explicitly supplied YYYY-YY format.")
        return value

    @field_validator("status", mode="before")
    @classmethod
    def mark_unversioned_records_unclear(
        cls,
        value: VerificationStatus,
        info: ValidationInfo,
    ) -> VerificationStatus:
        if (
            value == "VERIFIED"
            and info.data.get("curriculum_year") is None
            and info.data.get("batch") is None
        ):
            return "UNCLEAR"
        return value

    @model_validator(mode="after")
    def validate_source_type(self) -> CurriculumSource:
        expected: SourceType = (
            "OFFICIAL_PDF" if self.direct_pdf_url is not None else "OFFICIAL_HTML"
        )
        if self.source_type != expected:
            raise ValueError("Source type must match the presence of a supplied PDF URL.")
        if self.department != "Computer Science and Engineering":
            raise ValueError("Only CSE department records are allowed.")
        return self

    @property
    def curriculum_year_status(self) -> VerificationStatus:
        return "VERIFIED" if self.curriculum_year is not None else "UNCLEAR"

    @property
    def batch_status(self) -> VerificationStatus:
        return "VERIFIED" if self.batch is not None else "UNCLEAR"


@dataclass(frozen=True)
class CurriculumDocument:
    """Validated bytes and provenance for a retrieved official source."""

    record_id: str
    content: bytes
    document_type: SourceType
    source_url: str
    filename: str
    sha256: str
    cache_path: Path
    retrieved_at: str


class CurriculumFetchError(RuntimeError):
    """A source retrieval or validation error with a durable status."""

    def __init__(self, message: str, status: VerificationStatus = "PARTIAL") -> None:
        super().__init__(message)
        self.status = status


def validate_official_url(url: str) -> None:
    """Reject non-HTTPS, non-CU, credential-bearing, or nonstandard-port URLs."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.hostname.casefold() not in ALLOWED_DOMAINS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or not parsed.path.startswith("/")
    ):
        raise ValueError("Curriculum URLs must use HTTPS on cuchd.in or www.cuchd.in.")


class _AllowedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: HTTPResponse,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> Request:
        validate_official_url(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            raise ValueError("The official source returned an unsupported redirect.")
        return redirected


def _open_url(request: Request, timeout: int) -> object:
    opener: OpenerDirector = build_opener(_AllowedRedirectHandler())
    return opener.open(request, timeout=timeout)


@contextmanager
def _database_connection(database_path: Path) -> Iterator[sqlite3.Connection]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS curriculum_sources (
                id TEXT PRIMARY KEY,
                institute TEXT,
                department TEXT NOT NULL,
                degree TEXT,
                program TEXT NOT NULL,
                specialization TEXT NOT NULL,
                entry_type TEXT NOT NULL CHECK(entry_type IN ('REGULAR', 'LATERAL_ENTRY')),
                collaboration TEXT,
                curriculum_year INTEGER,
                batch TEXT,
                title TEXT NOT NULL,
                official_source_page TEXT NOT NULL,
                direct_pdf_url TEXT,
                source_type TEXT NOT NULL CHECK(source_type IN ('OFFICIAL_PDF', 'OFFICIAL_HTML')),
                verified INTEGER NOT NULL CHECK(verified IN (0, 1)),
                verification_notes TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('VERIFIED', 'PARTIAL', 'UNCLEAR', 'NOT_FOUND')),
                retrieval_status TEXT NOT NULL DEFAULT 'NOT_ATTEMPTED'
                    CHECK(retrieval_status IN ('NOT_ATTEMPTED', 'VERIFIED', 'PARTIAL', 'UNCLEAR', 'NOT_FOUND')),
                retrieved_at TEXT,
                document_hash TEXT,
                cache_path TEXT,
                last_error TEXT
            )
            """
        )
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def load_catalog(
    catalog_path: Path,
    database_path: Path | None = None,
) -> list[CurriculumSource]:
    """Load and validate the supplied catalog, syncing records to local SQLite."""
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not load CU CSE catalog at {catalog_path}: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError("CU CSE catalog must contain a JSON list of source records.")
    records = [CurriculumSource.model_validate(item) for item in payload]
    ids = [record.id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("CU CSE catalog contains duplicate record IDs.")
    if database_path is not None:
        sync_catalog_records(records, database_path)
    return records


def sync_catalog_records(
    records: list[CurriculumSource],
    database_path: Path,
) -> None:
    """Persist source metadata without overwriting retrieval/cache provenance."""
    with _database_connection(database_path) as connection:
        connection.executemany(
            """
            INSERT INTO curriculum_sources (
                id, institute, department, degree, program, specialization, entry_type,
                collaboration, curriculum_year, batch, title, official_source_page,
                direct_pdf_url, source_type, verified, verification_notes, status
            ) VALUES (
                :id, :institute, :department, :degree, :program, :specialization,
                :entry_type, :collaboration, :curriculum_year, :batch, :title,
                :official_source_page, :direct_pdf_url, :source_type, :verified,
                :verification_notes, :status
            )
            ON CONFLICT(id) DO UPDATE SET
                institute = excluded.institute,
                department = excluded.department,
                degree = excluded.degree,
                program = excluded.program,
                specialization = excluded.specialization,
                entry_type = excluded.entry_type,
                collaboration = excluded.collaboration,
                curriculum_year = excluded.curriculum_year,
                batch = excluded.batch,
                title = excluded.title,
                official_source_page = excluded.official_source_page,
                direct_pdf_url = excluded.direct_pdf_url,
                source_type = excluded.source_type,
                verified = excluded.verified,
                verification_notes = excluded.verification_notes,
                status = excluded.status
            """,
            [
                record.model_dump(mode="json")
                for record in records
            ],
        )


def _update_retrieval(
    record: CurriculumSource,
    database_path: Path,
    status: VerificationStatus,
    *,
    retrieved_at: str | None = None,
    document_hash: str | None = None,
    cache_path: Path | None = None,
    last_error: str | None = None,
) -> None:
    with _database_connection(database_path) as connection:
        connection.execute(
            """
            UPDATE curriculum_sources
            SET retrieval_status = ?, retrieved_at = ?, document_hash = ?,
                cache_path = ?, last_error = ?
            WHERE id = ?
            """,
            (
                status,
                retrieved_at,
                document_hash,
                str(cache_path) if cache_path else None,
                last_error,
                record.id,
            ),
        )


def _cached_document(
    record: CurriculumSource,
    cache_dir: Path,
    database_path: Path,
) -> CurriculumDocument | None:
    source_url = record.direct_pdf_url or record.official_source_page
    with _database_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, retrieved_at, document_hash, cache_path
            FROM curriculum_sources
            WHERE retrieval_status = 'VERIFIED'
              AND document_hash IS NOT NULL
              AND cache_path IS NOT NULL
              AND (direct_pdf_url = ? OR (direct_pdf_url IS NULL AND official_source_page = ?))
            """,
            (record.direct_pdf_url, record.official_source_page),
        ).fetchall()
    root = cache_dir.resolve()
    for row in rows:
        path = Path(row["cache_path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            continue
        retrieved_at = row["retrieved_at"] or ""
        if record.source_type == "OFFICIAL_HTML" and retrieved_at:
            try:
                cached_time = datetime.fromisoformat(retrieved_at)
            except ValueError:
                continue
            if datetime.now(UTC) - cached_time > HTML_CACHE_TTL:
                continue
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != row["document_hash"]:
            continue
        if record.source_type == "OFFICIAL_PDF" and not content.startswith(b"%PDF-"):
            continue
        _update_retrieval(
            record,
            database_path,
            "VERIFIED",
            retrieved_at=retrieved_at,
            document_hash=digest,
            cache_path=path,
        )
        return CurriculumDocument(
            record_id=record.id,
            content=content,
            document_type=record.source_type,
            source_url=source_url,
            filename=f"{record.id}.{'pdf' if record.source_type == 'OFFICIAL_PDF' else 'html'}",
            sha256=digest,
            cache_path=path,
            retrieved_at=retrieved_at,
        )
    return None


def fetch_curriculum(
    record: CurriculumSource,
    *,
    cache_dir: Path,
    database_path: Path,
    timeout: int = FETCH_TIMEOUT_SECONDS,
) -> CurriculumDocument:
    """Fetch one allowlisted CU PDF/HTML source and cache verified bytes by SHA-256."""
    source_url = record.direct_pdf_url or record.official_source_page
    validate_official_url(source_url)
    if record.source_type == "OFFICIAL_PDF" and not record.direct_pdf_url:
        raise ValueError("This catalog record has no verified direct PDF URL.")
    sync_catalog_records([record], database_path)

    cached = _cached_document(record, cache_dir, database_path)
    if cached is not None:
        return cached

    request = Request(
        source_url,
        headers={
            "Accept": (
                "application/pdf"
                if record.source_type == "OFFICIAL_PDF"
                else "text/html,application/xhtml+xml"
            ),
            "User-Agent": "CurriculumDriftAudit/1.0",
        },
    )
    try:
        response = _open_url(request, timeout)
        with response as result:
            status_code = result.getcode()
            final_url = result.geturl()
            validate_official_url(final_url)
            if status_code != 200:
                raise CurriculumFetchError(
                    f"CU source returned HTTP {status_code}.",
                    "NOT_FOUND" if status_code == 404 else "PARTIAL",
                )
            maximum = (
                MAX_PDF_BYTES
                if record.source_type == "OFFICIAL_PDF"
                else MAX_HTML_BYTES
            )
            content = result.read(maximum + 1)
            if len(content) > maximum:
                raise CurriculumFetchError(
                    "CU curriculum response exceeded the permitted size limit."
                )
            content_type = result.headers.get("Content-Type", "").casefold()
    except HTTPError as exc:
        status: VerificationStatus = "NOT_FOUND" if exc.code == 404 else "PARTIAL"
        error = CurriculumFetchError(f"CU source returned HTTP {exc.code}.", status)
        _update_retrieval(record, database_path, status, last_error=str(error))
        raise error from exc
    except CurriculumFetchError as exc:
        _update_retrieval(
            record, database_path, exc.status, last_error=str(exc)
        )
        raise
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        error = CurriculumFetchError(f"Could not safely retrieve CU source: {exc}")
        _update_retrieval(record, database_path, error.status, last_error=str(error))
        raise error from exc

    if record.source_type == "OFFICIAL_PDF":
        if not content.startswith(b"%PDF-"):
            error = CurriculumFetchError(
                "The supplied CU PDF URL did not return a PDF document."
            )
            _update_retrieval(record, database_path, error.status, last_error=str(error))
            raise error
    elif (
        "text/html" not in content_type
        and "application/xhtml+xml" not in content_type
        and b"<html" not in content[:4096].lower()
        and b"<!doctype html" not in content[:4096].lower()
    ):
        error = CurriculumFetchError(
            "The supplied CU source page did not return HTML."
        )
        _update_retrieval(record, database_path, error.status, last_error=str(error))
        raise error

    digest = hashlib.sha256(content).hexdigest()
    cache_dir.mkdir(parents=True, exist_ok=True)
    resolved_root = cache_dir.resolve()
    suffix = "pdf" if record.source_type == "OFFICIAL_PDF" else "html"
    destination = (resolved_root / f"{digest}.{suffix}").resolve()
    if not destination.is_relative_to(resolved_root):
        raise RuntimeError("Generated curriculum cache path escaped its configured root.")
    if not destination.exists():
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{digest}.",
                suffix=".tmp",
                dir=resolved_root,
                delete=False,
            ) as output:
                temporary_path = Path(output.name)
                output.write(content)
            temporary_path.replace(destination)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    retrieved_at = datetime.now(UTC).isoformat()
    _update_retrieval(
        record,
        database_path,
        "VERIFIED",
        retrieved_at=retrieved_at,
        document_hash=digest,
        cache_path=destination,
    )
    LOGGER.info(
        "Retrieved official CU curriculum record %s (%s, sha256=%s)",
        record.id,
        record.source_type,
        digest,
    )
    return CurriculumDocument(
        record_id=record.id,
        content=content,
        document_type=record.source_type,
        source_url=source_url,
        filename=f"{record.id}.{suffix}",
        sha256=digest,
        cache_path=destination,
        retrieved_at=retrieved_at,
    )
