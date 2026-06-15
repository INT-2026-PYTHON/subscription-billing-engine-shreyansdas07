from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
from typing import Optional

from billing_engine.models import Invoice


@dataclass(frozen=True)
class PaymentResult:
    success: bool
    failure_reason: Optional[str] = None


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, invoice: Invoice) -> PaymentResult:
        raise NotImplementedError


class ScriptedGateway(PaymentGateway):

    def __init__(self, results: list[PaymentResult]) -> None:
        self.results = list(results)

    def charge(self, invoice: Invoice) -> PaymentResult:
        if not self.results:
            return PaymentResult(False, "NO_MORE_SCRIPTED_RESULTS")
        return self.results.pop(0)


class FakeRandomGateway(PaymentGateway):

    def __init__(self, success_rate: float = 0.7, seed: Optional[int] = None) -> None:
        self.success_rate = success_rate
        self.random_instance = random.Random(seed)

    def charge(self, invoice: Invoice) -> PaymentResult:
        if self.random_instance.random() < self.success_rate:
            return PaymentResult(True)
        return PaymentResult(False, "CARD_DECLINED")