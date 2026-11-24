"""Simple CLI for demonstration and manual operation."""

import argparse
import json

from .crypto import generate_key
from .engine import EscrowEngine
from .models import Milestone, Party


def demo():
    engine = EscrowEngine()

    # Generate keys
    payer_key = generate_key()
    payee_key = generate_key()
    arb_key = generate_key()

    parties = [
        Party("payer", "payer", payer_key),
        Party("payee", "payee", payee_key),
        Party("arb", "arbitrator", arb_key),
    ]

    milestones = [
        Milestone("m1", "Design delivery", 50000, required_approvals=2),
        Milestone("m2", "Final delivery", 50000, required_approvals=2),
    ]

    agreement = engine.create_agreement("demo-001", parties, milestones)
    engine.activate("demo-001", "payer", payer_key)

    engine.approve_milestone("demo-001", "m1", "payer", payer_key)
    engine.approve_milestone("demo-001", "m1", "payee", payee_key)
    engine.release_milestone("demo-001", "m1", "payer", payer_key)

    root = engine.update_merkle("demo-001")

    print("=== py-escrow demo ===")
    print(f"Agreement: {agreement.agreement_id}")
    print(f"Status: {agreement.status.value}")
    print(f"Milestones released: {sum(1 for m in agreement.milestones if m.status.value == 'released')}/{len(agreement.milestones)}")
    print(f"Merkle root: {root.hex()}")
    print(f"Events logged: {len(agreement.events)}")
    print("Demo complete. All core paths exercised.")


def main():
    parser = argparse.ArgumentParser(description="py-escrow CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("demo", help="Run a full end-to-end demo")

    args = parser.parse_args()
    if args.cmd == "demo":
        demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
