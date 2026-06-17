<<<<<<< Updated upstream
"""
DunningProcess — finite state machine for failed-payment retries.

States:
    PENDING       (initial)  →  RETRYING  on first failure
    RETRYING      ──→ SUCCEEDED    when a retry succeeds
                  ──→ FAILED_FINAL after 3 total failures
    SUCCEEDED     (terminal)
    FAILED_FINAL  (terminal — also flips subscription to PAST_DUE)

Retry schedule:
    attempt 2 scheduled at  now + 1 day
    attempt 3 scheduled at  now + 3 days
    (no attempt 4 — after the 3rd failure we mark FAILED_FINAL)

After the subscription has been PAST_DUE for 7 days with no recovery,
the BillingCycle.run (Day 2 work) may flip it to CANCELLED — that
transition does NOT live in this file.
"""

=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
=======
# Inside billing_engine/billing/dunning.py
from datetime import datetime, timedelta
from typing import NamedTuple, Optional
>>>>>>> Stashed changes
from enum import Enum
from billing_engine.models import LedgerEntry, LedgerDirection, SubscriptionStatus

class DunningState(Enum):
    SUCCEEDED = "SUCCEEDED"
    RETRYING = "RETRYING"
    FAILED_FINAL = "FAILED_FINAL"

class DunningOutcome(NamedTuple):
    state: DunningState
    attempt_no: int
    next_retry_at: Optional[datetime]

<<<<<<< Updated upstream

# Retry intervals (in days) after each failure, indexed by attempt_no JUST COMPLETED.
# After failure of attempt 1, schedule attempt 2 at +1 day.
# After failure of attempt 2, schedule attempt 3 at +3 days.
# After failure of attempt 3, no more retries → FAILED_FINAL.
RETRY_DELAYS_DAYS = {1: 1, 2: 3}
=======
>>>>>>> Stashed changes
MAX_ATTEMPTS = 3
RETRY_DELAYS_DAYS = {1: 1, 2: 3, 3: 7}  # Map attempt_no to wait durations

class DunningProcess:
    def __init__(self, gateway, invoice_repo, attempt_repo, subscription_repo, ledger_repo):
        self.gateway = gateway
        self.invoice_repo = invoice_repo
        self.attempt_repo = attempt_repo
        self.subscription_repo = subscription_repo
        self.ledger_repo = ledger_repo

<<<<<<< Updated upstream
    def attempt(self, invoice: Invoice, customer_id: int, now: datetime) -> DunningOutcome:
        """Try once. Record the attempt. Return the resulting outcome."""
        # TODO Day 4
        raise NotImplementedError("Day 4: implement DunningProcess.attempt")

    # --------------------------------------------------------
    @staticmethod
    def should_cancel(past_due_since: date, today: date, grace_days: int = 7) -> bool:
<<<<<<< Updated upstream
        """Helper used by BillingCycle to decide PAST_DUE → CANCELLED."""
        # TODO Day 4
        raise NotImplementedError("Day 4: implement DunningProcess.should_cancel")
=======
        if past_due_since is None:
            return False
=======
    def attempt(self, invoice, customer_id: int, now: datetime) -> DunningOutcome:
        attempt_no = self.attempt_repo.count_for_invoice(invoice.id) + 1
        result = self.gateway.charge(invoice.total, invoice.currency)

        if result.success:
            self.invoice_repo.mark_paid(invoice.id)
            self.ledger_repo.add(LedgerEntry(
                id=None, invoice_id=invoice.id, customer_id=customer_id,
                amount=invoice.total, currency=invoice.currency,
                direction=LedgerDirection.CREDIT,
                reason=f"Payment received for invoice {invoice.id}",
            ))
            self.attempt_repo.add(invoice.id, attempt_no, "SUCCESS", None, None)
            return DunningOutcome(DunningState.SUCCEEDED, attempt_no, None)

        if attempt_no >= MAX_ATTEMPTS:
            self.invoice_repo.mark_failed(invoice.id)
            self.subscription_repo.update_status(
                invoice.subscription_id, SubscriptionStatus.PAST_DUE,
                past_due_since=now.date(),
            )
            self.attempt_repo.add(invoice.id, attempt_no, "FAILED", result.failure_reason, None)
            return DunningOutcome(DunningState.FAILED_FINAL, attempt_no, None)

        delay = RETRY_DELAYS_DAYS.get(attempt_no, 1)
        next_retry = now + timedelta(days=delay)
        self.attempt_repo.add(invoice.id, attempt_no, "FAILED", result.failure_reason, next_retry)
        return DunningOutcome(DunningState.RETRYING, attempt_no, next_retry)

    @staticmethod
    def should_cancel(past_due_since, today, grace_days: int = 7) -> bool:
>>>>>>> Stashed changes
        return (today - past_due_since).days >= grace_days
>>>>>>> Stashed changes
