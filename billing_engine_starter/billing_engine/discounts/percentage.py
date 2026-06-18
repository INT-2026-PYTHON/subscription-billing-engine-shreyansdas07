from decimal import Decimal
from billing_engine.money import Money
from billing_engine.discounts.base import DiscountStrategy, DiscountContext

class PercentageDiscount(DiscountStrategy):
    def __init__(self, percentage: Decimal):
        if isinstance(percentage, float):
            raise TypeError("Percentage must be a Decimal, not a float")
        if not (Decimal("0.00") <= percentage <= Decimal("1.00")):
            raise ValueError("Percentage must be between 0.00 (0%) and 1.00 (100%)")
        self.percentage = percentage

    def apply(self, subtotal: Money, context: DiscountContext) -> Money:
        return subtotal * self.percentage