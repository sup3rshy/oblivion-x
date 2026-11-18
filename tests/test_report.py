from oblivionx.eval.report import metrics_table, write_markdown_report


def test_markdown_report_renders_all_experiments(tiny_eval, tmp_path):
    out = tmp_path / "report.md"
    figures = tmp_path / "figures"
    write_markdown_report(tiny_eval, out, figures)
    text = out.read_text(encoding="utf-8")
    assert "16-sample" in text
    for section in ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8",
                    "Figures"):
        assert f"## {section}" in text or f"# {section}" in text
    assert (figures / "E2_recall.png").exists()
    assert "Analysis time/sample (ms)" in text


def test_metrics_table_formats_missing_values():
    table = metrics_table({"behavior_recall": 0.5,
                           "deobfuscation_success": None})
    assert "| Behavior recall | 0.500 |" in table
    assert "| Deobfuscation success | - |" in table
