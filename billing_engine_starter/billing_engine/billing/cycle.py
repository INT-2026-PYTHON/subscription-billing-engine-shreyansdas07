"""
BillingCycle — finds due subscriptions, generates invoices, posts ledger DEBITs,
advances the subscription period. Must be IDEMPOTENT (safe to run twice).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from billing_engine.db import (
    Database,
    CustomerRepository, PlanRepository, SubscriptionRepository,
    UsageRecordRepository, InvoiceRepository, InvoiceLineItemRepository,
    LedgerRepository,
)
from billing_engine.models import Subscription


@dataclass
class BillingResult:
    invoices_created: int
    invoices_skipped_duplicate: int
    trials_activated: int


class BillingCycle:
    """Day-3 deliverable. Day-4 stretch: add `upgrade_subscription(...)`."""

    def __init__(
        self,
        db: Database,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
        subscription_repo: SubscriptionRepository,
        usage_repo: UsageRecordRepository,
        invoice_repo: InvoiceRepository,
        line_item_repo: InvoiceLineItemRepository,
        ledger_repo: LedgerRepository,
        strategy_factory: Callable,    # given a Plan, returns a PricingStrategy
        discount_factory: Callable,    # given a discount_id or None, returns a Discount or None
        tax_factory: Callable,         # given a Customer, returns (TaxCalculator, TaxContext)
    ) -> None:
        self.db = db
        self.customer_repo = customer_repo
        self.plan_repo = plan_repo
        self.subscription_repo = subscription_repo
        self.usage_repo = usage_repo
        self.invoice_repo = invoice_repo
        self.line_item_repo = line_item_repo
        self.ledger_repo = ledger_repo
        self.strategy_factory = strategy_factory
        self.discount_factory = discount_factory
        self.tax_factory = tax_factory

    # --------------------------------------------------------
    def run(self, as_of: date) -> BillingResult:
        """Bill all subscriptions whose current period ends on or before `as_of`."""
        # TODO Day 3
        raise NotImplementedError("Day 3: implement BillingCycle.run")

    # --------------------------------------------------------
    def upgrade_subscription(self, subscription_id: int, new_plan_id: int, switch_date: date) -> None:
<<<<<<< Updated upstream
        """Mid-cycle upgrade — Day 4 stretch."""
        # TODO Day 4
        raise NotImplementedError("Day 4: implement BillingCycle.upgrade_subscription")
=======
        with self.db.transaction():
            sub = self.subscription_repo.get_by_id(subscription_id)
            if not sub:
                raise ValueError(f"Subscription {subscription_id} not found.")
                
            old_plan = self.plan_repo.get_by_id(sub.plan_id)
            new_plan = self.plan_repo.get_by_id(new_plan_id)
            customer = self.customer_repo.get_by_id(sub.customer_id)
            
            proration_result = compute_proration(
                old_plan=old_plan,
                new_plan=new_plan,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                switch_date=switch_date
            )
            
            if proration_result.net_amount > 0:
                pass 
                
<<<<<<< Updated upstream
            if proration_result.net_amount != 0:
                self.ledger_repo.post_transaction(
                    customer_id=sub.customer_id,
                    amount=proration_result.net_amount,
                    description=f"Proration adjustment: Upgraded from {old_plan.name} to {new_plan.name}",
                    reference_id=sub.id
                )
                
            sub.plan_id = new_plan_id
            self.subscription_repo.save(sub)
=======
            except sqlite3.IntegrityError:
                # Triggers automatically when checking UNIQUE(subscription_id, period_start)
                invoices_skipped += 1

        return BillingResult(invoices_created, invoices_skipped, trials_activated)
>>>>>>> Stashed changes
# Append inside BillingCycle class in billing_engine/billing/cycle.py
from billing_engine.billing.proration import compute_proration
from billing_engine.models import Invoice, InvoiceStatus, InvoiceLineItem, LineItemKind

def upgrade_subscription(self, subscription_id: int, new_plan_id: int, switch_date) -> Invoice:
    sub = self.subscription_repo.get(subscription_id)
    old_plan = self.plan_repo.get(sub.plan_id)
    new_plan = self.plan_repo.get(new_plan_id)
    customer = self.customer_repo.get(sub.customer_id)

    old_strategy = self.strategy_factory(old_plan)
    new_strategy = self.strategy_factory(new_plan)

    old_price = old_strategy.calculate(0)
    new_price = new_strategy.calculate(0)

    tax_calc, tax_context = self.tax_factory(customer)

    pr = compute_proration(
        old_price, new_price, 
        sub.current_period_start, sub.current_period_end, 
        switch_date, tax_calc, tax_context
    )

    net_subtotal = pr.charge_amount - pr.credit_amount
    net_tax = pr.charge_tax - pr.credit_tax
    net_total = net_subtotal + net_tax

    with self.db.transaction() as conn:
        # Build Header
        invoice = Invoice(
            id=None, subscription_id=sub.id,
            period_start=switch_date, period_end=sub.current_period_end,
            currency=old_price.currency, subtotal=net_subtotal,
            discount_total=Money.zero(old_price.currency), tax_total=net_tax,
            total=net_total, status=InvoiceStatus.DRAFT, issued_at=None, pdf_path=None
        )
        saved = self.invoice_repo.add(invoice)

        # Build Line Items
        self.line_item_repo.add(InvoiceLineItem(
            id=None, invoice_id=saved.id,
            description=f"Prorated Credit for remaining days on {old_plan.name}",
            amount=-pr.credit_amount, kind=LineItemKind.PRORATION_CREDIT
        ))
        self.line_item_repo.add(InvoiceLineItem(
            id=None, invoice_id=saved.id,
            description=f"Prorated Charge for remaining days on {new_plan.name}",
            amount=pr.charge_amount, kind=LineItemKind.PRORATION_CHARGE
        ))

        # Ledger Entry
        self.ledger_repo.add(LedgerEntry(
            id=None, invoice_id=saved.id, customer_id=sub.customer_id,
            amount=net_total, currency=old_price.currency,
            direction=LedgerDirection.DEBIT, reason=f"Proration adjustments upgrade to {new_plan.name}"
        ))

        # Update core structural identity
        self.subscription_repo.update_plan(sub.id, new_plan_id)

    return saved
>>>>>>> Stashed changes
>>>>>>> Stashed changes
