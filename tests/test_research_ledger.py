from app.research_ledger import LocalDeliveryClaims, ResearchLedger


def test_unconfigured_ledger_is_an_explicit_no_op() -> None:
    ledger = ResearchLedger()

    assert ledger.enabled is False
    assert ledger.list_events("run") == []
    assert ledger.handoff("run") == ""


def test_local_delivery_claims_reject_a_retry() -> None:
    claims = LocalDeliveryClaims()

    assert claims.claim("delivery-1") is True
    assert claims.claim("delivery-1") is False
