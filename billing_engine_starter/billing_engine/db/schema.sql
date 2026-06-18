from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from billing_engine.db.database import Database
from billing_engine.money import Money
from billing_engine.models import (
    Customer,
    Plan, PricingType, BillingPeriod,
    Subscription, SubscriptionStatus,
    Invoice, InvoiceStatus, InvoiceLineItem, LineItemKind,
    LedgerEntry, LedgerDirection,
)


class CustomerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, customer: Customer) -> Customer:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO customers (name, email, country_code, state_code)
                VALUES (?, ?, ?, ?);
                """,
                (
                    customer.name,
                    customer.email,
                    getattr(customer, "tax_country", getattr(customer, "country_code", "")),
                    getattr(customer, "tax_state", getattr(customer, "state_code", ""))
                )
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
                currency=row.get("currency", "USD"),
                tax_country=row["country_code"],
                tax_state=row["state_code"]
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
                currency=row.get("currency", "USD"),
                tax_country=row["country_code"],
                tax_state=row["state_code"]
            )

    def list_all(self) -> list[Customer]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM customers;").fetchall()
            return [
                Customer(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    currency=row.get("currency", "USD"),
                    tax_country=row["country_code"],
                    tax_state=row["state_code"]
                ) for row in rows
            ]


class PlanRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, plan: Plan) -> Plan:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO plans (name, pricing_type, billing_period, currency, config_json)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    plan.name,
                    plan.pricing_type.value if hasattr(plan.pricing_type, "value") else str(plan.pricing_type),
                    plan.billing_period.value if hasattr(plan.billing_period, "value") else str(plan.billing_period),
                    plan.currency,
                    getattr(plan, "config_json", "{}")
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
                base_price=Money.from_storage(row.get("base_price", "0.00"), row["currency"]),
                currency=row["currency"],
                usage_metric=row.get("usage_metric", "units")
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
                    base_price=Money.from_storage(row.get("base_price", "0.00"), row["currency"]),
                    currency=row["currency"],
                    usage_metric=row.get("usage_metric", "units")
                ) for row in rows
            ]


class PlanTierRepository:
    def __init__(self, db: Database) -> None:
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
    def __init__(self, db: Database) -> None:
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
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, subscription: Subscription) -> Subscription:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            status_val = subscription.status.value if hasattr(subscription.status, "value") else str(subscription.status)
            if status_val == "TRIALING":
                status_val = "TRIAL"
            cursor.execute(
                """
                INSERT INTO subscriptions (customer_id, plan_id, status, current_period_start, current_period_end, trial_end, discount_id, past_due_since)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    subscription.customer_id,
                    subscription.plan_id,
                    status_val,
                    subscription.current_period_start.isoformat(),
                    subscription.current_period_end.isoformat(),
                    subscription.trial_end.isoformat() if subscription.trial_end else None,
                    getattr(subscription, "discount_id", None),
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
            status_str = row["status"]
            if status_str == "TRIAL":
                status_str = "TRIALING"
            return Subscription(
                id=row["id"],
                customer_id=row["customer_id"],
                plan_id=row["plan_id"],
                status=SubscriptionStatus(status_str),
                current_period_start=date.fromisoformat(row["current_period_start"]),
                current_period_end=date.fromisoformat(row["current_period_end"]),
                trial_end=date.fromisoformat(row["trial_end"]) if row["trial_end"] else None,
                past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None
            )

    def list_all(self) -> list[Subscription]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM subscriptions;").fetchall()
            results = []
            for row in rows:
                status_str = row["status"]
                if status_str == "TRIAL":
                    status_str = "TRIALING"
                results.append(
                    Subscription(
                        id=row["id"],
                        customer_id=row["customer_id"],
                        plan_id=row["plan_id"],
                        status=SubscriptionStatus(status_str),
                        current_period_start=date.fromisoformat(row["current_period_start"]),
                        current_period_end=date.fromisoformat(row["current_period_end"]),
                        trial_end=date.fromisoformat(row["trial_end"]) if row["trial_end"] else None,
                        past_due_since=date.fromisoformat(row["past_due_since"]) if row["past_due_since"] else None
                    )
                )
            return results

    def get_due_for_billing(self, as_of: date) -> list[Subscription]:
        with self.db.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM subscriptions 
                WHERE current_period_end <= ? 
                AND status = 'ACTIVE';
                """,
                (as_of.isoformat(),)
            ).fetchall()
            return [
                Subscription(
                    id=row["id"],
                    customer_id=row["customer_id"],
                    plan_id=row["plan_id"],
                    status=SubscriptionStatus.ACTIVE,
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
            status_val = new_status.value if hasattr(new_status, "value") else str(new_status)
            if status_val == "TRIALING":
                status_val = "TRIAL"
            conn.execute(
                """
                UPDATE subscriptions 
                SET status = ?, past_due_since = ? 
                WHERE id = ?;
                """,
                (
                    status_val,
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
    def __init__(self, db: Database) -> None:
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
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, invoice: Invoice) -> Invoice:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            currency = invoice.total_amount.currency
            cursor.execute(
                """
                INSERT INTO invoices (subscription_id, period_start, period_end, currency, subtotal, discount_total, tax_total, total, status, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    invoice.subscription_id,
                    invoice.period_start.isoformat(),
                    invoice.period_end.isoformat(),
                    currency,
                    invoice.subtotal.to_storage(),
                    invoice.discount_total.to_storage(),
                    invoice.tax_total.to_storage(),
                    invoice.total_amount.to_storage(),
                    invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status),
                    invoice.pdf_path
                )
            )
            invoice.id = cursor.lastrowid
            conn.commit()
        return invoice

    def get(self, invoice_id: int) -> Optional[Invoice]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_id,)).fetchone()
            if not row:
                return None
            currency = row["currency"]
            return Invoice(
                id=row["id"],
                subscription_id=row["subscription_id"],
                customer_id=row.get("customer_id", 0),
                status=InvoiceStatus(row["status"]),
                period_start=date.fromisoformat(row["period_start"]),
                period_end=date.fromisoformat(row["period_end"]),
                subtotal=Money.from_storage(row["subtotal"], currency),
                discount_total=Money.from_storage(row["discount_total"], currency),
                tax_total=Money.from_storage(row["tax_total"], currency),
                total_amount=Money.from_storage(row["total"], currency),
                pdf_path=row["pdf_path"],
                line_items=[]
            )

    def count_for_subscription(self, subscription_id: int) -> int:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM invoices WHERE subscription_id = ?;",
                (subscription_id,)
            ).fetchone()
            return row["count"]

    def mark_paid(self, invoice_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE invoices SET status = 'PAID' WHERE id = ?;",
                (invoice_id,)
            )
            conn.commit()

    def mark_failed(self, invoice_id: int) -> None:
        with self.db.connect() as conn:
            conn.execute(
                "UPDATE invoices SET status = 'FAILED' WHERE id = ?;",
                (invoice_id,)
            )
            conn.commit()

    def set_pdf_path(self, invoice_id: int, path: str) -> None:
        with self.db.connect() as conn:
            conn.execute("UPDATE invoices SET pdf_path = ? WHERE id = ?;", (path, invoice_id))
            conn.commit()


class InvoiceLineItemRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, line_item: InvoiceLineItem) -> InvoiceLineItem:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoice_line_items (invoice_id, description, amount, kind)
                VALUES (?, ?, ?, ?);
                """,
                (
                    line_item.invoice_id,
                    line_item.description,
                    line_item.amount.to_storage(),
                    line_item.kind.value if hasattr(line_item.kind, "value") else str(line_item.kind)
                )
            )
            line_item.id = cursor.lastrowid
            conn.commit()
        return line_item

    def list_for_invoice(self, invoice_id: int) -> list[InvoiceLineItem]:
        with self.db.connect() as conn:
            invoice_row = conn.execute("SELECT currency FROM invoices WHERE id = ?;", (invoice_id,)).fetchone()
            currency = invoice_row["currency"] if invoice_row else "USD"
            rows = conn.execute("SELECT * FROM invoice_line_items WHERE invoice_id = ?;", (invoice_id,)).fetchall()
            return [
                InvoiceLineItem(
                    id=row["id"],
                    invoice_id=row["invoice_id"],
                    kind=LineItemKind(row["kind"]),
                    amount=Money.from_storage(row["amount"], currency),
                    description=row["description"]
                ) for row in rows
            ]


class LedgerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ledger_entries (invoice_id, customer_id, amount, currency, direction, reason)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    getattr(entry, "invoice_id", getattr(entry, "reference_id", None)),
                    entry.customer_id,
                    entry.amount.to_storage(),
                    entry.amount.currency,
                    entry.direction.value if hasattr(entry.direction, "value") else str(entry.direction),
                    getattr(entry, "reason", getattr(entry, "description", "Ledger entry"))
                )
            )
            entry.id = cursor.lastrowid
            conn.commit()
        return entry

    def list_for_customer(self, customer_id: int) -> list[LedgerEntry]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM ledger_entries WHERE customer_id = ? ORDER BY id ASC;", (customer_id,)).fetchall()
            return [
                LedgerEntry(
                    id=row["id"],
                    customer_id=row["customer_id"],
                    direction=LedgerDirection(row["direction"]),
                    amount=Money.from_storage(row["amount"], row["currency"]),
                    description=row["reason"],
                    reference_id=row["invoice_id"]
                ) for row in rows
            ]

    def update(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")


class PaymentAttemptRepository:
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
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO payment_attempts (invoice_id, attempt_no, status, failure_reason, next_retry_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    invoice_id,
                    attempt_no,
                    status.upper(),
                    failure_reason,
                    next_retry_at.isoformat() if next_retry_at else None
                )
            )
            new_id = cursor.lastrowid
            conn.commit()
        return new_id

    def list_for_invoice(self, invoice_id: int) -> list[dict]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM payment_attempts WHERE invoice_id = ? ORDER BY attempt_no ASC;", (invoice_id,)).fetchall()
            return [dict(row) for row in rows]

    def count_for_invoice(self, invoice_id: int) -> int:
        with self.db.connect() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM payment_attempts WHERE invoice_id = ?;", (invoice_id,)).fetchone()
            return row["count"]