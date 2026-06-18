from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class VATCalculator(TaxCalculator):

    def __init__(self, rate: Decimal) -> None:
        if not isinstance(rate, Decimal):
            raise TypeError("VAT rate must be a Decimal instance")
        if not (Decimal("0.00") <= rate <= Decimal("1.00")):
            raise ValueError("VAT rate must be between 0.00 and 1.00")
        self.rate = rate

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        vat_amount = taxable * self.rate
        percentage_str = f"{self.rate * 100}%"
        
        return TaxBreakdown(
            total=vat_amount,
            components=[(f"VAT {percentage_str}", vat_amount)],
            rate_summary=f"VAT {percentage_str}"
        )