"""PDF syllabus extraction with structured subject parsing and diagnostics.
Supports multi-course curricula, single-course syllabi, institutional lecture plans (e.g. Chandigarh University), and robust fallback.
Deterministic extraction only: does not hallucinate course codes or titles.
"""
import re
import hashlib
from html.parser import HTMLParser
from pathlib import Path
from typing import BinaryIO, Union
from .models import Corpus, CourseSubject, CourseUnit

COURSE_CODE_PATTERNS = [
    re.compile(r"(?im)\b(?:course|subject|paper)\s+code[ \t]*[:\-–]?[ \t]*([A-Z0-9\-_/]{3,15})\b"),
    re.compile(r"(?im)^\s*(?:course|subject|paper)?\s*(?:code|no\.?)[ \t]*[:\-–][ \t]*([A-Z0-9\-_/]{3,15})\b"),
    re.compile(
        r"(?im)^\s*((?:[A-Z]{2,5}\s*[-/]?\s*\d{2,4}[A-Z0-9X]{0,4}|"
        r"\d{2}[A-Z]{2,5}[-/]?\d{1,4}[A-Z0-9X]{0,4}))[ \t]*(?:[:\-–][ \t]*|[ \t]+)"
        r"([A-Z][A-Za-z0-9][^\r\n]{2,100})"
    ),
]
COURSE_CODE_ONLY_PATTERN = re.compile(
    r"(?i)^(?:[A-Z]{2,5}\s*[-/]?\s*\d{2,4}[A-Z0-9X]{0,4}|"
    r"\d{2}[A-Z]{2,5}[-/]?\d{1,4}[A-Z0-9X]{0,4})$"
)
COURSE_TYPE_VALUE_PATTERN = re.compile(
    r"(?i)^(?:core|professional core|elective|professional elective|open elective|"
    r"program(?:me)? elective|university elective|compulsory|mandatory|"
    r"major core|minor core|major elective|minor elective|"
    r"ability enhancement|skill enhancement|audit course)$"
)

COURSE_TITLE_PATTERNS = [
    re.compile(r"(?im)\b(?:course|subject|paper)\s+(?:name|title)[ \t]*[:\-–]?[ \t]*([A-Za-z0-9\s&,/()-]+?)(?=[ \t]+(?:course\s+code|code|credits?|$)|[\r\n])"),
    re.compile(r"(?im)^\s*(?:course|subject|paper)\s*(?:title|name)[ \t]*[:\-–]?[ \t]*([^\r\n]{3,80})"),
    re.compile(r"(?im)^\s*(?:title|subject)[ \t]*[:\-–][ \t]*([^\r\n]{3,80})"),
]

CREDIT_PATTERNS = [
    re.compile(r"(?im)\b(?:credits?|credit\s+points?|total\s+credits?)[ \t]*[:\-–]?[ \t]*(\d+(?:\.\d+)?)\b"),
    re.compile(r"(?im)\bL\s*[:\-–\s]\s*(\d+)\s*T\s*[:\-–\s]\s*(\d+)\s*P\s*[:\-–\s]\s*(\d+)\s*C\s*[:\-–\s]\s*(\d+(?:\.\d+)?)\b"),
    re.compile(r"(?im)\b(?:L-T-P-C|LTPC)[ \t]*[:\-–]?[ \t]*(\d+)[ \t]*[-:\s][ \t]*(\d+)[ \t]*[-:\s][ \t]*(\d+)[ \t]*[-:\s][ \t]*(\d+(?:\.\d+)?)\b"),
]

SEMESTER_PATTERN = re.compile(r"(?im)\b(?:semester|sem)\s*[:\-–]?\s*([IVX\d]+)\b")
COURSE_TYPE_PATTERN = re.compile(r"(?im)\b(?:course\s+type|category)\s*[:\-–]?\s*([A-Za-z\s]+?)(?:[;\n\r]|$)")
MULTI_COURSE_CATALOG_CUE = re.compile(
    r"(?i)\b(?:program(?:me)? structure|curriculum structure|scheme of studies?|"
    r"professional electives?|elective catalog|elective basket|course catalog|"
    r"list of (?:courses|subjects)|semester[- ]wise (?:course|curriculum)|"
    r"credit distribution)\b"
)


def _normalize(text: str) -> str:
    """Normalize ligatures, unicode hyphenations, and erratic spacing."""
    if not text:
        return ""
    text = text.replace("\u00ad", "").replace("\uFB01", "fi").replace("\uFB02", "fl")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", re.sub(r"-\s*\n", "", text)).strip()


