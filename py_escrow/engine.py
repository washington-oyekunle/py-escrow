"""Escrow state machine."""

from typing import Dict, List, Optional
import time

from .crypto import merkle_root, sign, verify
from .models import (
    Agreement,
    AgreementStatus,
    Event,
    Milestone,
    MilestoneStatus,
    Party,
)


class EscrowEngine:
    def __init__(self):
        self.agreements: Dict[str, Agreement] = {}

    def create_agreement(
        self,
        agreement_id: str,
        parties: List[Party],
        milestones: List[Milestone],
    ) -> Agreement:
        if agreement_id in self.agreements:
            raise ValueError("Agreement ID already exists")
        agreement = Agreement(
            agreement_id=agreement_id,
            parties=parties,
            milestones=milestones,
        )
        self.agreements[agreement_id] = agreement
        self._append_event(agreement, "agreement_created", {"id": agreement_id})
        return agreement

    def activate(self, agreement_id: str, signer_id: str, key: bytes) -> Agreement:
        agreement = self._get(agreement_id)
        if agreement.status != AgreementStatus.DRAFT:
            raise ValueError("Only draft agreements can be activated")
        self._require_party(agreement, signer_id)
        self._append_event(
            agreement,
            "activated",
            {"by": signer_id},
            signer_id=signer_id,
            key=key,
        )
        agreement.status = AgreementStatus.ACTIVE
        return agreement

    def approve_milestone(
        self,
        agreement_id: str,
        milestone_id: str,
        signer_id: str,
        key: bytes,
    ) -> Agreement:
        agreement = self._get(agreement_id)
        if agreement.status != AgreementStatus.ACTIVE:
            raise ValueError("Agreement is not active")
        milestone = self._get_milestone(agreement, milestone_id)
        if milestone.status not in (MilestoneStatus.PENDING, MilestoneStatus.FUNDED):
            raise ValueError("Milestone not in approvable state")
        if signer_id in milestone.approvals:
            raise ValueError("Already approved by this party")

        self._require_party(agreement, signer_id)
        milestone.approvals.append(signer_id)
        self._append_event(
            agreement,
            "milestone_approved",
            {"milestone": milestone_id, "by": signer_id},
            signer_id=signer_id,
            key=key,
        )

        if len(milestone.approvals) >= milestone.required_approvals:
            milestone.status = MilestoneStatus.APPROVED
            self._append_event(
                agreement,
                "milestone_ready",
                {"milestone": milestone_id},
            )
        return agreement

    def release_milestone(
        self,
        agreement_id: str,
        milestone_id: str,
        signer_id: str,
        key: bytes,
    ) -> Agreement:
        agreement = self._get(agreement_id)
        milestone = self._get_milestone(agreement, milestone_id)
        if milestone.status != MilestoneStatus.APPROVED:
            raise ValueError("Milestone must be approved before release")
        self._require_party(agreement, signer_id)

        milestone.status = MilestoneStatus.RELEASED
        milestone.released_at = time.time()
        self._append_event(
            agreement,
            "milestone_released",
            {"milestone": milestone_id, "amount": milestone.amount, "by": signer_id},
            signer_id=signer_id,
            key=key,
        )

        if all(m.status == MilestoneStatus.RELEASED for m in agreement.milestones):
            agreement.status = AgreementStatus.COMPLETED
            self._append_event(agreement, "agreement_completed", {})
        return agreement

    def open_dispute(
        self,
        agreement_id: str,
        milestone_id: str,
        signer_id: str,
        reason: str,
        key: bytes,
    ) -> Agreement:
        agreement = self._get(agreement_id)
        milestone = self._get_milestone(agreement, milestone_id)
        self._require_party(agreement, signer_id)
        milestone.status = MilestoneStatus.DISPUTED
        agreement.status = AgreementStatus.DISPUTED
        self._append_event(
            agreement,
            "dispute_opened",
            {"milestone": milestone_id, "reason": reason, "by": signer_id},
            signer_id=signer_id,
            key=key,
        )
        return agreement

    def resolve_dispute(
        self,
        agreement_id: str,
        milestone_id: str,
        arbitrator_id: str,
        outcome: str,  # "release" or "cancel"
        key: bytes,
    ) -> Agreement:
        """Arbitrator resolves a disputed milestone.

        outcome="release" marks it RELEASED and continues the agreement.
        outcome="cancel" marks it CANCELLED and may complete or keep the agreement disputed.
        """
        if outcome not in ("release", "cancel"):
            raise ValueError("outcome must be 'release' or 'cancel'")

        agreement = self._get(agreement_id)
        milestone = self._get_milestone(agreement, milestone_id)
        if milestone.status != MilestoneStatus.DISPUTED:
            raise ValueError("Milestone is not in disputed state")

        arb = self._require_party(agreement, arbitrator_id)
        if arb.role != "arbitrator":
            raise PermissionError("Only an arbitrator can resolve disputes")

        if outcome == "release":
            milestone.status = MilestoneStatus.RELEASED
            milestone.released_at = time.time()
            event_type = "dispute_resolved_release"
        else:
            milestone.status = MilestoneStatus.CANCELLED
            event_type = "dispute_resolved_cancel"

        self._append_event(
            agreement,
            event_type,
            {"milestone": milestone_id, "by": arbitrator_id, "outcome": outcome},
            signer_id=arbitrator_id,
            key=key,
        )

        # If all milestones are now terminal (RELEASED or CANCELLED), mark agreement completed
        terminal = {MilestoneStatus.RELEASED, MilestoneStatus.CANCELLED}
        if all(m.status in terminal for m in agreement.milestones):
            agreement.status = AgreementStatus.COMPLETED
            self._append_event(agreement, "agreement_completed", {})
        else:
            # Restore to ACTIVE if no other open disputes
            if not any(m.status == MilestoneStatus.DISPUTED for m in agreement.milestones):
                agreement.status = AgreementStatus.ACTIVE

        return agreement

    def update_merkle(self, agreement_id: str) -> bytes:
        agreement = self._get(agreement_id)
        leaves = [
            f"{e.timestamp}|{e.event_type}|{e.signer_id or ''}|{e.data}".encode()
            for e in agreement.events
        ]
        root = merkle_root(leaves)
        agreement.merkle_root = root
        return root

    # --- internals ---

    def _get(self, agreement_id: str) -> Agreement:
        if agreement_id not in self.agreements:
            raise KeyError("Agreement not found")
        return self.agreements[agreement_id]

    def _get_milestone(self, agreement: Agreement, milestone_id: str) -> Milestone:
        for m in agreement.milestones:
            if m.milestone_id == milestone_id:
                return m
        raise KeyError("Milestone not found")

    def _require_party(self, agreement: Agreement, party_id: str) -> Party:
        for p in agreement.parties:
            if p.party_id == party_id:
                return p
        raise PermissionError("Not a party to this agreement")

    def _append_event(
        self,
        agreement: Agreement,
        event_type: str,
        data: dict,
        signer_id: Optional[str] = None,
        key: Optional[bytes] = None,
    ) -> None:
        message = f"{event_type}|{data}|{time.time()}".encode()
        signature = None
        if key is not None and signer_id is not None:
            signature = sign(key, message)
        event = Event(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            signature=signature,
            signer_id=signer_id,
        )
        agreement.events.append(event)
