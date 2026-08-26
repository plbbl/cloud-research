from app.prompts import DIRECTOR, PROMPTS


def test_prompts_are_deliberately_short() -> None:
    assert len(DIRECTOR.split()) < 90
    assert all(len(prompt.split()) < 75 for name, prompt in PROMPTS.items() if name != "director")


def test_prompt_philosophy_is_present_without_a_rulebook() -> None:
    complete_prompt = " ".join(PROMPTS.values()).lower()
    assert "valuable research fruit exists" in complete_prompt
    assert "interesting" in complete_prompt
    assert "believe" in complete_prompt


def test_prompts_preserve_the_evidence_boundary() -> None:
    complete_prompt = " ".join(PROMPTS.values()).lower()
    assert "[observed here]" in complete_prompt
    assert "[sourced]" in complete_prompt
    assert "[proposed]" in complete_prompt
    assert "toy probe never validates a real benchmark" in complete_prompt
