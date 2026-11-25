# py-escrow

**Pure Python multi-party escrow and milestone payment engine.**

Threshold releases, digital signatures, dispute flows, and Merkle-rooted state. Zero external dependencies for core logic. Real-world usable for freelance contracts, supply agreements, real-estate deposits, and any situation requiring conditional fund release.

## Why this exists

Most escrow systems are either centralized platforms or heavy smart-contract deployments. `py-escrow` gives you a clean, auditable, dependency-free core that can run:

- As a local simulation / teaching tool
- Embedded in a larger Python service
- As the off-chain coordinator for an on-chain settlement layer
- In air-gapped or regulated environments where external packages are restricted

## Features

- Multi-party escrow agreements with arbitrary number of parties
- Milestone-based releases with configurable thresholds
- Explicit funding step (`fund_milestone`) before approval
- Cryptographic signatures (HMAC-SHA256 by default; easy to swap for real ECDSA)
- Signer key verification against registered party keys
- Dispute and arbitration flows (including arbitrator `resolve_dispute`)
- Merkle-rooted state snapshots for efficient verification
- Deterministic event log
- Full unit-test coverage of core paths
- Clean CLI for demos and manual operation

## Quick start

```bash
git clone https://github.com/washington-oyekunle/py-escrow
cd py-escrow
python -m pytest tests/ -q
python -m py_escrow.cli demo
```

## Architecture

```
Agreement → Milestones → Funding → Signatures → State Machine → Merkle Root
                      ↘
                   Event Log
```

All state transitions are explicit, signed, and append-only.

## Real-world usage ideas

- Freelance milestone payments (designer / client / arbitrator)
- Supply-chain partial deliveries
- Real-estate earnest-money deposits
- Grant disbursement with reporting milestones
- DAO treasury conditional releases

## License

MIT
