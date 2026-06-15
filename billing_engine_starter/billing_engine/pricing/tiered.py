from dataclasses import dataclass
from typing import Optional

from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


@dataclass(frozen=True)
class Tier:
    from_units: int
    to_units: Optional[int]   
    unit_price: Money


class TieredPricing(PricingStrategy):

    def __init__(self, tiers: list[Tier]) -> None:
        if not tiers:
            raise ValueError("Tiers list cannot be empty")
        self.tiers = sorted(tiers, key=lambda t: t.from_units)

    def calculate(self, quantity: int) -> Money:
        if quantity <= 0:
            return Money(0, self.tiers[0].unit_price.currency)

        total_amount = Money(0, self.tiers[0].unit_price.currency)
        remaining = quantity

        for tier in self.tiers:
            if remaining <= 0:
                break

            tier_span = (tier.to_units - tier.from_units) if tier.to_units is not None else remaining
            units_in_tier = min(remaining, tier_span)

            total_amount += tier.unit_price * units_in_tier
            remaining -= units_in_tier

        return total_amount