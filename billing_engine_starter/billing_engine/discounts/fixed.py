from billing_engine.money import Money
from billing_engine.discounts.base import Discount, DiscountContext


class FixedAmountDiscount(Discount):
    def __init__(self, amount: Money) -> None:
        self.amount = amount

    def apply(self, subtotal: Money, context: DiscountContext) -> Money:
        if self.amount.currency != subtotal.currency:
            raise ValueError(f"Currency mismatch: discount is in {self.amount.currency}, but subtotal is in {subtotal.currency}")
            
        if self.amount >= subtotal:
            return subtotal
            
        return self.amount