def _extract_units(text: str) -> tuple[list[CourseUnit], list[str]]:
    """Extract unit/module breakdown and all unit topic lines."""
    units: list[CourseUnit] = []
    all_topics: list[str] = []
    
    unit_pattern = re.compile(r"(?im)^\s*(?:unit|module)\s*[-:]?\s*([ivx\d]+)\s*[:\-–]?\s*(.*)$")
    # Table chapter pattern (e.g. Chandigarh University: "1 1 Chapter 1.1 - Topic...")
    chapter_row_pattern = re.compile(r"(?im)^\s*(\d+)\s+\d+\s+Chapter\s*[\d\.]*\s*[-:]?\s*([^\n\r]+)")
    
    lines = text.splitlines()
    
    current_unit_no: int | str = 1
    current_unit_title: str = ""
    current_topics: list[str] = []
    in_unit = False
    section_boundary = re.compile(
        r"(?i)^\s*(?:course\s+outcomes?|learning\s+outcomes?|"
        r"text\s*books?|references?)\s*:?\s*$"
    )

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        
        match = unit_pattern.match(line_clean)
        ch_match = chapter_row_pattern.match(line_clean) if not match else None

        if match:
            if in_unit and (current_unit_title or current_topics):
                units.append(CourseUnit(unit_no=current_unit_no, title=current_unit_title, topics=current_topics))
                all_topics.extend(current_topics)
            in_unit = True
            current_unit_no = match.group(1).strip()
            current_unit_title = match.group(2).strip() or f"Unit {current_unit_no}"
            current_topics = []
        elif ch_match:
            u_no = ch_match.group(1).strip()
            topic_str = ch_match.group(2).strip()
            # Clean trailing pedagogical/book artifacts
            topic_clean = re.sub(r"[,;]?\s*[TR]-Database.*$", "", topic_str).strip()
            topic_clean = re.sub(r"[,;]?\s*PPT.*$", "", topic_clean).strip()
            if not in_unit or str(current_unit_no) != str(u_no):
                if in_unit and (current_unit_title or current_topics):
                    units.append(CourseUnit(unit_no=current_unit_no, title=current_unit_title, topics=current_topics))
                    all_topics.extend(current_topics)
                in_unit = True
                current_unit_no = u_no
                current_unit_title = f"Unit {u_no}"
                current_topics = []
            if topic_clean and topic_clean not in current_topics:
                current_topics.append(topic_clean)
        elif in_unit:
            if section_boundary.match(line_clean):
                units.append(CourseUnit(unit_no=current_unit_no, title=current_unit_title, topics=current_topics))
                all_topics.extend(current_topics)
                in_unit = False
                current_topics = []
            else:
                subtopics = [t.strip() for t in re.split(r"[,;•\t]+", line_clean) if len(t.strip()) > 3]
                if subtopics:
                    current_topics.extend(subtopics)
                else:
                    current_topics.append(line_clean)
    
    if in_unit and (current_unit_title or current_topics):
        units.append(CourseUnit(unit_no=current_unit_no, title=current_unit_title, topics=current_topics))
        all_topics.extend(current_topics)
        
    return units, all_topics


def _extract_learning_outcomes(text: str) -> list[str]:
    """Detect NBA/NAAC Course Outcomes (CO1, CO2, etc.)."""
    outcomes: list[str] = []
    # Matches CO1:, CO1 -, CO1. or CO1 [space]
    co_pattern = re.compile(r"(?im)^\s*(co\s*[\d]+|course\s+outcome\s*[\d]+)[ \t]*[:\-–.]?[ \t]+(.+)$")
    
    in_co_block = False
    co_block_header = re.compile(r"(?im)^\s*(?:course\s+outcomes?|course\s+outcome|learning\s+outcomes?)\b")
    
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        co_match = co_pattern.match(clean)
        if co_match:
            outcomes.append(co_match.group(2).strip())
            continue
        if co_block_header.search(clean):
            in_co_block = True
            continue
        if in_co_block:
            if re.match(
                r"(?im)^\s*(?:unit\s+[ivx\d]+|lecture\s+plan|text\s*books?|references?)\b",
                clean,
            ) or re.fullmatch(r"[A-Z][A-Z\s/&-]{2,}:?", clean):
                in_co_block = False
            elif re.match(r"^\s*[\d•\-*]\s*[\.)\-]?\s*(.+)$", clean):
                sub = re.sub(r"^\s*[\d•\-*]\s*[\.)\-]?\s*", "", clean).strip()
                if len(sub) > 10:
                    outcomes.append(sub)
    return outcomes


