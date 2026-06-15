from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


class FlatRate(PricingStrategy):

    def __init__(self, amount: Money) -> None:
        self.amount = amount

    def calculate(self, quantity: int) -> Money:
        return self.amount