<<<<<<< Updated upstream
"""
PaymentGateway — abstract + two mock implementations.

In real life this would talk to Stripe / Razorpay / Adyen. For the project
we use mocks so tests are deterministic and the demo never hits the network.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
=======
# Inside billing_engine/payments/gateway.py
import random
from typing import NamedTuple, Optional
>>>>>>> Stashed changes

class PaymentResult(NamedTuple):
    success: bool
    failure_reason: Optional[str] = None

class ScriptedGateway:
    """Returns exact responses explicitly pre-stacked to verify workflow mechanics."""
    def __init__(self, sequence: list[PaymentResult]) -> None:
        self.sequence = sequence
        self.pointer = 0

    def charge(self, amount, currency) -> PaymentResult:
        if self.pointer >= len(self.sequence):
            return PaymentResult(success=False, failure_reason="Gateway Sequence Exhausted")
        res = self.sequence[self.pointer]
        self.pointer += 1
        return res

<<<<<<< Updated upstream

# ----------------------------------------------------------------
# Scripted — for deterministic tests
# ----------------------------------------------------------------
class ScriptedGateway(PaymentGateway):
    """Returns pre-set results from a queue. Used in tests.

    Example:
        gateway = ScriptedGateway([
            PaymentResult(False, "INSUFFICIENT_FUNDS"),
            PaymentResult(False, "INSUFFICIENT_FUNDS"),
            PaymentResult(True),
        ])
    """

    def __init__(self, results: list[PaymentResult]) -> None:
        # TODO Day 3
        raise NotImplementedError("Day 3: implement ScriptedGateway.__init__")

    def charge(self, invoice: Invoice) -> PaymentResult:
        # TODO Day 3
        raise NotImplementedError("Day 3: implement ScriptedGateway.charge")


# ----------------------------------------------------------------
# Fake-random — for the CLI demo
# ----------------------------------------------------------------
class FakeRandomGateway(PaymentGateway):
    """Succeeds at a configurable rate; seeded for reproducibility."""

    def __init__(self, success_rate: float = 0.7, seed: Optional[int] = None) -> None:
        # TODO Day 3
        raise NotImplementedError("Day 3: implement FakeRandomGateway.__init__")

    def charge(self, invoice: Invoice) -> PaymentResult:
        # TODO Day 3
        raise NotImplementedError("Day 3: implement FakeRandomGateway.charge")
=======
class FakeRandomGateway:
    """Provides a deterministic layout using an arbitrary execution sequence seed."""
    def __init__(self, success_rate: float = 0.8, seed: int = 42) -> None:
        self.rand = random.Random(seed)
        self.success_rate = success_rate

    def charge(self, amount, currency) -> PaymentResult:
        if self.rand.random() <= self.success_rate:
            return PaymentResult(success=True)
        return PaymentResult(success=False, failure_reason="Insufficient Funds (Mock)")
>>>>>>> Stashed changes
