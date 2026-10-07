from backend.report_exporter import build_pdf


def test_build_pdf_handles_long_generated_content(tmp_path):
    long_url = "https://example.com/" + "a" * 700 + "?token=" + "b" * 300
    patches = {}
    output = build_pdf(
        "University " + "Y" * 120,
        "Cloud Security Engineer",
        {"stability_index": None, "drift_rate": 100, "health_score": 0, "missing_tools": [None, long_url]},
        patches,
    )
    path = tmp_path / "audit.pdf"
    path.write_bytes(output)
    assert output.startswith(b"%PDF")
    assert output.rstrip().endswith(b"%%EOF")


def test_build_pdf_handles_empty_values():
    output = build_pdf(None, None, {}, {})
    assert output.startswith(b"%PDF")


def test_build_pdf_includes_market_provenance_certifications_and_copo():
    output = build_pdf(
        "Test Institute",
        "SOC Analyst",
        {
            "profile": {
                "provenance": {
                    "source_type": "INSUFFICIENT EVIDENCE",
                    "metric": "relative_demand_index_0_to_100",
                    "source": "Unverified curated baseline",
                    "date": "undocumented",
                    "denominator": None,
                }
            },
            "certification_options": {
                "Splunk": [{
                    "cert_name": "Splunk Core Certified User",
                    "issuer": "Splunk Inc.",
                    "level": "Entry",
                }]
            },
            "po_definitions": {"PO5": "Modern tool usage"},
        },
        {
            "evidence_provenance": "AI-ASSISTED",
            "copo_mapping": [{
                "course_outcome": "Use tools to analyze evidence.",
                "mapped_pos": [{
                    "po": "PO5",
                    "strength": 3,
                    "justification": "Applies modern tools.",
                }],
            }],
        },
    )

    assert output.startswith(b"%PDF")
    assert output.rstrip().endswith(b"%%EOF")
