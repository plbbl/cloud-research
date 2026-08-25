from app.job import research_job_prompt


def test_job_prompt_delegates_the_path_but_demands_a_handoff() -> None:
    prompt = research_job_prompt("Investigate small-model adaptation.")

    assert "any experts, in any order" in prompt
    assert "Explainer" in prompt
    assert "Writer" in prompt
    assert "Investigate small-model adaptation." in prompt
