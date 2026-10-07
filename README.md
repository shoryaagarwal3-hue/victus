# Curriculum Drift & Market-Alignment Engine

Streamlit audit instrument for comparing syllabus evidence with a curated market
profile. The application intentionally does not fabricate syllabus content:
upload a CU PDF (or another institution's PDF) in the sidebar and parsing runs
locally with `pdfplumber`.

## Run

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Set `GEMINI_API_KEY` (see `.env.example`) to enable the Google ADK
`curriculum_recommender` for AI-assisted subject, lab, elective, faculty, and
CO–PO recommendations. Without it, the dashboard still provides
the deterministic analysis, charts, certifications catalog and export, while
showing a visible unavailable state for AI content.
The AI model is configured centrally through `GEMINI_MODEL` (default:
`gemini-3.6-flash`); set it to a model supported by your provider/account.
OpenAI-compatible local endpoints, including gemini-web2api, can be configured
with `LOCAL_LLM_ENDPOINT` or `OPENAI_BASE_URL`; `OPENAI_MODEL` selects the
endpoint's model, defaulting to `GEMINI_MODEL`.

`data/market_skills.json` is an unverified curated MVP baseline: its values are
marked `INSUFFICIENT EVIDENCE` because auditable source records are not bundled.
The website hides demand numbers and CPS priority rankings when market
provenance is insufficient; no live scraping is claimed.

Career roles are listed in `data/role_catalog.json` and skills are classified
using `data/skill_taxonomy.json`. Role names without a configured market
profile remain selectable but do not receive fabricated market scores.

## CU source note

A local CU PDF is included in `data/sample_syllabus/` for parser and workflow
testing, but its official-source provenance has not been verified. The project
also includes a CSE-only official source catalog in
`data/cu_cse_curriculum_catalog.json`. Select an institute, department, degree,
program, specialization, entry type, and the supplied batch/year, then choose
**LOAD OFFICIAL CURRICULUM**. Supplied PDF URLs are fetched only from
`cuchd.in`/`www.cuchd.in`, validated as PDFs, hashed, and cached under
`data/curriculum_cache/`; retrieval provenance is kept in
`data/cu_cse_curriculum.sqlite3`. HTML-only entries link to their official page
and are parsed as visible page text through the existing deterministic parser.
Unknown years, batches, or degree details remain explicitly unspecified.

The local sample remains available in the upload/sample workflow for parser
testing only; it must not be treated as an authoritative CU curriculum.
