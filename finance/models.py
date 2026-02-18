import uuid
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from finance.currency import CurrencyConverter


class AssetType(models.TextChoices):
    CASH = 'CASH', 'Cash'
    BANK_CARD = 'BANK_CARD', 'Bank Card'
    DEPOSIT = 'DEPOSIT', 'Deposit'
    CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
    BROKERAGE = 'BROKERAGE', 'Brokerage Account'


class BrokerageAccountType(models.TextChoices):
    BROKERAGE = 'BROKERAGE', 'Brokerage'
    IIS = 'IIS', 'Individual Investment Account'
    IRA = 'IRA', 'Individual Retirement Account'


class TransactionType(models.TextChoices):
    REFILL = 'REFILL', 'Refill'
    WASTE = 'WASTE', 'Waste'
    TRANSFER = 'TRANSFER', 'Transfer'


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_assets')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=AssetType.choices)
    currency = models.CharField(max_length=3, default='RUB')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_balance_calc_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def calculate_balance(self, at_time=None):
        if at_time is None:
            at_time = timezone.now()

        start_time = self.last_balance_calc_at if self.last_balance_calc_at else self.created_at

        incoming = self.incoming_transactions.filter(
            date__gte=start_time,
            date__lte=at_time
        )
        outgoing = self.outgoing_transactions.filter(
            date__gte=start_time,
            date__lte=at_time
        )

        total_in = Decimal('0')
        total_out = Decimal('0')

        for t in incoming:
            amount = t.amount
            if t.currency != self.currency:
                amount = CurrencyConverter.convert(amount, t.currency, self.currency)
            total_in += amount

        for t in outgoing:
            amount = t.amount
            if t.currency != self.currency:
                amount = CurrencyConverter.convert(amount, t.currency, self.currency)
            total_out += amount

        return self.balance + total_in - total_out

    def update_balance(self, at_time=None):
        if at_time is None:
            at_time = timezone.now()
        
        new_balance = self.calculate_balance(at_time)
        self.balance = new_balance
        self.last_balance_calc_at = at_time
        self.save()
        return self.balance


class CashAsset(Asset):
    location = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Cash'
        verbose_name_plural = 'Cash'


class BankCardAsset(Asset):
    bank_name = models.CharField(max_length=100, blank=True)
    last_4_digits = models.CharField(max_length=4, blank=True)

    class Meta:
        verbose_name = 'Bank Card'
        verbose_name_plural = 'Bank Cards'


class DepositAsset(Asset):
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    term_months = models.PositiveIntegerField(blank=True, null=True)
    renewal_date = models.DateField(blank=True, null=True)
    is_capitalized = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'


class CreditCardAsset(Asset):
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    grace_period_days = models.PositiveIntegerField(blank=True, null=True)
    last_4_digits = models.CharField(max_length=4, blank=True)
    billing_day = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Credit Card'
        verbose_name_plural = 'Credit Cards'


class BrokerageAsset(Asset):
    broker_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    brokerage_account_type = models.CharField(
        max_length=20,
        choices=BrokerageAccountType.choices,
        blank=True
    )

    class Meta:
        verbose_name = 'Brokerage Account'
        verbose_name_plural = 'Brokerage Accounts'


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='RUB')
    from_asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='outgoing_transactions',
        blank=True,
        null=True
    )
    to_asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='incoming_transactions',
        blank=True,
        null=True
    )
    category = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} {self.currency}"
