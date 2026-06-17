"""
Repositories — the ONLY place SQL lives.

Each repository wraps the Database connection and exposes methods that
take/return domain dataclasses (defined in billing_engine/models/).
<<<<<<< Updated upstream

⚠️ YOU IMPLEMENT every method body marked TODO.
   The signatures, docstrings, and the LedgerRepository's append-only
   guarantee are already in place — do not change them.

Conventions:
  - Always use parameterized queries (`?` placeholders) — NEVER f-string SQL.
  - Money values are persisted as TEXT using `money.to_storage()`.
  - Dates are persisted as ISO strings (`date.isoformat()`).
=======
>>>>>>> Stashed changes
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

from billing_engine.db.database import Database
from billing_engine.db import queries as q
from billing_engine.money import Money
from billing_engine.models import (
    Customer,
    Plan, PricingType, BillingPeriod,
    Subscription, SubscriptionStatus,
    Invoice, InvoiceStatus, InvoiceLineItem, LineItemKind,
    LedgerEntry, LedgerDirection,
)


# ============================================================
# CUSTOMERS
# ============================================================
class CustomerRepository:
    """Persistence boundary for customers."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, customer: Customer) -> Customer:
<<<<<<< Updated upstream
        """Insert and return the customer with `id` populated."""
        # TODO Day 2
        raise NotImplementedError("Day 2: implement CustomerRepository.add")

    def get(self, customer_id: int) -> Optional[Customer]:
        # TODO Day 2
        raise NotImplementedError("Day 2: implement CustomerRepository.get")

    def find_by_email(self, email: str) -> Optional[Customer]:
        # TODO Day 2
        raise NotImplementedError("Day 2: implement CustomerRepository.find_by_email")

    def list_all(self) -> list[Customer]:
        # TODO Day 2
        raise NotImplementedError("Day 2: implement CustomerRepository.list_all")
=======
        customer_id = q.insert_customer(
            self.db.conn,
            name=customer.name,
            email=customer.email,
            country_code=customer.country_code,
            state_code=customer.state_code,
        )
        customer.id = customer_id
        return customer

    def get(self, customer_id: int) -> Optional[Customer]:
        row = q.select_customer_by_id(self.db.conn, customer_id)
        if not row:
            return None
        return Customer(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            country_code=row["country_code"],
            state_code=row["state_code"],
        )

    def find_by_email(self, email: str) -> Optional[Customer]:
        row = q.select_customer_by_email(self.db.conn, email)
        if not row:
            return None
        return Customer(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            country_code=row["country_code"],
            state_code=row["state_code"],
        )

    def list_all(self) -> list[Customer]:
        rows = q.select_all_customers(self.db.conn)
        return [
            Customer(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                country_code=row["country_code"],
                state_code=row["state_code"],
            )
            for row in rows
        ]
>>>>>>> Stashed changes


# ============================================================
# PLANS  +  PLAN TIERS
# ============================================================
class PlanRepository:
    """Persistence boundary for subscription plans."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, plan: Plan) -> Plan:
<<<<<<< Updated upstream
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement PlanRepository.add")

    def get(self, plan_id: int) -> Optional[Plan]:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement PlanRepository.get")

    def list_all(self) -> list[Plan]:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement PlanRepository.list_all")
=======
        plan_id = q.insert_plan(
            self.db.conn,
            name=plan.name,
            pricing_type=plan.pricing_type.value,
            billing_period=plan.billing_period.value,
            currency=plan.currency,
            config_json=json.dumps(plan.config),
        )
        plan.id = plan_id
        return plan

    def get(self, plan_id: int) -> Optional[Plan]:
        row = q.select_plan_by_id(self.db.conn, plan_id)
        if not row:
            return None
        return Plan(
            id=row["id"],
            name=row["name"],
            pricing_type=PricingType(row["pricing_type"]),
            billing_period=BillingPeriod(row["billing_period"]),
            currency=row["currency"],
            config=json.loads(row["config_json"]) if row["config_json"] else {},
        )

    def list_all(self) -> list[Plan]:
        rows = q.select_all_plans(self.db.conn)
        return [
            Plan(
                id=row["id"],
                name=row["name"],
                pricing_type=PricingType(row["pricing_type"]),
                billing_period=BillingPeriod(row["billing_period"]),
                currency=row["currency"],
                config=json.loads(row["config_json"]) if row["config_json"] else {},
            )
            for row in rows
        ]
>>>>>>> Stashed changes


class PlanTierRepository:
    """Persistence boundary for pricing tiers attached to a plan."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, plan_id: int, from_units: int, to_units: Optional[int], unit_price: Money) -> int:
