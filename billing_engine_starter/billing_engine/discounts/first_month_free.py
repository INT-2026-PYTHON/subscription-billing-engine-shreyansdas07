from billing_engine.money import Money
from billing_engine.discounts.base import DiscountStrategy, DiscountContext

class FirstMonthFree(DiscountStrategy):
    def apply(self, subtotal: Money, context: DiscountContext) -> Money:
        if context.invoice_count_so_far == 0:
            return Money(0, subtotal.currency)
        return subtotal