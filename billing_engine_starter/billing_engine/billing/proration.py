<<<<<<< Updated upstream
"""
Proration — Day 4 stretch.

Mid-cycle plan change: customer is on Plan A from period_start to period_end,
but on `switch_date` they upgrade (or downgrade) to Plan B.

Day-count proration:
    total_days     = (period_end - period_start).days
    used_days      = (switch_date - period_start).days
    remaining_days = total_days - used_days

    credit = old_price * (remaining_days / total_days)
    charge = new_price * (remaining_days / total_days)

Tax MUST be recalculated on BOTH legs (reverse-tax on the credit,
fresh tax on the new charge). Tax is NOT prorated linearly — the tax
on a proration credit/charge is just `tax_calc.apply(credit_or_charge)`.

The two legs are returned as TAX-INCLUSIVE Money values for the
PRORATION_CREDIT (negative) and PRORATION_CHARGE (positive) line items.
"""

=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
=======
# Inside billing_engine/billing/proration.py
>>>>>>> Stashed changes
from decimal import Decimal
from typing import NamedTuple
from billing_engine.money import Money
<<<<<<< Updated upstream
from billing_engine.taxes.base import TaxCalculator, TaxContext


@dataclass(frozen=True)
class ProrationResult:
<<<<<<< Updated upstream
    credit_amount: Money     # always returned as a POSITIVE Money; caller negates for line item
    charge_amount: Money     # always positive
    credit_tax: Money        # tax that was on the credit
    charge_tax: Money        # tax that is on the new charge
=======
    credit_amount: Money     
    charge_amount: Money     
    credit_tax: Money        
    charge_tax: Money        
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes

class ProrationResult(NamedTuple):
    credit_amount: Money
    charge_amount: Money
    credit_tax: Money
    charge_tax: Money

def compute_proration(
    old_plan_price: Money,
    new_plan_price: Money,
    period_start,
    period_end,
    switch_date,
    tax_calc,
    tax_context,
) -> ProrationResult:
<<<<<<< Updated upstream
    """Pure function. STRETCH — implement only after Days 1+2 are green."""
    # TODO Day 4
    raise NotImplementedError("Day 4: implement compute_proration")
=======
    if not (period_start <= switch_date <= period_end):
<<<<<<< Updated upstream
        raise ValueError("switch_date must fall within period_start and period_end")

    total_days = (period_end - period_start).days
    if total_days <= 0:
        raise ValueError("Invalid period: period_end must be after period_start")

    used_days = (switch_date - period_start).days
    remaining_days = total_days - used_days

    ratio = Decimal(remaining_days) / Decimal(total_days)

    credit = old_plan_price * ratio
    charge = new_plan_price * ratio

    credit_tax_result = tax_calc.apply(credit, tax_context)
    charge_tax_result = tax_calc.apply(charge, tax_context)

    return ProrationResult(
        credit_amount=credit,
        charge_amount=charge,
        credit_tax=credit_tax_result.total,
        charge_tax=charge_tax_result.total
    )
=======
        raise ValueError(f"switch_date {switch_date} outside period [{period_start}, {period_end}]")
    if old_plan_price.currency != new_plan_price.currency:
        raise ValueError("Cannot prorate across currencies")

    total_days = (period_end - period_start).days
    if total_days <= 0:
        raise ValueError("Period must be positive")

    remaining_days = (period_end - switch_date).days
    ratio = Decimal(remaining_days) / Decimal(total_days)

    credit_amount = old_plan_price * ratio
    charge_amount = new_plan_price * ratio

    credit_tax = tax_calc.apply(credit_amount, tax_context).total
    charge_tax = tax_calc.apply(charge_amount, tax_context).total

    return ProrationResult(credit_amount, charge_amount, credit_tax, charge_tax)
>>>>>>> Stashed changes
>>>>>>> Stashed changes