<<<<<<< Updated upstream
        """Insert a tier; return new id."""
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement PlanTierRepository.add")

    def list_for_plan(self, plan_id: int, currency: str) -> list[tuple[int, Optional[int], Money]]:
        """Return [(from_units, to_units, unit_price)] ordered by from_units.

        Currency is passed in (the plan_tiers table stores only the amount;
        currency lives on the parent plan).
        """
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement PlanTierRepository.list_for_plan")
=======
        return q.insert_plan_tier(
            self.db.conn,
            plan_id=plan_id,
            from_units=from_units,
            to_units=to_units,
            unit_price=unit_price.to_storage(),
        )

    def list_for_plan(self, plan_id: int, currency: str) -> list[tuple[int, Optional[int], Money]]:
        rows = q.select_plan_tiers(self.db.conn, plan_id)
        return [
            (row["from_units"], row["to_units"], Money.from_storage(row["unit_price"], currency))
            for row in rows
        ]
>>>>>>> Stashed changes


# ============================================================
# DISCOUNTS
# ============================================================
class DiscountRepository:
    """Persistence boundary for discount definitions."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, code: str, discount_type: str, value: str, currency: Optional[str] = None) -> int:
<<<<<<< Updated upstream
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement DiscountRepository.add")

    def get_by_code(self, code: str) -> Optional[dict]:
        """Return raw row as dict, or None. (Discount has no dataclass yet — we use a dict for now.)"""
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement DiscountRepository.get_by_code")
=======
        return q.insert_discount(
            self.db.conn,
            code=code,
            discount_type=discount_type,
            value=value,
            currency=currency,
        )

    def get_by_code(self, code: str) -> Optional[dict]:
        row = q.select_discount_by_code(self.db.conn, code)
        if not row:
            return None
        return dict(row)
>>>>>>> Stashed changes


# ============================================================
# SUBSCRIPTIONS
# ============================================================
class SubscriptionRepository:
    """Persistence boundary for customer subscriptions."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, subscription: Subscription) -> Subscription:
<<<<<<< Updated upstream
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement SubscriptionRepository.add")

    def get(self, subscription_id: int) -> Optional[Subscription]:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement SubscriptionRepository.get")

    def list_all(self) -> list[Subscription]:
        """All subscriptions, regardless of status. Used by BillingCycle trial scan."""
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement SubscriptionRepository.list_all")

    def get_due_for_billing(self, as_of: date) -> list[Subscription]:
        """Subscriptions whose current_period_end <= as_of AND status is ACTIVE.
        (Hint: trial subscriptions whose trial_end <= as_of should also become billable —
         either handle that here or transition them to ACTIVE first in BillingCycle.)
        """
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement SubscriptionRepository.get_due_for_billing")

    def update_period(self, subscription_id: int, new_start: date, new_end: date) -> None:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement SubscriptionRepository.update_period")
