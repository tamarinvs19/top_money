import uuid
from decimal import Decimal

from django.db import models
from model_utils.managers import InheritanceManager
from django.contrib.auth.models import User
from django.utils import timezone


class Bank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='banks/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


BANKS = [
    ('Sberbank', 'sberbank.png'),
    ('T-Bank', 'tbank.png'),
    ('Alfa-Bank', 'alfa.png'),
    ('VTB', 'vtb.png'),
    ('Gazprombank', 'gazprombank.png'),
    ('Rosselkhozbank', 'rosselkhozbank.png'),
    ('Otkritie', 'otkritie.png'),
    ('Raiffeisenbank', 'raiffeisen.png'),
    ('MKB', 'mkb.png'),
    ('UniCredit Bank', 'unicredit.png'),
    ('PSBank', 'psbank.png'),
    ('Russian Standard Bank', 'russianstandard.png'),
    ('MTS Bank', 'mts.png'),
    ('BIN', 'bin.png'),
    ('Ozon Bank', 'ozon.png'),
    ('Yandex Bank', 'yandex.png'),
    ('BCS Bank', 'bcs.png'),
    ('DOM.RF Bank', 'domrf.png'),
    ('Svoi Bank', 'svoi.png'),
]


class Provider(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='providers/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


PROVIDERS = [
    ('Qiwi', 'qiwi.png'),
    ('WebMoney', 'webmoney.png'),
    ('Finuslugi', 'finuslugi.png'),
    ('Alibaba', 'alibaba.png'),
]


class AssetType(models.TextChoices):
    CASH = 'CASH', 'Cash'
    DEBIT_CARD = 'DEBIT_CARD', 'Debit Card'
    CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
    DEPOSIT = 'DEPOSIT', 'Deposit'
    SAVING_ACCOUNT = 'SAVING_ACCOUNT', 'Saving Account'
    E_WALLET = 'E_WALLET', 'E-Wallet'
    BROKERAGE = 'BROKERAGE', 'Brokerage Account'


def get_asset_type_label(name: str):
    return dict(AssetType.choices).get(name, "")


class BrokerageAccountType(models.TextChoices):
    BROKERAGE = 'BROKERAGE', 'Brokerage'
    IIS = 'IIS', 'Individual Investment Account'
    IRA = 'IRA', 'Individual Retirement Account'


class TransactionType(models.TextChoices):
    WASTE = 'WASTE', 'Waste'
    TRANSFER = 'TRANSFER', 'Transfer'
    REFILL = 'REFILL', 'Refill'
    CHANGING_BALANCE = 'CHANGING_BALANCE', 'Changing Balance'


class CommissionType(models.TextChoices):
    PERCENT = 'PERCENT', 'Percent'
    ABSOLUTE = 'ABSOLUTE', 'Absolute'


def get_transaction_type_label(name: str):
    return dict(TransactionType.choices).get(name, "")


class WasteCategory(models.TextChoices):
    PRODUCTS = 'PRODUCTS', 'Products'
    CAFE_AND_RESTAURANTS = 'CAFE_AND_RESTAURANTS', 'Cafe and restaurants'
    TRANSPORT = 'TRANSPORT', 'Transport'
    HCS = 'HCS', 'HCS'
    HOUSEHOLD = 'HOUSEHOLD', 'Household'
    PERSONAL = 'PERSONAL', 'Personal'
    LEISURE = 'LEISURE', 'Leisure'
    ENTERTAINMENT = 'ENTERTAINMENT', 'Entertainment'
    CLOTHING_AND_SHOES = 'CLOTHING_AND_SHOES', 'Clothing and shoes'
    SPORT = 'SPORT', 'Sport'
    HEALTH_AND_BEAUTY = 'HEALTH_AND_BEAUTY', 'Health and beauty'
    SUBSCRIPTIONS = 'SUBSCRIPTIONS', 'Subscriptions'
    TAXES_AND_PENALTIES = 'TAXES_AND_PENALTIES', 'Taxes and penalties'
    LEARNING = 'LEARNING', 'Learning'
    GIFTS = 'GIFTS', 'Gifts'
    TECHNIQUE = 'TECHNIQUE', 'Technique'
    TRAVELING = 'TRAVELING', 'Traveling'
    REALTY = 'REALTY', 'Realty'
    OTHER = 'OTHER_WASTE', 'Other waste'


class RefillCategory(models.TextChoices):
    SALARY = 'SALARY', 'Salary'
    BONUS = 'BONUS', 'Bonus'
    CASHBACK = 'CASHBACK', 'Cashback'
    INTEREST = 'INTEREST', 'Interest'
    SALE = 'SALE', 'Sale'
    INVESTMENT = 'INVESTMENT', 'Investment'
    OTHER = 'OTHER_REFILL', 'Other refill'


class Asset(models.Model):
    objects = InheritanceManager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_assets')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=AssetType.choices)
    currency = models.CharField(max_length=3, default='RUB')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()}: {self.name}"

    @property
    def balance(self):
        return self.calculate_balance()

    def calculate_balance(self, at_time=None):
        if at_time is None:
            at_time = timezone.now()

        incoming = list(self.incoming_transactions.filter(
            date__lte=at_time
        ).select_related('to_asset'))
        outgoing = list(self.outgoing_transactions.filter(
            date__lte=at_time
        ).select_related('from_asset'))

        total_in = Decimal('0')
        total_out = Decimal('0')

        for t in incoming:
            if t.to_asset and t.to_asset.currency != t.currency and t.to_asset_rate and t.to_asset_rate != 0:
                amount = t.amount / t.to_asset_rate
            else:
                amount = t.amount
            total_in += amount

        for t in outgoing:
            if t.from_asset and t.from_asset.currency != t.currency and t.from_asset_rate and t.from_asset_rate != 0:
                amount = t.amount / t.from_asset_rate
            else:
                amount = t.amount
            if t.commission_rate and t.commission_rate != 0:
                if t.commission_type == CommissionType.ABSOLUTE:
                    commission = t.commission_rate
                else:
                    commission = amount * t.commission_rate / Decimal('100')
            else:
                commission = Decimal('0')
            total_out += amount + commission

        return total_in - total_out