def _calculate_confidence(
    code: str,
    name: str,
    credits_val: float | None,
    units: list[CourseUnit],
    outcomes: list[str],
    semester: str = "N/A",
    course_type: str = "Unspecified",
) -> tuple[float, str, list[str]]:
    score = 0.0
    reasons: list[str] = []
    
    if code and code != "N/A":
        score += 0.20
    else:
        reasons.append("Course code not explicitly detected in source")

    if name and name != "Unnamed Subject" and not name.startswith("Document"):
        score += 0.25
    else:
        reasons.append("Course title not cleanly delineated")

    if credits_val is not None and credits_val > 0:
        score += 0.15
    else:
        reasons.append("Credits or L-T-P scheme not detected")

    if units:
        score += 0.20
    else:
        reasons.append("Unit/Module hierarchy not detected")

    if outcomes:
        score += 0.15
    else:
        reasons.append("Course outcomes (COs) not explicitly stated")

    if semester and semester != "N/A":
        score += 0.05
    else:
        reasons.append("Semester not explicitly detected")

    if course_type and course_type != "Unspecified":
        score += 0.05
    else:
        reasons.append("Course category/type not explicitly detected")

    score = round(min(1.0, score), 2)
    if score >= 0.75:
        level = "HIGH"
    elif score >= 0.50:
        level = "MEDIUM"
    elif score >= 0.20:
        level = "LOW"
    else:
        level = "INSUFFICIENT EVIDENCE"
        
    return score, level, reasons


def _extract_subject_from_block(text: str, source_pages: list[int], fallback_title: str = "") -> CourseSubject:
    """Extract a CourseSubject from a text chunk representing a subject."""
    code = "N/A"
    name = "Unnamed Subject"
    
    # 1. Look for code
    for pat in COURSE_CODE_PATTERNS:
        match = pat.search(text)
        if match:
            if len(match.groups()) == 2:
                code = match.group(1).strip()
                name = match.group(2).strip()
            else:
                code = match.group(1).strip()
            break
            
    # 2. Look for name if not found
    if name == "Unnamed Subject" or not name:
        for pat in COURSE_TITLE_PATTERNS:
            match = pat.search(text)
            if match:
                cand_name = match.group(1).strip()
                # Check if next line contains word continuation (e.g. 'System' after 'Database Management')
                lines = text.splitlines()
                for idx, line in enumerate(lines):
                    if cand_name in line and idx + 1 < len(lines):
                        next_line = lines[idx + 1].strip()
                        if next_line in ("System", "Systems", "Security", "Engineering", "Networks", "Lab", "Laboratory"):
                            cand_name = f"{cand_name} {next_line}"
                        break
                name = cand_name
                break

    if name == "Unnamed Subject" and fallback_title:
        name = fallback_title

    # 3. Credits and course type
    credits_val: float | None = None
    course_type: str = "Unspecified"

    # Read credits from the institutional table without splitting course content.
    lines = text.splitlines()
    for idx, l in enumerate(lines[:-1]):
        if "Credit" in l:
            header_clean = re.sub(r"Self Study", "Self_Study", l)
            header_clean = re.sub(r"Subject Type", "Subject_Type", header_clean).split()
            val_clean = lines[idx + 1].split()
            if len(header_clean) == len(val_clean):
                data_map = dict(zip(header_clean, val_clean))
                try:
                    if "Credit" in data_map:
                        credits_val = float(data_map["Credit"])
                except (ValueError, TypeError):
                    pass
            break

    # Standard regex credit fallback if table not found
    if credits_val is None:
        for pat in CREDIT_PATTERNS:
            match = pat.search(text)
            if match:
                try:
                    if len(match.groups()) == 4:
                        credits_val = float(match.group(4))
                    else:
                        credits_val = float(match.group(1))
                    break
                except (ValueError, IndexError):
                    pass

    # 4. Semester
    sem_match = SEMESTER_PATTERN.search(text)
    semester = f"Semester {sem_match.group(1)}" if sem_match else "N/A"

    # 5. Course Type
    type_match = COURSE_TYPE_PATTERN.search(text)
    if type_match:
        course_type = _normalized_course_type(type_match.group(1)) or "Unspecified"
    if course_type == "Unspecified":
        for idx, line in enumerate(lines):
            if re.search(r"(?i)\bcourse\s+type\b", line):
                inline_value = re.split(r"(?i)\bcourse\s+type\b", line, maxsplit=1)[1]
                inline_value = inline_value.lstrip(" :\t-")
                candidate = _normalized_course_type(inline_value)
                if candidate is None and idx + 1 < len(lines):
                    candidate = _normalized_course_type(lines[idx + 1])
                if candidate:
                    course_type = candidate
                    break

    # 6. Units and topics
    units, topics = _extract_units(text)

    # 7. Learning outcomes
    outcomes = _extract_learning_outcomes(text)

    # 8. Confidence
    conf_score, conf_level, reasons = _calculate_confidence(
        code, name, credits_val, units, outcomes, semester, course_type
    )

    corpus_parts = [
        name,
        *topics,
        *[unit.title for unit in units],
        *[topic for unit in units for topic in unit.topics],
        *outcomes,
    ]
    corpus_text = "\n".join(dict.fromkeys(part.strip() for part in corpus_parts if part.strip()))

    return CourseSubject(
        course_code=code,
        course_name=name,
        credits=credits_val,
        semester=semester,
        course_type=course_type,
        units=units,
        topics=topics,
        corpus_text=corpus_text,
        learning_outcomes=outcomes,
        source_pages=source_pages,
        extraction_confidence=conf_score,
        confidence_level=conf_level,
        low_confidence_reasons=reasons,
    )


