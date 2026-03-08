import requests
from datetime import date
from decimal import Decimal
from typing import Optional

EXCHANGE_RATE_API_URL = "https://api.frankfurter.app"


class ExchangeRateService:
    @classmethod
    def get_rate(cls, from_currency: str, to_currency: str, at_date: Optional[date] = None) -> Decimal:
        if from_currency == to_currency:
            return Decimal('1')

        if at_date is None:
            at_date = date.today()

        try:
            response = requests.get(
                f"{EXCHANGE_RATE_API_URL}/{at_date}",
                params={"from": from_currency, "to": to_currency},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                rate = data.get("rates", {}).get(to_currency)
                if rate:
                    return Decimal(str(rate))
        except Exception:
            pass

        return Decimal('1')

    @classmethod
    def get_rates_for_date(cls, base_currency: str, target_currencies: list[str], at_date: Optional[date] = None) -> dict[str, Decimal]:
        if at_date is None:
            at_date = date.today()

        if base_currency in target_currencies:
            target_currencies = [c for c in target_currencies if c != base_currency]
            if not target_currencies:
                return {base_currency: Decimal('1')}

        try:
            response = requests.get(
                f"{EXCHANGE_RATE_API_URL}/{at_date}",
                params={"from": base_currency, "to": ",".join(target_currencies)},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                result = {base_currency: Decimal('1')}
                for currency, rate in rates.items():
                    result[currency] = Decimal(str(rate))
                return result
        except Exception:
            pass

        return {currency: Decimal('1') for currency in target_currencies}
