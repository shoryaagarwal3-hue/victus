"""Unit tests for structured syllabus parser and diagnostics.
Tests multi-course extraction, single-course extraction, empty/malformed PDFs, and confidence scoring.
"""
import io
from backend.parser import _course_table_records, parse_text, parse_syllabus
from backend.models import CourseSubject


def test_single_subject_structured_extraction():
    sample = """
    Course Code: CS501
    Course Title: Network Security & Cryptography
    Credits: 4
    Semester: 5
    Course Type: Professional Core
    UNIT I: Cryptographic Algorithms
    Symmetric encryption, AES, DES, Block cipher modes of operation.
    
    UNIT II: Public Key Infrastructure
    RSA, Elliptic Curve Cryptography, Digital Signatures, Certificates.

    COURSE OUTCOMES:
    CO1: Understand classical and modern symmetric cryptosystems.
    CO2: Implement public-key algorithms and digital signatures.

    Additional topic: Configure a local certificate authority and generate X.509 certs.
    """
    corpus = parse_text(sample, source_name="cs501_syllabus.txt")
    assert len(corpus.subjects) == 1
    subj = corpus.subjects[0]
    assert subj.course_code == "CS501"
    assert "Network Security" in subj.course_name
    assert subj.credits == 4.0
    assert subj.semester == "Semester 5"
    assert len(subj.units) == 2
    assert len(subj.learning_outcomes) >= 2
    assert "Network Security & Cryptography" in subj.corpus_text
    assert "Implement public-key algorithms and digital signatures." in subj.corpus_text
    assert "Symmetric encryption" in subj.corpus_text
    assert corpus.corpus_text == corpus.corpus_text.strip()
    assert subj.extraction_confidence >= 0.75
    assert subj.confidence_level == "HIGH"


def test_multi_course_syllabus_segmentation():
    sample = """
    Course Code: CS401
    Course Name: Operating Systems
    Credits: 3
    UNIT 1: Process Scheduling
    Processes, threads, CPU scheduling algorithms.
    COURSE OUTCOMES:
    CO1: Analyze CPU scheduling and synchronization.

    ---
    Course Code: CS402
    Course Name: Computer Networks
    Credits: 4
    UNIT 1: OSI Architecture
    Physical and data link layer, framing, error control.
    COURSE OUTCOMES:
    CO1: Describe OSI and TCP/IP layered architecture.
    """
    corpus = parse_text(sample, source_name="curriculum_book.txt")
    assert len(corpus.subjects) >= 2
    codes = [s.course_code for s in corpus.subjects]
    assert "CS401" in codes
    assert "CS402" in codes


def test_catalog_rows_with_close_code_title_records_are_not_deduplicated():
    rows = [
        "25CSH-101 Logical Thinking and Problem Solving",
        "25CSH-102 Mathematics-I",
        "25CSH-103 Communication Skills-I",
        "25CSH-104 Digital Electronics",
        "25CSH-105 AI Applications Lab",
        "25CSH-106 Data Structures and Algorithms",
        "25CSH-107 Programming Practice",
        "25CSH-108 Computer Organization and Architecture",
        "25CSH-109 Advanced Data Structures",
        "25CSH-110 Object Oriented Programming",
        "25CSH-111 Database Management System",
        "25CSH-112 Machine Learning with Python",
        "25CSH-113 Software Engineering",
        "25CSH-114 Operating Systems",
        "25CSH-115 Design and Analysis of Algorithms",
        "25CSH-116 Computer Networks",
        "25CSH-117 Full Stack Development",
        "Professional Electives",
    ]
    corpus = parse_text("\n".join(rows), source_name="engineering_curriculum.txt")

    assert len(corpus.subjects) == 17
    assert corpus.subjects[0].course_name.startswith("Logical Thinking")
    assert corpus.subjects[-1].course_name.startswith("Full Stack Development")


def test_catalog_cue_with_single_low_confidence_subject_marks_parse_partial():
    corpus = parse_text(
        "Professional Electives\nCourse Category: Core\n",
        source_name="program_curriculum.txt",
    )

    assert corpus.parse_quality == "partial"
    assert any("fewer than two subjects" in warning for warning in corpus.diagnostics)


def test_table_rows_extract_program_and_elective_subjects():
    page_tables = [
        (
            1,
            [
                [
                    ["Course Code", "Course Name", "Semester", "Credits", "Course Type"],
                    ["26CSH-101", "Logical Thinking and Problem Solving", "1", "4", "Major Core"],
                ],
                [
                    ["Semester", "Course Name", "Category", "Credits"],
                    ["4", "Introduction to Machine Learning", "Professional Elective", "3"],
                ],
            ],
        )
    ]

    subjects = _course_table_records(page_tables)

    assert [(subject.course_code, subject.course_name) for subject in subjects] == [
        ("26CSH-101", "Logical Thinking and Problem Solving"),
        ("N/A", "Introduction to Machine Learning"),
    ]
    assert subjects[0].semester == "Semester 1"
    assert subjects[0].course_type == "Major Core"
    assert subjects[1].semester == "Semester 4"
    assert subjects[1].course_type == "Professional Elective"


def test_empty_text_returns_safe_corpus():
    corpus = parse_text("", source_name="empty.txt")
    assert len(corpus.subjects) == 0
    assert corpus.parse_quality == "insufficient"


def test_malformed_pdf_stream_handling():
    malformed_stream = io.BytesIO(b"This is not a real PDF file header.")
    setattr(malformed_stream, "name", "corrupt.pdf")
    corpus = parse_syllabus(malformed_stream)
    assert len(corpus.subjects) == 0
    assert any("Failed to read PDF file" in d for d in corpus.diagnostics)


def test_low_confidence_subject_is_flagged():
    # Only a snippet of text without course code, credits, or outcomes
    sample = "Some general text mentioning security and network concepts without formal headers."
    corpus = parse_text(sample, source_name="snippet.txt")
    assert len(corpus.subjects) == 1
    subj = corpus.subjects[0]
    assert subj.extraction_confidence < 0.60
    assert subj.confidence_level in ("LOW", "INSUFFICIENT EVIDENCE")
    assert len(subj.low_confidence_reasons) > 0
    assert corpus.parse_quality != "usable"
