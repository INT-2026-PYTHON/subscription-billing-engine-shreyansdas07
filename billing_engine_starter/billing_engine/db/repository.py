"""
Repositories — the ONLY place SQL lives.

Each repository wraps the Database connection and exposes methods that
take/return domain dataclasses (defined in billing_engine/models/).

⚠️ YOU IMPLEMENT every method body marked TODO.
   The signatures, docstrings, and the LedgerRepository's append-only
   guarantee are already in place — do not change them.

Conventions:
  - Always use parameterized queries (`?` placeholders) — NEVER f-string SQL.
  - Money values are persisted as TEXT using `money.to_storage()`.
  - Dates are persisted as ISO strings (`date.isoformat()`).
"""

import sqlite3
from typing import List, Optional
from datetime import date
from decimal import Decimal

from billing_engine.db.database import Database
from billing_engine.money import Money
from billing_engine.models import (
    Customer,
    Plan,
    PlanTier,
    PricingType,
    BillingPeriod,
    Discount,
    DiscountType,
    Subscription,
    SubscriptionStatus,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    LedgerEntry,
    LedgerType,
    PaymentAttempt,
    PaymentStatus
)

class CustomerRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, customer: Customer) -> Customer:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO customers (name, email, country, state)
                VALUES (?, ?, ?, ?)
                """,
                (customer.name, customer.email, customer.country, customer.state)
            )
            customer.id = cursor.lastrowid
            return customer

    def get(self, customer_id: int) -> Optional[Customer]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, country, state FROM customers WHERE id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Customer(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            country=row["country"],
            state=row["state"]
        )


class PlanRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, plan: Plan) -> Plan:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO plans (name, pricing_type, billing_period, currency)
                VALUES (?, ?, ?, ?)
                """,
                (plan.name, plan.pricing_type.value, plan.billing_period.value, plan.currency)
            )
            plan.id = cursor.lastrowid
            return plan

    def get(self, plan_id: int) -> Optional[Plan]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, pricing_type, billing_period, currency FROM plans WHERE id = ?",
            (plan_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Plan(
            id=row["id"],
            name=row["name"],
            pricing_type=PricingType(row["pricing_type"]),
            billing_period=BillingPeriod(row["billing_period"]),
            currency=row["currency"]
        )


class PlanTierRepository:
    def __init__(self, db: Database):
        self.db = db

    def add_tiers(self, plan_id: int, tiers: List[PlanTier]) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            for tier in tiers:
                cursor.execute(
                    """
                    INSERT INTO plan_tiers (plan_id, from_units, to_units, unit_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (plan_id, tier.from_units, tier.to_units, tier.unit_price.to_storage())
                )

    def get_for_plan(self, plan_id: int, currency: str) -> List[PlanTier]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT from_units, to_units, unit_price FROM plan_tiers WHERE plan_id = ? ORDER BY from_units ASC",
            (plan_id,)
        )
        return [
            PlanTier(
                from_units=row["from_units"],
                to_units=row["to_units"],
                unit_price=Money(row["unit_price"], currency)
            )
            for row in cursor.fetchall()
        ]


class DiscountRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, discount: Discount) -> Discount:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO discounts (subscription_id, discount_type, amount, percentage)
                VALUES (?, ?, ?, ?)
                """,
                (
                    discount.subscription_id,
                    discount.discount_type.value,
                    discount.amount.to_storage() if discount.amount else None,
                    str(discount.percentage) if discount.percentage else None
                )
            )
            discount.id = cursor.lastrowid
            return discount

    def get_for_subscription(self, subscription_id: int, currency: str) -> Optional[Discount]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, subscription_id, discount_type, amount, percentage FROM discounts WHERE subscription_id = ?",
            (subscription_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
            
        amt_val = row["amount"]
        pct_val = row["percentage"]
        
        return Discount(
            id=row["id"],
            subscription_id=row["subscription_id"],
            discount_type=DiscountType(row["discount_type"]),
            amount=Money(amt_val, currency) if amt_val else None,
            percentage=Decimal(pct_val) if pct_val else None
        )


class SubscriptionRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, sub: Subscription) -> Subscription:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO subscriptions (customer_id, plan_id, status, current_period_start, current_period_end)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sub.customer_id, sub.plan_id, sub.status.value, sub.current_period_start.isoformat(), sub.current_period_end.isoformat())
            )
            sub.id = cursor.lastrowid
            return sub

    def update_status(self, subscription_id: int, status: SubscriptionStatus, period_start: date, period_end: date) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE subscriptions 
                SET status = ?, current_period_start = ?, current_period_end = ? 
                WHERE id = ?
                """,
                (status.value, period_start.isoformat(), period_end.isoformat(), subscription_id)
            )

    def get_active_and_due(self, target_date: date) -> List[Subscription]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, customer_id, plan_id, status, current_period_start, current_period_end 
            FROM subscriptions 
            WHERE status = 'ACTIVE' AND current_period_end <= ?
            """,
            (target_date.isoformat(),)
        )
        return [
            Subscription(
                id=row["id"],
                customer_id=row["customer_id"],
                plan_id=row["plan_id"],
                status=SubscriptionStatus(row["status"]),
                current_period_start=date.fromisoformat(row["current_period_start"]),
                current_period_end=date.fromisoformat(row["current_period_end"])
            )
            for row in cursor.fetchall()
        ]


