# Changelog

## [0.1.5] - 2026-11-28

### Added
- JSON serialization support: `to_dict` / `from_dict` on all models and `export_agreement` / `import_agreement` on `EscrowEngine`
- Merkle inclusion proofs: `generate_merkle_proof` and `verify_merkle_proof` in `crypto.py`
- Round-trip serialization tests and Merkle proof tests

### Changed
- Version bumped to 0.1.5

## [0.1.4] - 2026-11-24

- Initial public release with core escrow state machine, funding, approvals, releases, disputes, cancellation, signatures, and Merkle roots.
