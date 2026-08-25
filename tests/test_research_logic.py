from app.research_logic import compare_claim_text, research_terms, safe_artifact_name


def test_claim_comparison_is_a_hint_not_a_verdict() -> None:
    result = compare_claim_text(
        "Test-time adaptation fails when entropy hides class collapse",
        "Class collapse is hidden by entropy during test time adaptation",
    )

    assert result["overlap"] > 0.5
    assert "mechanism" in result["interpretation"]


def test_research_terms_drop_empty_scaffolding() -> None:
    assert research_terms("This is a mechanism for the model") == {"mechanism", "model"}


def test_artifact_name_is_portable() -> None:
    assert safe_artifact_name("A Surprising Result: Why?") == "a-surprising-result-why.md"
