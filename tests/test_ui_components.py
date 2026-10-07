import streamlit as st

from frontend.ui_components import kpi


def test_kpi_escapes_label_and_renders_configured_unit(monkeypatch):
    output = []
    monkeypatch.setattr(st, "markdown", lambda markup, **_: output.append(markup))

    kpi("<script>alert(1)</script>", 82.5, "#3DDC97", " / 100")

    assert "&lt;script&gt;" in output[0]
    assert "<script>" not in output[0]
    assert "82.5 / 100" in output[0]