def _table_cell(row: list[str | None], index: int | None) -> str:
    if index is None or index >= len(row) or row[index] is None:
        return ""
    return re.sub(r"\s+", " ", str(row[index])).strip()


def _normalized_course_type(value: str) -> str | None:
    """Keep explicit recognized category values; never mistake a title for its type."""
    normalized = re.sub(r"\s+", " ", value).strip()
    if COURSE_TYPE_VALUE_PATTERN.fullmatch(normalized):
        return normalized
    for prefix in ("major core", "minor core", "major elective", "minor elective"):
        if re.match(rf"(?i)^{re.escape(prefix)}\b", normalized):
            return prefix.title()
    if re.fullmatch(
        r"(?i)(?:professional|open|program(?:me)?|university)?\s*elective[\s\-–]*[ivx\d]*",
        normalized,
    ):
        return normalized
    return None


def _is_outcome_code(code: str) -> bool:
    """Exclude program and course outcome labels from course segmentation."""
    return bool(re.match(r"(?i)^(?:PO|PEO|PSO|CO)\d+$", code.strip()))


def _course_table_records(
    page_tables: list[tuple[int, list[list[list[str | None]]]]],
    curriculum_batch: str | None = None,
) -> list[CourseSubject]:
    """Extract course records from PDF tables with explicit row/column provenance."""
    records: list[CourseSubject] = []
    active_semester = "N/A"
    active_batch: str | None = None
    def add_record(
        page_number: int,
        code: str,
        name: str,
        credits: float | None,
        semester: str,
        course_type: str,
    ) -> None:
        name = re.sub(r"\s+", " ", name).strip()
        if not name or name.casefold() in {
            "course name",
            "subject name",
            "title",
            "program electives",
        }:
            return
        if re.fullmatch(r"\d+(?:\.\d+)?", name):
            return
        if course_type == "Unspecified" and re.search(r"\belective\b", name, re.I):
            course_type = "Elective"
        confidence, level, reasons = _calculate_confidence(
            code or "N/A", name, credits, [], [], semester, course_type
        )
        records.append(
            CourseSubject(
                course_code=code or "N/A",
                course_name=name,
                credits=credits,
                semester=semester,
                course_type=course_type,
                source_pages=[page_number],
                extraction_confidence=confidence,
                confidence_level=level,
                low_confidence_reasons=reasons,
            )
        )

    for page_number, tables in page_tables:
        for table in tables:
            cells_by_row = [
                [_table_cell(row, index) for index in range(len(row))]
                for row in table
            ]
            semester_for_table = active_semester
            for cells in cells_by_row:
                for cell in cells:
                    batch_marker = re.fullmatch(
                        r"(?i)batch[\s\-:]*((?:20\d{2}-\d{2}))", cell
                    )
                    if batch_marker:
                        active_batch = batch_marker.group(1)
                    if cell.casefold() == "c":
                        # In CU's code/name/L-T-P-S-C-CH table C is its credit column.
                        continue
                    semester_marker = re.fullmatch(
                        r"(?i)semester[\s\-:]*([ivx\d]+)(?:st|nd|rd|th)?", cell
                    )
                    if semester_marker:
                        active_semester = f"Semester {semester_marker.group(1)}"
                        semester_for_table = active_semester

            if curriculum_batch and active_batch != curriculum_batch:
                continue

            header_row = -1
            headers: dict[str, int] = {}
            for row_index, cells in enumerate(cells_by_row):
                lowered = [cell.casefold() for cell in cells]
                indices: dict[str, int] = {}
                for index, cell in enumerate(lowered):
                    if "semester" in cell:
                        indices["semester"] = index
                    if "course name" in cell or "subject name" in cell or cell in {
                        "title",
                        "subject",
                    }:
                        indices["name"] = index
                    if "course code" in cell or "subject code" in cell or cell == "code":
                        indices["code"] = index
                    if "course category" in cell or "course type" in cell or cell in {
                        "category",
                        "type",
                    }:
                        indices["type"] = index
                    if "credit" in cell:
                        indices["credits"] = index
                    if cell == "c":
                        indices["credits"] = index
                if "name" in indices and (
                    "credits" in indices or "semester" in indices or "code" in indices
                ):
                    header_row = row_index
                    headers = indices
                    break

            if header_row >= 0:
                for cells in cells_by_row[header_row + 1 :]:
                    if not any(cells):
                        continue
                    code = _table_cell(cells, headers.get("code"))
                    name = _table_cell(cells, headers.get("name"))
                    if cells and COURSE_CODE_ONLY_PATTERN.fullmatch(cells[0]):
                        code = cells[0]
                        if len(cells) > 1:
                            name = cells[1]

                    raw_credits = _table_cell(cells, headers.get("credits"))
                    try:
                        credits = float(raw_credits) if raw_credits else None
                    except ValueError:
                        credits = None

                    semester = semester_for_table
                    raw_semester = _table_cell(cells, headers.get("semester"))
                    if raw_semester:
                        semester = (
                            f"Semester {raw_semester}"
                            if raw_semester.isdigit()
                            or re.fullmatch(r"[IVX]+", raw_semester, re.I)
                            else raw_semester
                        )
                    course_type = _normalized_course_type(
                        _table_cell(cells, headers.get("type"))
                    ) or "Unspecified"
                    if code and not COURSE_CODE_ONLY_PATTERN.fullmatch(code):
                        code = ""
                    add_record(page_number, code, name, credits, semester, course_type)
                continue

            coded_rows = [
                cells
                for cells in cells_by_row
                if len(cells) >= 3
                and COURSE_CODE_ONLY_PATTERN.fullmatch(cells[0])
                and cells[1]
            ]
            if len(coded_rows) >= 2:
                for cells in coded_rows:
                    try:
                        credits = float(cells[-1])
                    except ValueError:
                        credits = None
                    add_record(
                        page_number,
                        cells[0],
                        cells[1],
                        credits,
                        semester_for_table,
                        "Unspecified",
                    )
                continue

            elective_rows = [
                cells
                for cells in cells_by_row
                if len(cells) >= 4
                and cells[0].isdigit()
                and cells[1]
                and _normalized_course_type(cells[2]) is not None
                and re.fullmatch(r"\d+(?:\.\d+)?", cells[3])
            ]
            if len(elective_rows) >= 2:
                for cells in elective_rows:
                    add_record(
                        page_number,
                        "",
                        cells[1],
                        float(cells[3]),
                        f"Semester {cells[0]}",
                        _normalized_course_type(cells[2]) or "Unspecified",
                    )

    return records


