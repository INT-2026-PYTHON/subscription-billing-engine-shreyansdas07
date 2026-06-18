from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy

class FlatRate(PricingStrategy):
    """Charges a fixed amount every billing period."""

    def __init__(self, amount: Money) -> None:
        if not isinstance(amount, Money):
            raise TypeError("Amount must be an instance of Money")
        if amount.is_negative():
            raise ValueError("Amount cannot be negative")
        self.amount = amount

    def calculate(self, quantity: int) -> Money:
        return self.amount