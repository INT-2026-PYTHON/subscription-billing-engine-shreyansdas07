from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext


@dataclass(frozen=True)
class ProrationResult:
    credit_amount: Money     
    charge_amount: Money     
    credit_tax: Money        
    charge_tax: Money        


def compute_proration(
    old_plan_price: Money,
    new_plan_price: Money,
    period_start: date,
    period_end: date,
    switch_date: date,
    tax_calc: TaxCalculator,
    tax_context: TaxContext,
) -> ProrationResult:
    if not (period_start <= switch_date <= period_end):
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