def _merge_table_records(
    extracted_subjects: list[CourseSubject],
    table_records: list[CourseSubject],
) -> list[CourseSubject]:
    """Merge tabular metadata into text-derived subjects and retain catalog-only rows."""
    subjects = list(extracted_subjects)
    by_code: dict[str, list[CourseSubject]] = {}
    for subject in subjects:
        if subject.course_code != "N/A":
            by_code.setdefault(subject.course_code.casefold(), []).append(subject)
    by_name_semester = {
        (subject.course_name.casefold(), subject.semester.casefold()): subject
        for subject in subjects
    }

    for table_subject in table_records:
        if table_subject.course_code != "N/A":
            candidates = by_code.get(table_subject.course_code.casefold(), [])
            target = next(
                (
                    subject
                    for subject in candidates
                    if subject.course_name.casefold()
                    == table_subject.course_name.casefold()
                ),
                None,
            )
            if target is None and not re.search(r"(?i)x", table_subject.course_code):
                target = next(
                    (
                        subject
                        for subject in candidates
                        if subject.course_name == "Unnamed Subject"
                    ),
                    candidates[0] if len(candidates) == 1 else None,
                )
        else:
            target = by_name_semester.get(
                (table_subject.course_name.casefold(), table_subject.semester.casefold())
            )

        if target is None:
            subjects.append(table_subject)
            if table_subject.course_code != "N/A":
                by_code.setdefault(table_subject.course_code.casefold(), []).append(
                    table_subject
                )
            by_name_semester[
                (table_subject.course_name.casefold(), table_subject.semester.casefold())
            ] = table_subject
            continue

        target.course_name = table_subject.course_name
        if table_subject.credits is not None:
            target.credits = table_subject.credits
        if table_subject.semester != "N/A":
            target.semester = table_subject.semester
        if table_subject.course_type != "Unspecified":
            target.course_type = table_subject.course_type
        target.source_pages = sorted(set(target.source_pages + table_subject.source_pages))
        confidence, level, reasons = _calculate_confidence(
            target.course_code,
            target.course_name,
            target.credits,
            target.units,
            target.learning_outcomes,
            target.semester,
            target.course_type,
        )
        target.extraction_confidence = confidence
        target.confidence_level = level
        target.low_confidence_reasons = reasons

    unique_subjects: list[CourseSubject] = []
    seen: set[tuple[str, str, str]] = set()
    for subject in subjects:
        key = (
            subject.course_code.casefold(),
            subject.course_name.casefold(),
            subject.semester.casefold(),
        )
        if key not in seen:
            unique_subjects.append(subject)
            seen.add(key)
    return unique_subjects


