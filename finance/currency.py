from decimal import Decimal


class CurrencyConverter:
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
