"""
build_invoice — PURE function that turns inputs into an Invoice dataclass.

⚠️ NO database calls here. No `datetime.now()`. No PDF. Just math.

The order is FIXED:
    1. base       = strategy.calculate(usage)
    2. discount   = discount.apply(base) if discount else 0
    3. taxable    = base - discount
    4. tax        = tax_calc.apply(taxable)
    5. total      = taxable + tax.total
"""

from datetime import date
from typing import Optional
from billing_engine.money import Money
from billing_engine.models import Invoice, InvoiceLineItem, InvoiceStatus, Subscription
from billing_engine.pricing.base import PricingStrategy
from billing_engine.discounts.base import DiscountStrategy, DiscountContext
from billing_engine.taxes.base import TaxCalculator, TaxContext

def build_invoice(
    subscription: Subscription,
    period_start: date,
    period_end: date,
    quantity: int,
    pricing_strategy: PricingStrategy,
    discount_strategy: Optional[DiscountStrategy],
    invoice_count_so_far: int,
    tax_calculator: TaxCalculator,
    customer_country: str,
    customer_state: Optional[str],
    seller_country: str,
    seller_state: Optional[str]
) -> Invoice:
    
    # 1. Compute Base Usage/Flat charges
    subtotal = pricing_strategy.calculate(quantity)
    line_items = [InvoiceLineItem(id=None, invoice_id=None, description="Base Plan Charge", amount=subtotal)]
    
    # 2. Process Discounts if attached
    discount_amount = Money.zero(subtotal.currency)
    if discount_strategy:
        disc_ctx = DiscountContext(invoice_count_so_far=invoice_count_so_far)
        discount_amount = discount_strategy.apply(subtotal, disc_ctx)
        
    taxable_amount = subtotal - discount_amount
    
    # 3. Apply Localized Taxation Strategies
    tax_ctx = TaxContext(
        customer_country=customer_country,
        customer_state=customer_state,
        seller_country=seller_country,
        seller_state=seller_state
    )
    tax_breakdown = tax_calculator.apply(taxable_amount, tax_ctx)
    
    # Append tax calculations as line items
    for label, amt in tax_breakdown.components:
        line_items.append(InvoiceLineItem(id=None, invoice_id=None, description=label, amount=amt))
        
    total_amount = taxable_amount + tax_breakdown.total
    
    # 4. Generate Draft Invoice Model
    return Invoice(
        id=None,
        subscription_id=subscription.id,
        period_start=period_start,
        period_end=period_end,
        subtotal=subtotal,
        discount_amount=discount_amount,
        tax_amount=tax_breakdown.total,
        total_amount=total_amount,
        status=InvoiceStatus.DRAFT,
        line_items=line_items
    )