def extract_subjects_from_pages(
    pages: list[tuple[int, str]],
    doc_name: str,
    table_records: list[CourseSubject] | None = None,
) -> list[CourseSubject]:
    """Segment pages into individual CourseSubject records."""
    if not pages:
        return []
        
    full_text = "\n".join(text for _, text in pages if text)
    if not full_text.strip():
        return []

    accumulated_len = 0
    page_offsets: list[tuple[int, int]] = []
    for p_num, p_text in pages:
        page_offsets.append((accumulated_len, p_num))
        accumulated_len += len(p_text) + 1

    course_boundaries: list[tuple[int, int, str]] = []
    for pat in COURSE_CODE_PATTERNS:
        for match in pat.finditer(full_text):
            idx = match.start()
            code = match.group(1).strip()
            if _is_outcome_code(code):
                continue
            page = 1
            for offset, p in page_offsets:
                if idx >= offset:
                    page = p
                else:
                    break
            course_boundaries.append((idx, page, code))

    course_boundaries.sort(key=lambda x: x[0])
    filtered_boundaries: list[tuple[int, int, str]] = []
    seen_codes: set[str] = set()
    for b in course_boundaries:
        normalized_code = b[2].casefold()
        if normalized_code not in seen_codes:
            filtered_boundaries.append(b)
            seen_codes.add(normalized_code)

    subjects: list[CourseSubject] = []
    if len(filtered_boundaries) > 1:
        for i, (start_idx, page_num, code) in enumerate(filtered_boundaries):
            end_idx = filtered_boundaries[i + 1][0] if i + 1 < len(filtered_boundaries) else len(full_text)
            chunk = full_text[start_idx:end_idx]
            covered_pages = [p for offset, p in page_offsets if start_idx <= offset < end_idx or (start_idx >= offset and offset + 500 >= start_idx)]
            if not covered_pages:
                covered_pages = [page_num]
            subject = _extract_subject_from_block(chunk, source_pages=sorted(list(set(covered_pages))))
            if subject.course_code == "N/A":
                subject.course_code = code
            subjects.append(subject)
    else:
        all_pages = [p for p, t in pages if t.strip()]
        fallback = Path(doc_name).stem.replace("_", " ").title() if doc_name else "Course Syllabus"
        subject = _extract_subject_from_block(full_text, source_pages=all_pages, fallback_title=fallback)
        subjects.append(subject)

    return _merge_table_records(subjects, table_records or [])


