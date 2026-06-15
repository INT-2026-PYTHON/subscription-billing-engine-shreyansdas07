from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class NoTax(TaxCalculator):

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        zero_tax = Money(0, taxable.currency)
        return TaxBreakdown(
            total=zero_tax,
            components=[],
            rate_summary="No Tax (0%)"
        )