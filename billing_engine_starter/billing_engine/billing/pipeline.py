<<<<<<< Updated upstream
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
=======
from datetime import date
from typing import Optional
from billing_engine.models import (
    Invoice,
    InvoiceStatus,
    InvoiceLineItem,
    LineItemKind,
    Plan,
    Customer,
)
from billing_engine.money import Money

def build_invoice(
    subscription_id: int,
    customer: Customer,
    plan: Plan,
    period_start: date,
    period_end: date,
    usage_quantity: int,
    invoice_count_so_far: int,
    strategy,          # Day 1 PricingStrategy
    discount,          # Day 1 Discount Strategy (Optional)
    discount_context,  # Instantiated Context
    tax_calc,          # Day 1 Tax Calculator
    tax_context,       # Instantiated Tax Context
) -> Invoice:
    """Builds an immutable Invoice instance with structured line items.

    This function operates purely on domain objects, generating the complete breakdown
    of charges, discounts, and taxes natively before saving.
    """
    # 1. Compute base gross charge
    base = strategy.calculate(usage_quantity)
    currency = base.currency

    # 2. Compute discount line item
    if discount is None:
        discount_amount = Money.zero(currency)
    else:
        discount_amount = discount.apply(base, discount_context)

    # 3. Handle base taxable ceiling
    taxable = base - discount_amount

    # 4. Generate tax breakdown matrices
    breakdown = tax_calc.apply(taxable, tax_context)
    
    # 5. Total summation
    total = taxable + breakdown.total

    # 6. Structuring line items sequence
    line_items = [
        InvoiceLineItem(
            id=None,
            invoice_id=None,
            description=f"{plan.name} Base Service Charge ({period_start} to {period_end})",
            amount=base,
            kind=LineItemKind.BASE,
        )
    ]

    # Append discount tracking only if it actively altered the subtotal
    if discount_amount > Money.zero(currency):
        line_items.append(
            InvoiceLineItem(
                id=None,
                invoice_id=None,
                description="Applied Discount Credit",
                amount=-discount_amount,  # Must match requirement to persist as negative
                kind=LineItemKind.DISCOUNT,
            )
        )

    # Deconstruct and append tax calculations dynamically
    for label, amt in breakdown.components:
        line_items.append(
            InvoiceLineItem(
                id=None,
                invoice_id=None,
                description=label,
                amount=amt,
                kind=LineItemKind.TAX,
            )
        )

    # 7. Unify everything inside a transient draft invoice
    return Invoice(
        id=None,
        subscription_id=subscription_id,
        period_start=period_start,
        period_end=period_end,
        currency=currency,
        subtotal=base,
        discount_total=discount_amount,
        tax_total=breakdown.total,
        total=total,
        status=InvoiceStatus.DRAFT,
        issued_at=None,
        pdf_path=None,
        line_items=line_items,  # Attaching nested array structure for validation passes
>>>>>>> Stashed changes
    )