from billing_engine.money import Money
from billing_engine.discounts.base import DiscountStrategy, DiscountContext

class FixedAmountDiscount(DiscountStrategy):
    def __init__(self, amount: Money):
        if not isinstance(amount, Money):
            raise TypeError("Amount must be an instance of Money")
        if amount.is_negative():
            raise ValueError("Discount amount cannot be negative")
        self.amount = amount

    def apply(self, subtotal: Money, context: DiscountContext) -> Money:
        if self.amount.currency != subtotal.currency:
            raise ValueError(f"Currency mismatch: discount is in {self.amount.currency}, but subtotal is in {subtotal.currency}")
            
        return min(self.amount, subtotal)