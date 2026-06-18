from __future__ import annotations

import sqlite3
from typing import List, Optional
from datetime import date, datetime
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
    LineItemKind,
    LedgerEntry,
    LedgerDirection,
    PaymentAttempt,
    PaymentStatus
)

class CustomerRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, customer: Customer) -> Customer:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO customers (name, email, currency, tax_country, tax_state)
                VALUES (?, ?, ?, ?, ?);
                """,
                (customer.name, customer.email, customer.currency, customer.tax_country, customer.tax_state)
            )
            customer.id = cursor.lastrowid
            conn.commit()
        return customer

    def get(self, customer_id: int) -> Optional[Customer]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,)).fetchone()
            if not row:
                return None
            return Customer(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                currency=row["currency"],
                tax_country=row["tax_country"],
                tax_state=row["tax_state"]
            )

    def find_by_email(self, email: str) -> Optional[Customer]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM customers WHERE email = ?;", (email,)).fetchone()
            if not row:
                return None
            return Customer(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                currency=row["currency"],
                tax_country=row["tax_country"],
                tax_state=row["tax_state"]
            )

    def list_all(self) -> list[Customer]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM customers;").fetchall()
            return [
                Customer(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    currency=row["currency"],
                    tax_country=row["tax_country"],
                    tax_state=row["tax_state"]
                ) for row in rows
            ]

class PlanRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, plan: Plan) -> Plan:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO plans (name, pricing_type, billing_period, base_price, currency, usage_metric)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    plan.name,
                    plan.pricing_type.value if hasattr(plan.pricing_type, "value") else str(plan.pricing_type),
                    plan.billing_period.value if hasattr(plan.billing_period, "value") else str(plan.billing_period),
                    plan.base_price.to_storage(),
                    plan.currency,
                    plan.usage_metric
                )
            )
            plan.id = cursor.lastrowid
            conn.commit()
        return plan

    def get(self, plan_id: int) -> Optional[Plan]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM plans WHERE id = ?;", (plan_id,)).fetchone()
            if not row:
                return None
            return Plan(
                id=row["id"],
                name=row["name"],
                pricing_type=PricingType(row["pricing_type"]),
                billing_period=BillingPeriod(row["billing_period"]),
                base_price=Money.from_storage(row["base_price"], row["currency"]),
                currency=row["currency"],
                usage_metric=row["usage_metric"]
            )

    def list_all(self) -> list[Plan]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM plans;").fetchall()
            return [
                Plan(
                    id=row["id"],
                    name=row["name"],
                    pricing_type=PricingType(row["pricing_type"]),
                    billing_period=BillingPeriod(row["billing_period"]),
                    base_price=Money.from_storage(row["base_price"], row["currency"]),
                    currency=row["currency"],
                    usage_metric=row["usage_metric"]
                ) for row in rows
            ]

class PlanTierRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, plan_id: int, from_units: int, to_units: Optional[int], unit_price: Money) -> int:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO plan_tiers (plan_id, from_units, to_units, unit_price)
                VALUES (?, ?, ?, ?);
                """,
                (plan_id, from_units, to_units, unit_price.to_storage())
            )
            new_id = cursor.lastrowid
            conn.commit()
        return new_id

    def list_for_plan(self, plan_id: int, currency: str) -> list[tuple[int, Optional[int], Money]]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT from_units, to_units, unit_price FROM plan_tiers WHERE plan_id = ? ORDER BY from_units;",
                (plan_id,)
            ).fetchall()
            return [
                (row["from_units"], row["to_units"], Money.from_storage(row["unit_price"], currency))
                for row in rows
            ]

class DiscountRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, code: str, discount_type: str, value: str, currency: Optional[str] = None) -> int:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO discounts (code, discount_type, value, currency)
                VALUES (?, ?, ?, ?);
                """,
                (code, discount_type, value, currency)
            )
            new_id = cursor.lastrowid
            conn.commit()
        return new_id

    def get_by_code(self, code: str) -> Optional[dict]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM discounts WHERE code = ?;", (code,)).fetchone()
            if not row:
                return None
            return dict(row)

class SubscriptionRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, subscription: Subscription) -> Subscription:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO subscriptions (customer_id, plan_id, status, current_period_start, current_period_end, trial_end, past_due_since)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    subscription.customer_id,
                    subscription.plan_id,
                    subscription.status.value if hasattr(subscription.status, "value") else str(subscription.status),
                    subscription.current_period_start.isoformat(),
                    subscription.current_period_end.isoformat(),
                    subscription.trial_end.isoformat() if subscription.trial_end else None,
                    subscription.past_due_since.isoformat() if subscription.past_due_since else None
                )
            )
            subscription.id = cursor.lastrowid
            conn.commit()
        return subscription

    def get(self, subscription_id: int) -> Optional[Subscription]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM subscriptions WHERE id = ?;", (subscription_id,)).fetchone()
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
                past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None
            )

    def list_all(self) -> list[Subscription]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM subscriptions;").fetchall()
            return [
                Subscription(
                    id=row["id"],
                    customer_id=row["customer_id"],
                    plan_id=row["plan_id"],
                    status=SubscriptionStatus(row["status"]),
                    current_period_start=date.fromisoformat(row["current_period_start"]),
                    current_period_end=date.fromisoformat(row["current_period_end"]),
                    trial_end=date.fromisoformat(row["trial_end"]) if row["trial_end"] else None,
                    past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None
                ) for row in rows
            ]

    def get_due_for_billing(self, as_of: date) -> list[Subscription]:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM subscriptions 
                WHERE current_period_end <= ? 
                AND status = ?;
                """,
                (as_of.isoformat(), SubscriptionStatus.ACTIVE.value)
            ).fetchall()
            return [
                Subscription(
                    id=row["id"],
                    customer_id=row["customer_id"],
                    plan_id=row["plan_id"],
                    status=SubscriptionStatus(row["status"]),
                    current_period_start=date.fromisoformat(row["current_period_start"]),
                    current_period_end=date.fromisoformat(row["current_period_end"]),
                    trial_end=date.fromisoformat(row["trial_end"]) if row["trial_end"] else None,
                    past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None
                ) for row in rows
            ]

    def update_period(self, subscription_id: int, new_start: date, new_end: date) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                UPDATE subscriptions 
                SET current_period_start = ?, current_period_end = ? 
                WHERE id = ?;
                """,
                (new_start.isoformat(), new_end.isoformat(), subscription_id)
            )
            conn.commit()

    def update_status(
        self,
        subscription_id: int,
        new_status: SubscriptionStatus,
        past_due_since: Optional[date] = None,
    ) -> None:
        with self.db.connect() as conn:
            conn.execute(
                """
                UPDATE subscriptions 
                SET status = ?, past_due_since = ? 
                WHERE id = ?;
                """,
                (
                    new_status.value if hasattr(new_status, "value") else str(new_status),
                    past_due_since.isoformat() if past_due_since else None,
                    subscription_id
                )
            )
            conn.commit()

    def update_plan(self, subscription_id: int, new_plan_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE subscriptions SET plan_id = ? WHERE id = ?;",
                (new_plan_id, subscription_id)
            )
            conn.commit()

class UsageRecordRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, subscription_id: int, metric: str, quantity: int) -> int:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usage_records (subscription_id, metric, quantity, recorded_at)
                VALUES (?, ?, ?, ?);
                """,
                (subscription_id, metric, quantity, datetime.utcnow().isoformat())
            )
            new_id = cursor.lastrowid
            conn.commit()
        return new_id

    def sum_for_period(
        self, subscription_id: int, metric: str, period_start: date, period_end: date
    ) -> int:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(quantity), 0) as total 
                FROM usage_records 
                WHERE subscription_id = ? 
                AND metric = ? 
                AND recorded_at >= ? 
                AND recorded_at < ?;
                """,
                (subscription_id, metric, period_start.isoformat(), period_end.isoformat())
            ).fetchone()
            return row["total"]

class InvoiceRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, invoice: Invoice) -> Invoice:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoices (subscription_id, customer_id, status, period_start, period_end, subtotal, discount_total, tax_total, total_amount, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    invoice.subscription_id,
                    invoice.customer_id,
                    invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status),
                    invoice.period_start.isoformat(),
                    invoice.period_end.isoformat(),
                    invoice.subtotal.to_storage(),
                    invoice.discount_total.to_storage(),
                    invoice.tax_total.to_storage(),
                    invoice.total_amount.to_storage(),
                    invoice.pdf_path
                )
            )
            invoice.id = cursor.lastrowid
            conn.commit()
        return invoice

    def get(self, invoice_id: int) -> Optional[Invoice]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_