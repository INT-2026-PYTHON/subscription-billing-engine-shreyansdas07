from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


class Freemium(PricingStrategy):

    def __init__(self, free_quota: int, overage_strategy: PricingStrategy) -> None:
        if free_quota < 0:
            raise ValueError("free_quota cannot be negative")
        self.free_quota = free_quota
        self.overage_strategy = overage_strategy

    def calculate(self, quantity: int) -> Money:
        if quantity <= self.free_quota:
            return Money(0, self.overage_strategy.calculate(0).currency)
            
        overage_quantity = quantity - self.free_quota
        return self.overage_strategy.calculate(overage_quantity)