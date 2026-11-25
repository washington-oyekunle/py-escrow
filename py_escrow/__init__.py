"""py-escrow: pure-Python multi-party escrow engine."""

__version__ = "0.1.2"

from .models import Agreement, Milestone, Party
from .engine import EscrowEngine
from .crypto import sign, verify, generate_key

__all__ = [
    "Agreement",
    "Milestone",
    "Party",
    "EscrowEngine",
    "sign",
    "verify",
    "generate_key",
]
