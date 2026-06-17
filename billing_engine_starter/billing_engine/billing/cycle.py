<<<<<<< Updated upstream
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
=======
# Inside billing_engine/billing/cycle.py
import sqlite3
from datetime import date
from billing_engine.models import BillingResult, SubscriptionStatus, LedgerEntry, LedgerDirection
from billing_engine.billing.pipeline import build_invoice

class BillingCycle:
    def __init__(self, db, customer_repo, plan_repo, subscription_repo, usage_repo, invoice_repo, line_item_repo, ledger_repo, strategy_factory, discount_factory, tax_factory):
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        """Bill all subscriptions whose current period ends on or before `as_of`."""
        # TODO Day 3
        raise NotImplementedError("Day 3: implement BillingCycle.run")

    # --------------------------------------------------------
    def upgrade_subscription(self, subscription_id: int, new_plan_id: int, switch_date: date) -> None:
        """Mid-cycle upgrade — Day 4 stretch."""
        # TODO Day 4
        raise NotImplementedError("Day 4: implement BillingCycle.upgrade_subscription")
=======
        invoices_created = 0
        invoices_skipped = 0
        trials_activated = 0

        # Phase 1: Promote active trial structures
        for sub in self.subscription_repo.list_all():
            if sub.status == SubscriptionStatus.TRIAL and sub.trial_end and sub.trial_end <= as_of:
                self.subscription_repo.update_status(sub.id, SubscriptionStatus.ACTIVE)
                trials_activated += 1

        # Phase 2: Query pending subscriptions matching time ceilings
        due = self.subscription_repo.get_due_for_billing(as_of)
        
        for sub in due:
            plan = self.plan_repo.get(sub.plan_id)
            customer = self.customer_repo.get(sub.customer_id)
            
            strategy = self.strategy_factory(plan)
            discount = self.discount_factory(sub.discount_id)
            tax_calc, tax_context = self.tax_factory(customer)
            
            usage = self.usage_repo.sum_for_period(sub.id, "units", sub.current_period_start, sub.current_period_end)
            invoice_count = self.invoice_repo.count_for_subscription(sub.id)

            # Generate draft entity via purely mathematical layer
            draft_invoice = build_invoice(
                subscription_id=sub.id,
                customer=customer,
                plan=plan,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                usage_quantity=usage,
                invoice_count_so_far=invoice_count,
                strategy=strategy,
                discount=discount,
                discount_context=None, # pass relevant objects matching implementation signature
                tax_calc=tax_calc,
                tax_context=tax_context
            )

            # Execution block safely nested within atomic boundaries
            try:
                with self.db.transaction() as conn:
                    # 1. Save header to obtain invoice identity
                    saved_invoice = self.invoice_repo.add(draft_invoice)
                    
                    # 2. Add nested line item sub-records
                    for item in draft_invoice.line_items:
                        item.invoice_id = saved_invoice.id
                        self.line_item_repo.add(item)
                        
                    # 3. Post equivalent accounting ledger entry 
                    self.ledger_repo.add(LedgerEntry(
                        id=None,
                        invoice_id=saved_invoice.id,
                        customer_id=sub.customer_id,
                        amount=saved_invoice.total,
                        currency=saved_invoice.currency,
                        direction=LedgerDirection.DEBIT,
                        reason=f"Invoice #{saved_invoice.id} Base Service Charges"
                    ))
                    
                    # 4. Roll dates forward to next cycle period
                    # (Assuming plan mapping rules specify standard incremental step lookups)
                    new_start = sub.current_period_end
                    new_end = plan.calculate_next_period_end(new_start) 
                    self.subscription_repo.update_period(sub.id, new_start, new_end)
                    
                invoices_created += 1
                
            except sqlite3.IntegrityError:
                # Triggers automatically when checking UNIQUE(subscription_id, period_start)
                invoices_skipped += 1

        return BillingResult(invoices_created, invoices_skipped, trials_activated)
>>>>>>> Stashed changes
