"""Core data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import time


class MilestoneStatus(Enum):
    PENDING = "pending"
    FUNDED = "funded"
    APPROVED = "approved"
    RELEASED = "released"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class AgreementStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


@dataclass
class Party:
    party_id: str
    role: str  # e.g. "payer", "payee", "arbitrator"
    public_key: bytes


@dataclass
class Milestone:
    milestone_id: str
    description: str
    amount: int  # smallest unit (e.g. cents or wei)
    required_approvals: int = 1
    status: MilestoneStatus = MilestoneStatus.PENDING
    approvals: List[str] = field(default_factory=list)  # party_ids
    released_at: Optional[float] = None


@dataclass
class Event:
    timestamp: float
    event_type: str
    data: dict
    signature: Optional[bytes] = None
    signer_id: Optional[str] = None


@dataclass
class Agreement:
    agreement_id: str
    parties: List[Party]
    milestones: List[Milestone]
    status: AgreementStatus = AgreementStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    events: List[Event] = field(default_factory=list)
    merkle_root: Optional[bytes] = None

    def total_amount(self) -> int:
        return sum(m.amount for m in self.milestones)
