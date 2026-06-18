from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy

class Freemium(PricingStrategy):
    """Returns 0 for quantity <= free_quota, else delegates overage to inner strategy."""

    def __init__(self, free_quota: int, overage_strategy: PricingStrategy):
        if free_quota < 0:
            raise ValueError("Free quota cannot be negative")
        if not isinstance(overage_strategy, PricingStrategy):
            raise TypeError("Overage strategy must be a PricingStrategy instance")
        
        self.free_quota = free_quota
        self.overage_strategy = overage_strategy

    def calculate(self, quantity: int) -> Money:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
            
        if quantity <= self.free_quota:
            return Money(0, self.overage_strategy.calculate(0).currency)
            
        overage_quantity = quantity - self.free_quota
        return self.overage_strategy.calculate(overage_quantity)