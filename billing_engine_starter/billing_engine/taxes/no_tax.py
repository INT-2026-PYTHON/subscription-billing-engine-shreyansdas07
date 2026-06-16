"""
NoTax — for jurisdictions where you don't charge tax (or the customer is tax-exempt).
"""

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown

class NoTax(TaxCalculator):
    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
<<<<<<< Updated upstream
        # TODO Day 1
        raise NotImplementedError("Day 1: implement NoTax.apply")
=======
        return TaxBreakdown(components=[], total=Money.zero(taxable.currency))
>>>>>>> Stashed changes
..
