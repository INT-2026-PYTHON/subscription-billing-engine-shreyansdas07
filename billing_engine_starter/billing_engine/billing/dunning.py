from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

from billing_engine.db import (
    InvoiceRepository, LedgerRepository, SubscriptionRepository,
    PaymentAttemptRepository,
)
from billing_engine.models import Invoice, LedgerEntry, LedgerDirection, SubscriptionStatus
from billing_engine.payments.gateway import PaymentGateway, PaymentResult


class DunningState(str, Enum):
    PENDING = "PENDING"
    RETRYING = "RETRYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED_FINAL = "FAILED_FINAL"


@dataclass(frozen=True)
class DunningOutcome:
    state: DunningState
    attempt_no: int
    next_retry_at: Optional[datetime]


RETRY_DELAYS_DAYS = {1: 1, 2: 3}
MAX_ATTEMPTS = 3


class DunningProcess:
    def __init__(
        self,
        gateway: PaymentGateway,
        invoice_repo: InvoiceRepository,
        ledger_repo: LedgerRepository,
        subscription_repo: SubscriptionRepository,
        attempt_repo: PaymentAttemptRepository,
    ) -> None:
        self.gateway = gateway
        self.invoice_repo = invoice_repo
        self.ledger_repo = ledger_repo
        self.subscription_repo = subscription_repo
        self.attempt_repo = attempt_repo

    def attempt(self, invoice: Invoice, customer_id: int, now: datetime) -> DunningOutcome:
        previous_attempts = self.attempt_repo.find_for_invoice(invoice.id)
        attempt_no = len(previous_attempts) + 1

        if attempt_no > MAX_ATTEMPTS:
            return DunningOutcome(
                state=DunningState.FAILED_FINAL,
                attempt_no=len(previous_attempts),
                next_retry_at=None
            )

        payment_result = self.gateway.charge(customer_id, invoice.total_amount, invoice.id)
        self.attempt_repo.record_attempt(invoice.id, attempt_no, payment_result.success, now)

        if payment_result.success:
            invoice.status = "paid"
            self.invoice_repo.save(invoice)

            self.ledger_repo.post_credit(
                customer_id=customer_id,
                amount=invoice.total_amount,
                description=f"Payment success for Invoice #{invoice.id}",
                reference_id=invoice.id
            )

            subscription = self.subscription_repo.find_by_invoice(invoice.id)
            if subscription:
                subscription.status = "active"
                self.subscription_repo.save(subscription)

            return DunningOutcome(state=DunningState.SUCCEEDED, attempt_no=attempt_no, next_retry_at=None)

        else:
            if attempt_no >= MAX_ATTEMPTS:
                invoice.status = "unpaid"
                self.invoice_repo.save(invoice)

                subscription = self.subscription_repo.find_by_invoice(invoice.id)
                if subscription:
                    subscription.status = "past_due"
                    subscription.past_due_since = now.date()
                    self.subscription_repo.save(subscription)

                return DunningOutcome(state=DunningState.FAILED_FINAL, attempt_no=attempt_no, next_retry_at=None)

            else:
                delay_days = RETRY_DELAYS_DAYS.get(attempt_no, 1)
                next_retry_at = now + timedelta(days=delay_days)
                
                return DunningOutcome(state=DunningState.RETRYING, attempt_no=attempt_no, next_retry_at=next_retry_at)

    @staticmethod
    def should_cancel(past_due_since: date, today: date, grace_days: int = 7) -> bool:
        if past_due_since is None:
            return False
        return (today - past_due_since).days >= grace_days