def parse_syllabus(source: Union[str, Path, BinaryIO]) -> Corpus:
    """Extract page text, split theory/applied, and extract structured CourseSubject objects."""
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("pdfplumber is required to parse syllabus PDFs") from exc

    pages: list[tuple[int, str]] = []
    page_tables: list[tuple[int, list[list[list[str | None]]]]] = []
    source_name = getattr(source, "name", str(source))
    doc_stem = Path(source_name).name

    try:
        with pdfplumber.open(source) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                raw = page.extract_text() or ""
                pages.append((idx, _normalize(raw)))
                page_tables.append((idx, page.extract_tables() or []))
    except Exception as exc:
        diagnostics = [f"Failed to read PDF file: {exc}. The file may be corrupt or encrypted."]
        return _corpus("", [], 0, doc_stem, diagnostics)

    full = "\n".join(p[1] for p in pages if p[1])
    table_records = _course_table_records(page_tables)
    subjects = extract_subjects_from_pages(pages, doc_stem, table_records)
    diagnostics = _diagnostics(full, len(pages), subjects)

    return _corpus(full, subjects, len(pages), doc_stem, diagnostics)


def parse_text(text: str, source_name: str = "text") -> Corpus:
    """Parse raw syllabus text for testing and text inputs."""
    normalized = _normalize(text)
    pages = [(1, normalized)] if normalized else []
    subjects = extract_subjects_from_pages(pages, source_name) if normalized else []
    diagnostics = _diagnostics(normalized, len(pages), subjects)
    return _corpus(normalized, subjects, len(pages), source_name, diagnostics)


