from pathlib import Path

from app.tools import publish_research_packet, write_research_artifact


def test_write_research_artifact(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_RESEARCH_LAB_DIR", str(tmp_path))
    result = write_research_artifact("Interesting failure", "# Evidence\n\nIt broke.")

    assert Path(result["path"]).read_text(encoding="utf-8").endswith("It broke.\n")


def test_publish_without_github_keeps_the_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_RESEARCH_LAB_DIR", str(tmp_path))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    result = publish_research_packet("Handoff", "# Handoff")

    assert Path(result["path"]).exists()
    assert "not configured" in result["message"]
