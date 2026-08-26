import hashlib
import hmac

from app.github_events import research_brief, valid_signature


def test_signature_uses_the_raw_github_payload() -> None:
    body = b'{"action":"cloud-research"}'
    secret = "test-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert valid_signature(body, f"sha256={digest}", secret)
    assert not valid_signature(body + b" ", f"sha256={digest}", secret)


def test_issue_label_becomes_a_research_brief() -> None:
    trigger = research_brief(
        "issues",
        {
            "action": "labeled",
            "label": {"name": "cloud-research"},
            "issue": {
                "number": 11,
                "title": "A narrow task",
                "body": "Find the cheapest kill test.",
                "html_url": "https://github.com/example/repo/issues/11",
                "labels": [{"name": "lab:mechanistic_vision"}],
            },
        },
    )

    assert trigger is not None
    assert trigger.lab_id == "mechanistic_vision"
    assert trigger.source == "github:issue:11"
    assert "cheapest kill test" in trigger.brief


def test_unrelated_issue_is_ignored() -> None:
    assert (
        research_brief(
            "issues",
            {
                "action": "labeled",
                "label": {"name": "documentation"},
                "issue": {"labels": []},
            },
        )
        is None
    )