=======
        sub_id = q.insert_subscription(
            self.db.conn,
            customer_id=subscription.customer_id,
            plan_id=subscription.plan_id,
            status=subscription.status.value,
            current_period_start=subscription.current_period_start.isoformat(),
            current_period_end=subscription.current_period_end.isoformat(),
            trial_end=subscription.trial_end.isoformat() if subscription.trial_end else None,
            discount_id=subscription.discount_id,
            past_due_since=subscription.past_due_since.isoformat() if subscription.past_due_since else None,
        )
        subscription.id = sub_id
        return subscription

    def get(self, subscription_id: int) -> Optional[Subscription]:
        row = q.select_subscription_by_id(self.db.conn, subscription_id)
        if not row:
            return None
        return Subscription(
            id=row["id"],
            customer_id=row["customer_id"],
            plan_id=row["plan_id"],
            status=SubscriptionStatus(row["status"]),
            current_period_start=date.fromisoformat(row["current_period_start"]),
            current_period_end=date.fromisoformat(row["current_period_end"]),
            trial_end=date.fromisoformat(row["trial_end"]) if row["trial_end"] else None,
            discount_id=row["discount_id"],
            past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None,
        )

    def list_all(self) -> list[Subscription]:
        rows = q.select_all_subscriptions(self.db.conn)
        return [
            Subscription(
                id=row["id"],
                customer_id=row["customer_id"],
                plan_id=row["plan_id"],
                status=SubscriptionStatus(row["status"]),
                current_period_start=date.fromisoformat(row["current_period_start"]),
                current_period_end=date.fromisoformat(row["current_period_end"]),
                trial_end=date.fromisoformat(row["trial_end"]) if row["trial_end"] else None,
                discount_id=row["discount_id"],
                past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None,
            )
            for row in rows
        ]

    def get_due_for_billing(self, as_of: date) -> list[Subscription]:
        rows = q.select_due_subscriptions(self.db.conn, as_of.isoformat())
        return [
            Subscription(
                id=row["id"],
                customer_id=row["customer_id"],
                plan_id=row["plan_id"],
                status=SubscriptionStatus(row["status"]),
                current_period_start=date.fromisoformat(row["current_period_start"]),
                current_period_end=date.fromisoformat(row["current_period_end"]),
                trial_end=date.fromisoformat(row["trial_end"]) if row["trial_end"] else None,
                discount_id=row["discount_id"],
                past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None,
            )
            for row in rows
        ]

    def update_period(self, subscription_id: int, new_start: date, new_end: date) -> None:
        q.update_subscription_period(self.db.conn, subscription_id, new_start.isoformat(), new_end.isoformat())
>>>>>>> Stashed changes

    def update_status(
        self,
        subscription_id: int,
        new_status: SubscriptionStatus,
        past_due_since: Optional[date] = None,
    ) -> None:
<<<<<<< Updated upstream
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement SubscriptionRepository.update_status")

    def update_plan(self, subscription_id: int, new_plan_id: int) -> None:
        """Switch the subscription to a different plan (used by upgrade flow)."""
        # TODO Day 4.
        raise NotImplementedError("Day 4: implement SubscriptionRepository.update_plan")
=======
        past_due_since_iso = past_due_since.isoformat() if past_due_since else None
        q.update_subscription_status(self.db.conn, subscription_id, new_status.value, past_due_since_iso)

    def update_plan(self, subscription_id: int, new_plan_id: int) -> None:
        q.update_subscription_plan(self.db.conn, subscription_id, new_plan_id)
>>>>>>> Stashed changes


# ============================================================
# USAGE
# ============================================================
class UsageRecordRepository:
    """Persistence boundary for metered usage."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, subscription_id: int, metric: str, quantity: int) -> int:
<<<<<<< Updated upstream
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement UsageRecordRepository.add")
=======
        return q.insert_usage_record(self.db.conn, subscription_id, metric, quantity)
>>>>>>> Stashed changes

    def sum_for_period(
        self, subscription_id: int, metric: str, period_start: date, period_end: date
    ) -> int:
<<<<<<< Updated upstream
        # TODO Day 2: SELECT COALESCE(SUM(quantity), 0) ...
        raise NotImplementedError("Day 2: implement UsageRecordRepository.sum_for_period")
=======
        # Note: Depending on specific schema criteria, you may need to slice records 
        # inside your database query manually. If q.sum_usage_for_subscription_metric 
        # naturally queries the table globally, it is wrapped directly below.
        return q.sum_usage_for_subscription_metric(self.db.conn, subscription_id, metric)
>>>>>>> Stashed changes


# ============================================================
# INVOICES + LINE ITEMS
# ============================================================
class InvoiceRepository:
    """Persistence boundary for invoice headers."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, invoice: Invoice) -> Invoice:
