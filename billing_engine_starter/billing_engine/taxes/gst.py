from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class GSTCalculator(TaxCalculator):

    def __init__(self, cgst: Decimal, sgst: Decimal, igst: Decimal) -> None:
        for name, rate in [("cgst", cgst), ("sgst", sgst), ("igst", igst)]:
            if not (Decimal("0.00") <= rate <= Decimal("1.00")):
                raise ValueError(f"{name} rate must be between 0.00 and 1.00")
                
        if cgst + sgst != igst:
            raise ValueError(f"Invalid GST configuration: CGST ({cgst}) + SGST ({sgst}) must equal IGST ({igst})")
            
        self.cgst = cgst
        self.sgst = sgst
        self.igst = igst

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        customer_state = getattr(context, "customer_state", getattr(context, "state_code", ""))
        seller_state = getattr(context, "seller_state", "")

        is_intra = bool(customer_state) and customer_state == seller_state

        if is_intra:
            cgst_amount = taxable * self.cgst
            sgst_amount = taxable * self.sgst
            total_tax = cgst_amount + sgst_amount
            
            components = [
                (f"CGST {self.cgst * 100}%", cgst_amount),
                (f"SGST {self.sgst * 100}%", sgst_amount)
            ]
            rate_summary = f"CGST {self.cgst * 100}% + SGST {self.sgst * 100}%"
        else:
            total_tax = taxable * self.igst
            components = [
                (f"IGST {self.igst * 100}%", total_tax)
            ]
            rate_summary = f"IGST {self.igst * 100}%"

        return TaxBreakdown(
            total=total_tax,
            components=components,
            rate_summary=rate_summary
        )