class _CurriculumHTMLTextParser(HTMLParser):
    """Extract visible text and preserve table row/cell boundaries for the parser."""

    _SKIPPED_TAGS = frozenset({"script", "style", "noscript", "svg"})
    _BLOCK_TAGS = frozenset(
        {
            "address",
            "article",
            "br",
            "caption",
            "dd",
            "div",
            "dl",
            "dt",
            "h1",
            "h2",
            "h3",
            "h4",
            "li",
            "ol",
            "p",
            "section",
            "ul",
        }
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.tables: list[list[list[str]]] = []
        self._skip_depth = 0
        self._table_depth = 0
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None
        self._active_semester: str | None = None
        self._active_batch: str | None = None
        self._pending_semester_prefix = False
        self._pending_batch_prefix = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.casefold()
        if lowered in self._SKIPPED_TAGS:
            self._skip_depth += 1
        if self._skip_depth:
            return
        if lowered == "table":
            if self._table_depth == 0:
                self._current_table = []
                if self._active_batch:
                    self._current_table.append([f"Batch {self._active_batch}"])
                if self._active_semester:
                    self._current_table.append([self._active_semester])
            self._table_depth += 1
        elif self._table_depth:
            if self._table_depth == 1 and lowered == "tr":
                self._current_row = []
            elif self._table_depth == 1 and lowered in {"td", "th"}:
                self._current_cell = []
        elif lowered in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.casefold()
        if lowered in self._SKIPPED_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if self._table_depth:
            if self._table_depth == 1 and lowered in {"td", "th"}:
                cell = re.sub(
                    r"\s+",
                    " ",
                    " ".join(self._current_cell or []),
                ).strip()
                if self._current_row is not None:
                    self._current_row.append(cell)
                self._current_cell = None
            elif self._table_depth == 1 and lowered == "tr":
                if self._current_row and self._current_table is not None:
                    self._current_table.append(self._current_row)
                self._current_row = None
            elif lowered == "table":
                self._table_depth -= 1
                if self._table_depth == 0 and self._current_table is not None:
                    self.tables.append(self._current_table)
                    self._current_table = None
            return
        if lowered in self._BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not data.strip():
            return
        if self._table_depth:
            if self._table_depth == 1 and self._current_cell is not None:
                self._current_cell.append(data.strip())
            return
        clean = data.strip()
        semester_match = re.search(
            r"(?i)\bsemester\s*[-:–]?\s*([ivx\d]+)(?:st|nd|rd|th)?\b",
            clean,
        )
        if not semester_match and re.search(
            r"(?i)\bsemester\s*[-:–]?\s*$", clean
        ):
            self._pending_semester_prefix = True
        elif not semester_match and self._pending_semester_prefix:
            semester_match = re.fullmatch(
                r"(?i)\s*([ivx\d]+)(?:st|nd|rd|th)?\s*", clean
            )
            self._pending_semester_prefix = False
        if semester_match:
            self._active_semester = f"Semester {semester_match.group(1)}"
        batch_match = re.search(r"(?i)\bbatch\s+(20\d{2}-\d{2})\b", clean)
        if not batch_match and re.search(r"(?i)\bbatch\s*$", clean):
            self._pending_batch_prefix = True
        elif not batch_match and self._pending_batch_prefix:
            batch_match = re.fullmatch(r"\s*(20\d{2}-\d{2})\s*", clean)
            self._pending_batch_prefix = False
        if batch_match:
            self._active_batch = batch_match.group(1)
        self.parts.append(clean)


def parse_html(
    text: str,
    source_name: str = "official_curriculum.html",
    curriculum_batch: str | None = None,
) -> Corpus:
    """Parse visible official HTML through the existing deterministic text parser."""
    extractor = _CurriculumHTMLTextParser()
    extractor.feed(text)
    extractor.close()
    visible_text = _normalize("\n".join(extractor.parts))
    if curriculum_batch:
        selected_tables = [
            table
            for table in extractor.tables
            if any(
                re.fullmatch(
                    rf"(?i)batch[\s\-:]*{re.escape(curriculum_batch)}",
                    cell.strip(),
                )
                for row in table
                for cell in row
            )
        ]
        table_records = _course_table_records(
            [(1, selected_tables)],
            curriculum_batch=curriculum_batch,
        )
        selected_text = "\n".join(
            "\n".join("\t".join(row) for row in table)
            for table in selected_tables
        )
        visible_text = _normalize(selected_text)
    else:
        table_records = _course_table_records([(1, extractor.tables)])
    if curriculum_batch:
        subjects = _merge_table_records([], table_records)
    else:
        subjects = extract_subjects_from_pages(
            [(1, visible_text)] if visible_text else [],
            source_name,
            table_records,
        )
    diagnostics = _diagnostics(visible_text, 1 if visible_text else 0, subjects)
    return _corpus(visible_text, subjects, 1, source_name, diagnostics)


def _diagnostics(full: str, page_count: int, subjects: list[CourseSubject]) -> list[str]:
    diagnostics = []
    if page_count > 0 and not full:
        diagnostics.append("No extractable text was found in the PDF. Scanned or image-only PDF may require OCR.")
    if subjects and not any(subject.units for subject in subjects):
        diagnostics.append("No subject-level unit/module breakdowns were extracted.")
    if subjects and not any(subject.learning_outcomes for subject in subjects):
        diagnostics.append("No course learning outcomes were extracted.")
    if not subjects and full:
        diagnostics.append("Structured subjects could not be delineated; document is unclassified.")
    if subjects and len(subjects) < 2 and MULTI_COURSE_CATALOG_CUE.search(full):
        diagnostics.append(
            "The document appears to contain a multi-course curriculum/catalog, but fewer "
            "than two subjects were extracted. Curriculum analysis is incomplete."
        )
    for subj in subjects:
        if subj.confidence_level in ("LOW", "INSUFFICIENT EVIDENCE"):
            diagnostics.append(f"Subject '{subj.course_name}' ({subj.course_code}): {subj.confidence_level} confidence. {', '.join(subj.low_confidence_reasons)}")
    return diagnostics


def _corpus(corpus_text: str, subjects: list[CourseSubject], pages: int, source: str,
            diagnostics: list[str]) -> Corpus:
    digest = hashlib.sha256(corpus_text.encode("utf-8")).hexdigest()[:16]
    characters = len(corpus_text)
    lines = len([line for line in corpus_text.splitlines() if line.strip()])
    sections = len(re.findall(r"(?im)^\s*(?:unit|module)\s+[ivx\d]+\b", corpus_text))
    quality = "insufficient" if characters < 100 else ("usable" if subjects else "partial")
    low_confidence_count = sum(
        1 for subject in subjects
        if subject.confidence_level in ("LOW", "INSUFFICIENT EVIDENCE")
    )
    if subjects and (
        (len(subjects) <= 2 and low_confidence_count > 0)
        or (low_confidence_count / len(subjects) >= 0.5)
    ):
        quality = "partial"
    if any("multi-course curriculum/catalog" in message for message in diagnostics):
        quality = "partial"
    if characters < 500 and characters > 0:
        diagnostics.append("PDF extraction produced insufficient text (<500 characters). Check whether OCR is required.")
    return Corpus(
        corpus_text=corpus_text,
        subjects=subjects,
        page_count=pages,
        source_name=source,
        diagnostics=diagnostics,
        fingerprint=digest,
        extracted_characters=characters,
        non_empty_lines=lines,
        sections_detected=sections,
        parse_quality=quality,
    )