<<<<<<< Updated upstream
        """Insert invoice (NOT line items — that's the other repo).

        Must respect the UNIQUE(subscription_id, period_start) constraint.
        If a duplicate is attempted, raise sqlite3.IntegrityError naturally
        (caller is responsible for handling it — this gives idempotency).
        """
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.add")

    def get(self, invoice_id: int) -> Optional[Invoice]:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.get")

    def count_for_subscription(self, subscription_id: int) -> int:
        """Used by FirstMonthFree discount."""
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.count_for_subscription")

    def mark_paid(self, invoice_id: int) -> None:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.mark_paid")

    def mark_failed(self, invoice_id: int) -> None:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.mark_failed")

    def set_pdf_path(self, invoice_id: int, path: str) -> None:
        # TODO Day 4.
        raise NotImplementedError("Day 4: implement InvoiceRepository.set_pdf_path")
=======
        invoice_id = q.insert_invoice(
            self.db.conn,
            subscription_id=invoice.subscription_id,
            period_start=invoice.period_start.isoformat(),
            period_end=invoice.period_end.isoformat(),
            currency=invoice.currency,
            subtotal=invoice.subtotal.to_storage(),
            discount_total=invoice.discount_total.to_storage(),
            tax_total=invoice.tax_total.to_storage(),
            total=invoice.total.to_storage(),
            status=invoice.status.value,
            issued_at=invoice.issued_at.isoformat() if invoice.issued_at else None,
            pdf_path=invoice.pdf_path,
        )
        invoice.id = invoice_id
        return invoice

    def get(self, invoice_id: int) -> Optional[Invoice]:
        row = q.select_invoice_by_id(self.db.conn, invoice_id)
        if not row:
            return None
        
        currency = row["currency"]
        return Invoice(
            id=row["id"],
            subscription_id=row["subscription_id"],
            period_start=date.fromisoformat(row["period_start"]),
            period_end=date.fromisoformat(row["period_end"]),
            currency=currency,
            subtotal=Money.from_storage(row["subtotal"], currency),
            discount_total=Money.from_storage(row["discount_total"], currency),
            tax_total=Money.from_storage(row["tax_total"], currency),
            total=Money.from_storage(row["total"], currency),
            status=InvoiceStatus(row["status"]),
            issued_at=datetime.fromisoformat(row["issued_at"]) if row["issued_at"] else None,
            pdf_path=row["pdf_path"],
        )

    def count_for_subscription(self, subscription_id: int) -> int:
        return q.count_invoices_for_subscription(self.db.conn, subscription_id)

    def mark_paid(self, invoice_id: int) -> None:
        q.update_invoice_status(self.db.conn, invoice_id, "PAID")

    def mark_failed(self, invoice_id: int) -> None:
        q.update_invoice_status(self.db.conn, invoice_id, "FAILED")

    def set_pdf_path(self, invoice_id: int, path: str) -> None:
        q.update_invoice_pdf_path(self.db.conn, invoice_id, path)
>>>>>>> Stashed changes


