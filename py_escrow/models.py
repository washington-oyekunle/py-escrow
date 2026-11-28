"""Core data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import time
import base64


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "party_id": self.party_id,
            "role": self.role,
            "public_key": base64.b64encode(self.public_key).decode("ascii"),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Party":
        return cls(
            party_id=data["party_id"],
            role=data["role"],
            public_key=base64.b64decode(data["public_key"]),
        )


@dataclass
class Milestone:
    milestone_id: str
    description: str
    amount: int  # smallest unit (e.g. cents or wei)
    required_approvals: int = 1
    status: MilestoneStatus = MilestoneStatus.PENDING
    approvals: List[str] = field(default_factory=list)  # party_ids
    released_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "milestone_id": self.milestone_id,
            "description": self.description,
            "amount": self.amount,
            "required_approvals": self.required_approvals,
            "status": self.status.value,
            "approvals": self.approvals[:],
            "released_at": self.released_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Milestone":
        return cls(
            milestone_id=data["milestone_id"],
            description=data["description"],
            amount=data["amount"],
            required_approvals=data.get("required_approvals", 1),
            status=MilestoneStatus(data["status"]),
            approvals=data.get("approvals", []),
            released_at=data.get("released_at"),
        )


@dataclass
class Event:
    timestamp: float
    event_type: str
    data: dict
    signature: Optional[bytes] = None
    signer_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "data": self.data,
            "signature": base64.b64encode(self.signature).decode("ascii") if self.signature else None,
            "signer_id": self.signer_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        sig = data.get("signature")
        return cls(
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            data=data["data"],
            signature=base64.b64decode(sig) if sig else None,
            signer_id=data.get("signer_id"),
        )


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agreement_id": self.agreement_id,
            "parties": [p.to_dict() for p in self.parties],
            "milestones": [m.to_dict() for m in self.milestones],
            "status": self.status.value,
            "created_at": self.created_at,
            "events": [e.to_dict() for e in self.events],
            "merkle_root": base64.b64encode(self.merkle_root).decode("ascii") if self.merkle_root else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agreement":
        root = data.get("merkle_root")
        return cls(
            agreement_id=data["agreement_id"],
            parties=[Party.from_dict(p) for p in data["parties"]],
            milestones=[Milestone.from_dict(m) for m in data["milestones"]],
            status=AgreementStatus(data["status"]),
            created_at=data["created_at"],
            events=[Event.from_dict(e) for e in data.get("events", [])],
            merkle_root=base64.b64decode(root) if root else None,
        )