class UsageRecordRepository:
    def __init__(self, db: Database):
        self.db = db

    def add_usage(self, subscription_id: int, quantity: int, usage_date: date) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usage_records (subscription_id, quantity, usage_date) VALUES (?, ?, ?)",
                (subscription_id, quantity, usage_date.isoformat())
            )

    def count_for_subscription(self, subscription_id: int, start_date: date, end_date: date) -> int:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT SUM(quantity) as total 
            FROM usage_records 
            WHERE subscription_id = ? AND usage_date >= ? AND usage_date < ?
            """,
            (subscription_id, start_date.isoformat(), end_date.isoformat())
        )
        row = cursor.fetchone()
        return row["total"] if row["total"] is not None else 0


class InvoiceRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, invoice: Invoice) -> Invoice:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO invoices (subscription_id, period_start, period_end, subtotal, discount_amount, tax_amount, total_amount, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice.subscription_id,
                        invoice.period_start.isoformat(),
                        invoice.period_end.isoformat(),
                        invoice.subtotal.to_storage(),
                        invoice.discount_amount.to_storage(),
                        invoice.tax_amount.to_storage(),
                        invoice.total_amount.to_storage(),
                        invoice.status.value
                    )
                )
                invoice.id = cursor.lastrowid
                return invoice
            except sqlite3.IntegrityError as e:
                raise e


class InvoiceLineItemRepository:
    def __init__(self, db: Database):
        self.db = db

    def add_items(self, invoice_id: int, items: List[InvoiceLineItem]) -> None:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            for item in items:
                cursor.execute(
                    """
                    INSERT INTO invoice_line_items (invoice_id, description, amount)
                    VALUES (?, ?, ?)
                    """,
                    (invoice_id, item.description, item.amount.to_storage())
                )


class LedgerRepository:
    def __init__(self, db: Database):
        self.db = db

    def add_entry(self, entry: LedgerEntry) -> LedgerEntry:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ledger_entries (customer_id, entry_type, amount, currency, reference_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (entry.customer_id, entry.entry_type.value, entry.amount.to_storage(), entry.currency, entry.reference_id)
            )
            entry.id = cursor.lastrowid
            return entry


class PaymentAttemptRepository:
    def __init__(self, db: Database):
        self.db = db

    def add_attempt(self, attempt: PaymentAttempt) -> PaymentAttempt:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO payment_attempts (invoice_id, amount, status, gateway_reference)
                VALUES (?, ?, ?, ?)
                """,
                (attempt.invoice_id, attempt.amount.to_storage(), attempt.status.value, attempt.gateway_reference)
            )
            attempt.id = cursor.lastrowid
            return attempt