class CashAsset(Asset):
    location = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Cash'
        verbose_name_plural = 'Cash'


class BankAsset(Asset):
    bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, blank=True, null=True, related_name='%(class)s_assets')

    class Meta:
        abstract = True

    @property
    def bank_name(self):
        return self.bank.name if self.bank else ''


class CardAsset(BankAsset):
    last_4_digits = models.CharField(max_length=4, blank=True)

    class Meta:
        abstract = True


class DebitCardAsset(CardAsset):

    class Meta:
        verbose_name = 'Debit Card'
        verbose_name_plural = 'Debit Cards'


class BankInvestment(BankAsset):
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        abstract = True


class DepositAsset(BankInvestment):
    term_months = models.PositiveIntegerField(blank=True, null=True)
    renewal_date = models.DateField(blank=True, null=True)
    is_capitalized = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Deposit'
        verbose_name_plural = 'Deposits'


class SavingAccount(BankInvestment):
    class Meta:
        verbose_name = 'Saving Account'
        verbose_name_plural = 'Saving Accounts'


class CreditCardAsset(CardAsset):
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    grace_period_days = models.PositiveIntegerField(blank=True, null=True)
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


class EWalletAsset(Asset):
    provider_name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'E-Wallet'
        verbose_name_plural = 'E-Wallets'


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='RUB')
    from_asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='outgoing_transactions',
        blank=True,
        null=True
    )
    from_asset_rate = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('1'))
    to_asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='incoming_transactions',
        blank=True,
        null=True
    )
    to_asset_rate = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('1'))
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0'))
    commission_type = models.CharField(
        max_length=10,
        choices=CommissionType.choices,
        default=CommissionType.PERCENT
    )
    category = models.CharField(max_length=30, choices=WasteCategory.choices + RefillCategory.choices, blank=True)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} {self.currency}"
    
    def type_label(self):
        return get_transaction_type_label(self.type)

    @property
    def commission_amount(self) -> Decimal:
        if self.commission_rate is None or self.commission_rate == 0:
            return Decimal('0')
        if self.commission_type == CommissionType.ABSOLUTE:
            return self.commission_rate
        return self.amount * self.commission_rate / Decimal('100')


class InvitationCode(models.Model):
    code = models.CharField(max_length=32, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    used_by = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_invitation')
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = 'used' if self.used_by else 'available'
        return f"{self.code} ({status})"

    @property
    def is_used(self):
        return self.used_by is not None

    @classmethod
    def generate_code(cls, created_by):
        import secrets
        code = secrets.token_urlsafe(16)
        return cls.objects.create(code=code, created_by=created_by)