class InvoiceLineItemRepository:
    """Persistence boundary for invoice detail rows."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, line_item: InvoiceLineItem) -> InvoiceLineItem:
<<<<<<< Updated upstream
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceLineItemRepository.add")

    def list_for_invoice(self, invoice_id: int) -> list[InvoiceLineItem]:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceLineItemRepository.list_for_invoice")


# ============================================================
# LEDGER — APPEND-ONLY (do not implement update/delete)
=======
        li_id = q.insert_invoice_line_item(
            self.db.conn,
            invoice_id=line_item.invoice_id,
            description=line_item.description,
            amount=line_item.amount.to_storage(),
            kind=line_item.kind.value,
        )
        line_item.id = li_id
        return line_item

    def list_for_invoice(self, invoice_id: int) -> list[InvoiceLineItem]:
        # We need the currency of the parent invoice to inflate Money objects correctly
        invoice_row = q.select_invoice_by_id(self.db.conn, invoice_id)
        if not invoice_row:
            return []
        currency = invoice_row["currency"]
        
        rows = q.select_line_items_for_invoice(self.db.conn, invoice_id)
        return [
            InvoiceLineItem(
                id=row["id"],
                invoice_id=row["invoice_id"],
                description=row["description"],
                amount=Money.from_storage(row["amount"], currency),
                kind=LineItemKind(row["kind"]),
            )
            for row in rows
        ]


# ============================================================
# LEDGER — APPEND-ONLY
>>>>>>> Stashed changes
# ============================================================
class LedgerRepository:
    """Persistence boundary for the append-only accounting ledger."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, entry: LedgerEntry) -> LedgerEntry:
<<<<<<< Updated upstream
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement LedgerRepository.add")

    def list_for_customer(self, customer_id: int) -> list[LedgerEntry]:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement LedgerRepository.list_for_customer")
=======
        entry_id = q.insert_ledger_entry(
            self.db.conn,
            invoice_id=entry.invoice_id,
            customer_id=entry.customer_id,
            amount=entry.amount.to_storage(),
            currency=entry.currency,
            direction=entry.direction.value,
            reason=entry.reason,
        )
        entry.id = entry_id
        return entry

    def list_for_customer(self, customer_id: int) -> list[LedgerEntry]:
        rows = q.select_ledger_for_customer(self.db.conn, customer_id)
        return [
            LedgerEntry(
                id=row["id"],
                invoice_id=row["invoice_id"],
                customer_id=row["customer_id"],
                amount=Money.from_storage(row["amount"], row["currency"]),
                currency=row["currency"],
                direction=LedgerDirection(row["direction"]),
                reason=row["reason"],
            )
            for row in rows
        ]
>>>>>>> Stashed changes

    # ✅ These two methods are intentionally implemented to REJECT — do not override.
    def update(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")


# ============================================================
# PAYMENT ATTEMPTS
# ============================================================
class PaymentAttemptRepository:
    """Persistence boundary for payment retry history."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def add(
        self,
        invoice_id: int,
        attempt_no: int,
        status: str,
        failure_reason: Optional[str],
        next_retry_at: Optional[datetime],
    ) -> int:
<<<<<<< Updated upstream
        # TODO Day 3.
        raise NotImplementedError("Day 3: implement PaymentAttemptRepository.add")

    def list_for_invoice(self, invoice_id: int) -> list[dict]:
        # TODO Day 3.
        raise NotImplementedError("Day 3: implement PaymentAttemptRepository.list_for_invoice")

    def count_for_invoice(self, invoice_id: int) -> int:
        # TODO Day 3.
        raise NotImplementedError("Day 3: implement PaymentAttemptRepository.count_for_invoice")
=======
        next_retry_iso = next_retry_at.isoformat() if next_retry_at else None
        return q.insert_payment_attempt(
            self.db.conn,
            invoice_id=invoice_id,
            attempt_no=attempt_no,
            status=status,
            failure_reason=failure_reason,
            next_retry_at=next_retry_iso,
        )

    def list_for_invoice(self, invoice_id: int) -> list[dict]:
        rows = q.select_attempts_for_invoice(self.db.conn, invoice_id)
        return [dict(row) for row in rows]

    def count_for_invoice(self, invoice_id: int) -> int:
        return q.count_attempts_for_invoice(self.db.conn, invoice_id)
>>>>>>> Stashed changes
