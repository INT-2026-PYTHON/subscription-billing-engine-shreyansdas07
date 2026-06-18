from __future__ import annotations

from datetime import date
from typing import Optional

from billing_engine.money import Money
from billing_engine.models import (
    Invoice, InvoiceStatus, InvoiceLineItem, LineItemKind, Subscription, Plan,
)
from billing_engine.pricing.base import PricingStrategy
from billing_engine.discounts.base import Discount, DiscountContext
from billing_engine.taxes.base import TaxCalculator, TaxContext


def build_invoice(
    subscription: Subscription,
    plan: Plan,
    strategy: PricingStrategy,
    discount: Optional[Discount],
    tax_calc: TaxCalculator,
    tax_context: TaxContext,
    usage_quantity: int,
    period_start: date,
    period_end: date,
    invoice_count_so_far: int,
) -> Invoice:
    base_amount = strategy.calculate(usage_quantity)
    
    discount_amount = Money(0)
    if discount:
        discount_context = DiscountContext(
            customer_id=subscription.customer_id,
            invoice_count_so_far=invoice_count_so_far
        )
        discount_amount = discount.apply(base_amount, discount_context)
        
    taxable_amount = base_amount - discount_amount
    
    tax_result = tax_calc.apply(taxable_amount, tax_context)
    
    total_amount = taxable_amount + tax_result.total

    line_items = []
    
    line_items.append(
        InvoiceLineItem(
            id=None,
            invoice_id=None,
            kind=LineItemKind.BASE,
            amount=base_amount,
            description=f"Base plan charges for {plan.name}"
        )
    )
    
    if discount_amount > 0:
        line_items.append(
            InvoiceLineItem(
                id=None,
                invoice_id=None,
                kind=LineItemKind.DISCOUNT,
                amount=-discount_amount,
                description=f"Discount applied: {discount.name if hasattr(discount, 'name') else 'Promo'}"
            )
        )
        
    if tax_result.total > 0:
        line_items.append(
            InvoiceLineItem(
                id=None,
                invoice_id=None,
                kind=LineItemKind.TAX,
                amount=tax_result.total,
                description=f"Tax charges ({tax_result.rate_summary})"
            )
        )

    return Invoice(
        id=None,
        subscription_id=subscription.id,
        customer_id=subscription.customer_id,
        status=InvoiceStatus.DRAFT,
        period_start=period_start,
        period_end=period_end,
        subtotal=base_amount,
        discount_total=discount_amount,
        tax_total=tax_result.total,
        total_amount=total_amount,
        line_items=line_items
    )