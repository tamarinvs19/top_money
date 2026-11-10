from decimal import Decimal
from typing import Optional


class CurrencyConverter:
    BASE_CURRENCY = 'RUB'

    RATES = {
        ('RUB', 'USD'): Decimal('0.011'),
        ('USD', 'RUB'): Decimal('90.0'),
        ('RUB', 'EUR'): Decimal('0.010'),
        ('EUR', 'RUB'): Decimal('100.0'),
        ('USD', 'EUR'): Decimal('0.92'),
        ('EUR', 'USD'): Decimal('1.09'),
    }

    @classmethod
    def convert(cls, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        if from_currency == to_currency:
            return amount

        rate = cls.RATES.get((from_currency, to_currency))
        if rate is None:
            raise ValueError(f"Conversion rate from {from_currency} to {to_currency} not available")
        
        return amount * rate

    @classmethod
    def to_base(cls, amount: Decimal, from_currency: str, asset_rate: Optional[Decimal] = None) -> Decimal:
        """Convert an amount to RUB using a transaction asset rate when available.

        Asset rates store how many transaction-currency units equal one
        asset-currency unit, so the amount is divided by the rate.
        """
        if from_currency == cls.BASE_CURRENCY:
            return amount

        if asset_rate:
            return amount / asset_rate

        try:
            return cls.convert(amount, from_currency, cls.BASE_CURRENCY)
        except ValueError:
            return amount
