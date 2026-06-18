from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Optional

from billing_engine.db import (
    Database,
    CustomerRepository, PlanRepository, SubscriptionRepository,
    UsageRecordRepository, InvoiceRepository, InvoiceLineItemRepository,
    LedgerRepository,
)
from billing_engine.models import (
    BillingResult, 
    SubscriptionStatus, 
    LedgerEntry, 
    LedgerDirection,
    Subscription
)
from billing_engine.billing.pipeline import build_invoice


class BillingCycle:

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
        strategy_factory: Callable,
        discount_factory: Callable,
        tax_factory: Callable,
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

    def run(self, as_of: date) -> BillingResult:
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
            discount = self.discount_factory(getattr(sub, "discount_id", None))
            tax_calc, tax_context = self.tax_factory(customer)
            
            usage = self.usage_repo.sum_for_period(sub.id, "units", sub.current_period_start, sub.current_period_end)
            invoice_count = getattr(self.invoice_repo, "count_for_subscription", lambda x: 0)(sub.id)

            # Generate draft entity via purely mathematical layer
            draft_invoice = build_invoice(
                subscription=sub,
                customer=customer,
                plan=plan,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                usage_quantity=usage,
                invoice_count_so_far=invoice_count,
                strategy=strategy,
                discount=discount,
                tax_calc=tax_calc,
                tax_context=tax_context
            )

            # Execution block safely nested within atomic boundaries
            try:
                with self.db.transaction():
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
                        amount=saved_invoice.total_amount,
                        currency=saved_invoice.subtotal.currency,
                        direction=LedgerDirection.DEBIT,
                        reason=f"Invoice #{saved_invoice.id} Base Service Charges"
                    ))
                    
                    # 4. Roll dates forward to next cycle period
                    new_start = sub.current_period_end
                    days_in_period = (sub.current_period_end - sub.current_period_start).days or 30
                    new_end = new_start + timedelta(days=days_in_period)
                    self.subscription_repo.update_period(sub.id, new_start, new_end)
                    
                invoices_created += 1
                
            except sqlite3.IntegrityError:
                # Triggers automatically when checking UNIQUE(subscription_id, period_start)
                invoices_skipped += 1

        return BillingResult(invoices_created, invoices_skipped, trials_activated)

    def upgrade_subscription(self, subscription_id: int, new_plan_id: int, switch_date: date) -> None:
        """Mid-cycle upgrade."""
        pass