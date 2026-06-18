from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy

"""
TieredPricing — different price per unit depending on the tier the quantity falls into.

This is the "cumulative" / "stacked" tier model, NOT the "volume" model:
    Tiers: [(0, 1000, ₹2.00), (1000, 5000, ₹1.50), (5000, None, ₹1.00)]
    Quantity = 6000:
        First 1000 units  @ ₹2.00 = ₹2000
        Next  4000 units  @ ₹1.50 = ₹6000
        Last  1000 units  @ ₹1.00 = ₹1000
        ------------------------------------
        Total                     = ₹9000

A tier with `to_units = None` is the open-ended top tier.

Tier boundaries are HALF-OPEN on the right: a tier (from, to, price)
covers units strictly less than `to` (i.e. [from, to)).
"""

@dataclass(frozen=True)
class Tier:
    from_units: int
    to_units: Optional[int]   
    unit_price: Money


class TieredPricing(PricingStrategy):
    def __init__(self, tiers: List[Tier]):
        if not tiers:
            raise ValueError("Tier list cannot be empty")
        
        # Sort tiers chronologically by lower boundary
        sorted_tiers = sorted(tiers, key=lambda t: t.from_units)
        
        # Check continuity and upper bounds
        for i in range(len(sorted_tiers) - 1):
            if sorted_tiers[i+1].from_units != sorted_tiers[i].to_units:
                raise ValueError("Tiers must be contiguous")
            if sorted_tiers[i].to_units is None:
                raise ValueError("Only the final tier can be open-ended (to_units=None)")
        
        if sorted_tiers[-1].to_units is not None:
            raise ValueError("The final tier must be open-ended (to_units=None)")

        # Validate currency uniformity
        base_currency = sorted_tiers[0].unit_price.currency
        for tier in sorted_tiers:
            if tier.unit_price.currency != base_currency:
                raise ValueError("All tiers must use the same currency")
            if tier.unit_price.is_negative():
                raise ValueError("Tier unit prices cannot be negative")

        self.tiers = sorted_tiers

    def calculate(self, quantity: int) -> Money:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if quantity == 0:
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