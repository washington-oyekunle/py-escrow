"""Core tests for the escrow engine."""

import pytest

from py_escrow.crypto import generate_key, verify
from py_escrow.engine import EscrowEngine
from py_escrow.models import Milestone, MilestoneStatus, Party


def test_full_happy_path():
    engine = EscrowEngine()
    k1, k2, k3 = generate_key(), generate_key(), generate_key()
    parties = [
        Party("a", "payer", k1),
        Party("b", "payee", k2),
        Party("c", "arb", k3),
    ]
    milestones = [
        Milestone("m1", "Phase 1", 1000, required_approvals=2),
        Milestone("m2", "Phase 2", 2000, required_approvals=1),
    ]

    agr = engine.create_agreement("test-1", parties, milestones)
    assert agr.status.value == "draft"

    engine.activate("test-1", "a", k1)
    assert agr.status.value == "active"

    engine.fund_milestone("test-1", "m1", "a", k1)
    assert agr.milestones[0].status == MilestoneStatus.FUNDED

    engine.approve_milestone("test-1", "m1", "a", k1)
    engine.approve_milestone("test-1", "m1", "b", k2)
    assert agr.milestones[0].status == MilestoneStatus.APPROVED

    engine.release_milestone("test-1", "m1", "a", k1)
    assert agr.milestones[0].status == MilestoneStatus.RELEASED

    engine.fund_milestone("test-1", "m2", "a", k1)
    engine.approve_milestone("test-1", "m2", "b", k2)
    engine.release_milestone("test-1", "m2", "a", k1)
    assert agr.status.value == "completed"

    root = engine.update_merkle("test-1")
    assert len(root) == 32
    assert len(agr.events) >= 8
    assert engine.verify_event_signatures("test-1") is True


def test_dispute_flow():
    engine = EscrowEngine()
    k1, k2 = generate_key(), generate_key()
    parties = [Party("a", "payer", k1), Party("b", "payee", k2)]
    milestones = [Milestone("m1", "Work", 500, 1)]

    engine.create_agreement("d1", parties, milestones)
    engine.activate("d1", "a", k1)
    engine.open_dispute("d1", "m1", "a", "Quality issues", k1)

    agr = engine.agreements["d1"]
    assert agr.status.value == "disputed"
    assert agr.milestones[0].status == MilestoneStatus.DISPUTED
    assert engine.verify_event_signatures("d1") is True


def test_resolve_dispute_release():
    engine = EscrowEngine()
    k1, k2, k3 = generate_key(), generate_key(), generate_key()
    parties = [
        Party("a", "payer", k1),
        Party("b", "payee", k2),
        Party("c", "arbitrator", k3),
    ]
    milestones = [Milestone("m1", "Work", 1000, 1)]

    engine.create_agreement("r1", parties, milestones)
    engine.activate("r1", "a", k1)
    engine.open_dispute("r1", "m1", "a", "Incomplete delivery", k1)

    engine.resolve_dispute("r1", "m1", "c", "release", k3)

    agr = engine.agreements["r1"]
    assert agr.milestones[0].status == MilestoneStatus.RELEASED
    assert agr.status.value == "completed"
    assert engine.verify_event_signatures("r1") is True


def test_resolve_dispute_cancel():
    engine = EscrowEngine()
    k1, k2, k3 = generate_key(), generate_key(), generate_key()
    parties = [
        Party("a", "payer", k1),
        Party("b", "payee", k2),
        Party("c", "arbitrator", k3),
    ]
    milestones = [Milestone("m1", "Work", 1000, 1)]

    engine.create_agreement("r2", parties, milestones)
    engine.activate("r2", "a", k1)
    engine.open_dispute("r2", "m1", "b", "Non-payment", k2)

    engine.resolve_dispute("r2", "m1", "c", "cancel", k3)

    agr = engine.agreements["r2"]
    assert agr.milestones[0].status == MilestoneStatus.CANCELLED
    assert agr.status.value == "completed"


def test_resolve_dispute_requires_arbitrator():
    engine = EscrowEngine()
    k1, k2 = generate_key(), generate_key()
    parties = [Party("a", "payer", k1), Party("b", "payee", k2)]
    milestones = [Milestone("m1", "Work", 500, 1)]

    engine.create_agreement("r3", parties, milestones)
    engine.activate("r3", "a", k1)
    engine.open_dispute("r3", "m1", "a", "issue", k1)

    with pytest.raises(PermissionError):
        engine.resolve_dispute("r3", "m1", "a", "release", k1)


def test_unauthorized_rejected():
    engine = EscrowEngine()
    k1 = generate_key()
    parties = [Party("a", "payer", k1)]
    milestones = [Milestone("m1", "Work", 100, 1)]
    engine.create_agreement("u1", parties, milestones)

    with pytest.raises(PermissionError):
        engine.activate("u1", "stranger", generate_key())


def test_wrong_key_rejected():
    engine = EscrowEngine()
    k1 = generate_key()
    wrong_key = generate_key()
    parties = [Party("a", "payer", k1)]
    milestones = [Milestone("m1", "Work", 100, 1)]
    engine.create_agreement("u2", parties, milestones)

    with pytest.raises(PermissionError):
        engine.activate("u2", "a", wrong_key)


def test_fund_milestone():
    engine = EscrowEngine()
    k1 = generate_key()
    parties = [Party("a", "payer", k1)]
    milestones = [Milestone("m1", "Work", 100, 1)]
    engine.create_agreement("f1", parties, milestones)
    engine.activate("f1", "a", k1)
    engine.fund_milestone("f1", "m1", "a", k1)

    agr = engine.agreements["f1"]
    assert agr.milestones[0].status == MilestoneStatus.FUNDED
    assert engine.verify_event_signatures("f1") is True
