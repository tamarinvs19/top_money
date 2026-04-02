from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import make_aware
from decimal import Decimal
from datetime import datetime

from finance.models import (
    Asset, CashAsset, DebitCardAsset, DepositAsset, 
    CreditCardAsset, BrokerageAsset, EWalletAsset, Transaction, 
    AssetType, TransactionType, WasteCategory, RefillCategory, BrokerageAccountType,
    BankAsset, BankInvestment, SavingAccount, InvitationCode, Bank, CommissionType,
    Provider
)
from finance.exchange_rate import ExchangeRateService


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))


class AssetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_cash_asset(self):
        asset = CashAsset.objects.create(
            user=self.user,
            name='Wallet Cash',
            type=AssetType.CASH,
            currency='RUB',
            location='Wallet'
        )
        self.assertEqual(asset.name, 'Wallet Cash')
        self.assertEqual(asset.type, AssetType.CASH)
        self.assertEqual(asset.location, 'Wallet')
        self.assertTrue(asset.is_active)
        self.assertEqual(asset.balance, Decimal('0'))

    def test_create_cash_asset_with_initial_balance(self):
        asset = CashAsset.objects.create(
            user=self.user,
            name='Wallet Cash',
            type=AssetType.CASH,
            currency='RUB',
            location='Wallet'
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=asset,
            date=timezone.now()
        )
        self.assertEqual(asset.balance, Decimal('5000.00'))

    def test_create_bank_card_asset(self):
        bank = Bank.objects.create(name='Sberbank')
        asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
            bank=bank,
            last_4_digits='1234'
        )
        self.assertEqual(asset.bank_name, 'Sberbank')
        self.assertEqual(asset.last_4_digits, '1234')

    def test_create_deposit_asset(self):
        asset = DepositAsset.objects.create(
            user=self.user,
            name='Savings Deposit',
            type=AssetType.DEPOSIT,
            currency='RUB',
            interest_rate=Decimal('4.5'),
            term_months=12,
            renewal_date='2027-01-01',
            is_capitalized=True
        )
        self.assertEqual(asset.interest_rate, Decimal('4.5'))
        self.assertEqual(asset.term_months, 12)

    def test_create_credit_card_asset(self):
        asset = CreditCardAsset.objects.create(
            user=self.user,
            name='Credit Card',
            type=AssetType.CREDIT_CARD,
            currency='RUB',
            credit_limit=Decimal('100000.00'),
            grace_period_days=25,
            last_4_digits='5678',
            billing_day=1
        )
        self.assertEqual(asset.credit_limit, Decimal('100000.00'))
        self.assertEqual(asset.balance, Decimal('0'))

    def test_create_brokerage_asset(self):
        asset = BrokerageAsset.objects.create(
            user=self.user,
            name='Tinkoff Invest',
            type=AssetType.BROKERAGE,
            currency='RUB',
            broker_name='Tinkoff',
            account_number='123456789',
            brokerage_account_type=BrokerageAccountType.BROKERAGE
        )
        self.assertEqual(asset.broker_name, 'Tinkoff')
        self.assertEqual(asset.brokerage_account_type, BrokerageAccountType.BROKERAGE)

    def test_user_asset_relation(self):
        CashAsset.objects.create(
            user=self.user,
            name='Cash',
            type=AssetType.CASH,
        )
        DebitCardAsset.objects.create(
            user=self.user,
            name='Card',
            type=AssetType.DEBIT_CARD,
        )
        self.assertEqual(CashAsset.objects.filter(user=self.user).count(), 1)
        self.assertEqual(DebitCardAsset.objects.filter(user=self.user).count(), 1)

    def test_asset_str_representation(self):
        asset = CashAsset.objects.create(
            user=self.user,
            name='Test Cash',
            type=AssetType.CASH,
        )
        self.assertEqual(str(asset), 'Cash: Test Cash')


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def test_create_refill_transaction(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            category='Salary',
            date=timezone.now()
        )
        self.assertEqual(transaction.type, TransactionType.REFILL)
        self.assertEqual(transaction.to_asset, self.asset)
        self.assertIsNone(transaction.from_asset)

    def test_create_waste_transaction(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('1500.00'),
            currency='RUB',
            from_asset=self.asset,
            category='Food',
            date=timezone.now()
        )
        self.assertEqual(transaction.type, TransactionType.WASTE)
        self.assertEqual(transaction.from_asset, self.asset)
        self.assertIsNone(transaction.to_asset)

    def test_create_transfer_transaction(self):
        to_asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Tinkoff Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.TRANSFER,
            amount=Decimal('3000.00'),
            currency='RUB',
            from_asset=self.asset,
            to_asset=to_asset,
            category='Transfer',
            date=timezone.now()
        )
        self.assertEqual(transaction.type, TransactionType.TRANSFER)
        self.assertEqual(transaction.from_asset, self.asset)
        self.assertEqual(transaction.to_asset, to_asset)

    def test_transaction_str_representation(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        self.assertIn('1000.00', str(transaction))
        self.assertIn('RUB', str(transaction))

    def test_user_transaction_relation(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            to_asset=self.asset,
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('500.00'),
            from_asset=self.asset,
            date=timezone.now()
        )
        self.assertEqual(self.user.transactions.count(), 2)

    def test_asset_incoming_transactions(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('5000.00'),
            to_asset=self.asset,
            date=timezone.now()
        )
        self.assertEqual(self.asset.incoming_transactions.count(), 1)

    def test_asset_outgoing_transactions(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('1000.00'),
            from_asset=self.asset,
            date=timezone.now()
        )
        self.assertEqual(self.asset.outgoing_transactions.count(), 1)


class ExchangeRateServiceTest(TestCase):
    def test_same_currency_returns_one(self):
        result = ExchangeRateService.get_rate('RUB', 'RUB')
        self.assertEqual(result, Decimal('1'))

    def test_same_currency_with_date(self):
        from datetime import date
        result = ExchangeRateService.get_rate('RUB', 'RUB', date(2025, 1, 1))
        self.assertEqual(result, Decimal('1'))


class TransactionExchangeRateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.asset_rub = DebitCardAsset.objects.create(
            user=self.user,
            name='RUB Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )
        self.asset_usd = DebitCardAsset.objects.create(
            user=self.user,
            name='USD Card',
            type=AssetType.DEBIT_CARD,
            currency='USD',
        )
        self.asset_eur = DebitCardAsset.objects.create(
            user=self.user,
            name='EUR Card',
            type=AssetType.DEBIT_CARD,
            currency='EUR',
        )

    def test_transaction_with_default_rate(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset_rub,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        self.assertEqual(transaction.to_asset_rate, Decimal('1'))

    def test_transaction_with_custom_from_asset_rate(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='USD',
            from_asset=self.asset_usd,
            from_asset_rate=Decimal('95.5'),
            date=timezone.now()
        )
        self.assertEqual(transaction.from_asset_rate, Decimal('95.5'))

    def test_transaction_with_custom_to_asset_rate(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='EUR',
            to_asset=self.asset_eur,
            to_asset_rate=Decimal('88.5'),
            date=timezone.now()
        )
        self.assertEqual(transaction.to_asset_rate, Decimal('88.5'))

    def test_transfer_with_different_currencies(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.TRANSFER,
            amount=Decimal('100.00'),
            currency='USD',
            from_asset=self.asset_usd,
            from_asset_rate=Decimal('90.0'),
            to_asset=self.asset_rub,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        self.assertEqual(transaction.from_asset_rate, Decimal('90.0'))
        self.assertEqual(transaction.to_asset_rate, Decimal('1'))


class AssetBalanceWithExchangeRateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.asset_rub = DebitCardAsset.objects.create(
            user=self.user,
            name='RUB Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def test_refill_with_same_currency_uses_rate_one(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset_rub,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        self.assertEqual(self.asset_rub.balance, Decimal('1000.00'))

    def test_refill_with_custom_rate_applies_division(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('100.00'),
            currency='USD',
            to_asset=self.asset_rub,
            to_asset_rate=Decimal('0.011'),
            date=timezone.now()
        )
        self.assertAlmostEqual(float(self.asset_rub.balance), 9090.91, places=2)

    def test_waste_with_custom_rate_applies_division(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=self.asset_rub,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('50.00'),
            currency='USD',
            from_asset=self.asset_rub,
            from_asset_rate=Decimal('0.011'),
            date=timezone.now()
        )
        self.assertAlmostEqual(float(self.asset_rub.balance), 5454.55, places=2)

    def test_transfer_between_different_currencies(self):
        asset_usd = DebitCardAsset.objects.create(
            user=self.user,
            name='USD Card',
            type=AssetType.DEBIT_CARD,
            currency='USD',
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=self.asset_rub,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.TRANSFER,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset_rub,
            from_asset_rate=Decimal('1'),
            to_asset=asset_usd,
            to_asset_rate=Decimal('0.011'),
            date=timezone.now()
        )
        self.assertAlmostEqual(float(self.asset_rub.balance), 9900.00, places=2)
        self.assertAlmostEqual(float(asset_usd.balance), 9090.91, places=2)

    def test_transfer_rub_to_yuan_with_exchange_rate(self):
        asset_cny = DebitCardAsset.objects.create(
            user=self.user,
            name='CNY Card',
            type=AssetType.DEBIT_CARD,
            currency='CNY',
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('1200.00'),
            currency='RUB',
            to_asset=self.asset_rub,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('100.00'),
            currency='CNY',
            to_asset=asset_cny,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.TRANSFER,
            amount=Decimal('1200.00'),
            currency='RUB',
            from_asset=self.asset_rub,
            from_asset_rate=Decimal('12'),
            to_asset=asset_cny,
            to_asset_rate=Decimal('12'),
            date=timezone.now()
        )
        self.assertAlmostEqual(float(self.asset_rub.balance), 0.00, places=2)
        self.assertAlmostEqual(float(asset_cny.balance), 200.00, places=2)


class AssetBalanceCalculationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def _set_initial_balance(self, amount):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=amount,
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )

    def test_balance_with_only_refill(self):
        self._set_initial_balance(Decimal('10000.00'))
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('15000.00'))

    def test_balance_with_only_waste(self):
        self._set_initial_balance(Decimal('10000.00'))
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('3000.00'),
            currency='RUB',
            from_asset=self.asset,
            date=timezone.now()
        )
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('7000.00'))

    def test_balance_with_refill_and_waste(self):
        self._set_initial_balance(Decimal('10000.00'))
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('3000.00'),
            currency='RUB',
            from_asset=self.asset,
            date=timezone.now()
        )
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('17000.00'))

    def test_balance_with_currency_conversion(self):
        self._set_initial_balance(Decimal('10000.00'))
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='USD',
            to_asset=self.asset,
            to_asset_rate=Decimal('0.01'),
            date=timezone.now()
        )
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('110000.00'))

    def test_balance_empty_asset(self):
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('0'))

    def test_balance_at_specific_time(self):
        from datetime import timedelta
        now = timezone.now()
        past = now - timedelta(days=2)
        future = now + timedelta(days=1)

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=past
        )

        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=past
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('2000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=future
        )

        balance_at_past = self.asset.calculate_balance(at_time=past)
        self.assertEqual(balance_at_past, Decimal('11000.00'))

        balance_at_now = self.asset.calculate_balance(at_time=now)
        self.assertEqual(balance_at_now, Decimal('11000.00'))

        balance_at_future = self.asset.calculate_balance(at_time=future)
        self.assertEqual(balance_at_future, Decimal('13000.00'))

    def test_balance_with_transfer(self):
        to_asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Tinkoff Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )
        self._set_initial_balance(Decimal('10000.00'))
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.TRANSFER,
            amount=Decimal('5000.00'),
            currency='RUB',
            from_asset=self.asset,
            to_asset=to_asset,
            date=timezone.now()
        )
        calculated_from = self.asset.calculate_balance()
        self.assertEqual(calculated_from, Decimal('5000.00'))

    def test_balance_ignores_other_assets(self):
        other_asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Other Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )
        self._set_initial_balance(Decimal('10000.00'))
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=other_asset,
            date=timezone.now()
        )
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('10000.00'))

    def test_balance_counts_all_transactions(self):
        from datetime import timedelta
        now = timezone.now()
        
        self._set_initial_balance(Decimal('10000.00'))
        
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('5000.00'),
            currency='RUB',
            from_asset=self.asset,
            date=now - timedelta(days=3)
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('3000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=now - timedelta(days=2)
        )

        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('8000.00'))


class AssetChangingBalanceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def test_balance_property_returns_calculated_balance(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('15000.00'))

    def test_changing_balance_transaction_increases_balance(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('5000.00'))

    def test_changing_balance_transaction_decreases_balance(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('3000.00'),
            currency='RUB',
            from_asset=self.asset,
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('-3000.00'))

    def test_changing_balance_excluded_from_summary(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('2000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        non_changing = Transaction.objects.filter(
            user=self.user
        ).exclude(type=TransactionType.CHANGING_BALANCE)
        self.assertEqual(non_changing.count(), 1)

    def test_balance_calculation_includes_changing_balance_transactions(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('2000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=timezone.now()
        )
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('7000.00'))


class TransactionCategoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def test_create_waste_transaction_with_category(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('500.00'),
            currency='RUB',
            from_asset=self.asset,
            category=WasteCategory.PRODUCTS,
            date=timezone.now()
        )
        self.assertEqual(transaction.category, WasteCategory.PRODUCTS)
        self.assertEqual(transaction.get_category_display(), 'Products')

    def test_create_waste_transaction_with_all_categories(self):
        categories = [
            WasteCategory.PRODUCTS,
            WasteCategory.CAFE_AND_RESTAURANTS,
            WasteCategory.TRANSPORT,
            WasteCategory.HCS,
            WasteCategory.LEISURE,
            WasteCategory.CLOTHING_AND_SHOES,
            WasteCategory.SPORT,
            WasteCategory.HEALTH_AND_BEAUTY,
            WasteCategory.SUBSCRIPTIONS,
            WasteCategory.TAXES_AND_PENALTIES,
            WasteCategory.LEARNING,
            WasteCategory.GIFTS,
            WasteCategory.TECHNIQUE,
            WasteCategory.TRAVELING,
            WasteCategory.REALTY,
            WasteCategory.OTHER,
        ]
        for category in categories:
            transaction = Transaction.objects.create(
                user=self.user,
                type=TransactionType.WASTE,
                amount=Decimal('100.00'),
                currency='RUB',
                from_asset=self.asset,
                category=category,
                date=timezone.now()
            )
            self.assertEqual(transaction.category, category)

    def test_create_refill_transaction_with_category(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            category=RefillCategory.SALARY,
            date=timezone.now()
        )
        self.assertEqual(transaction.category, RefillCategory.SALARY)
        self.assertEqual(transaction.get_category_display(), 'Salary')

    def test_create_refill_transaction_with_all_categories(self):
        categories = [
            RefillCategory.SALARY,
            RefillCategory.BONUS,
            RefillCategory.CASHBACK,
            RefillCategory.SALE,
            RefillCategory.INVESTMENT,
            RefillCategory.OTHER,
        ]
        for category in categories:
            transaction = Transaction.objects.create(
                user=self.user,
                type=TransactionType.REFILL,
                amount=Decimal('1000.00'),
                currency='RUB',
                to_asset=self.asset,
                category=category,
                date=timezone.now()
            )
            self.assertEqual(transaction.category, category)

    def test_transaction_without_category(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            date=timezone.now()
        )
        self.assertEqual(transaction.category, '')

    def test_waste_category_display(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('200.00'),
            currency='RUB',
            from_asset=self.asset,
            category=WasteCategory.CAFE_AND_RESTAURANTS,
            date=timezone.now()
        )
        self.assertEqual(transaction.get_category_display(), 'Cafe and restaurants')

    def test_refill_category_display(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('3000.00'),
            currency='RUB',
            to_asset=self.asset,
            category=RefillCategory.CASHBACK,
            date=timezone.now()
        )
        self.assertEqual(transaction.get_category_display(), 'Cashback')


class TransactionDateTimeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def test_transaction_datetime_stores_time(self):
        from datetime import datetime
        from django.utils.timezone import make_aware
        test_time = datetime(2026, 2, 21, 15, 30, 0)
        test_datetime = make_aware(test_time)
        
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('500.00'),
            currency='RUB',
            from_asset=self.asset,
            date=test_datetime
        )
        
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.date)
        self.assertEqual(transaction.date.minute, 30)

    def test_transaction_datetime_with_different_minutes(self):
        
        minutes = [0, 15, 30, 45, 59]
        
        for minute in minutes:
            test_time = datetime(2026, 2, 21, 15, minute, 0)
            test_datetime = make_aware(test_time)
            
            transaction = Transaction.objects.create(
                user=self.user,
                type=TransactionType.REFILL,
                amount=Decimal('100.00'),
                currency='RUB',
                to_asset=self.asset,
                date=test_datetime
            )
            
            transaction.refresh_from_db()
            self.assertEqual(transaction.date.minute, minute, f"Minute mismatch for minute {minute}")


class BankAssetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_card_asset_inherits_bank_name(self):
        bank = Bank.objects.create(name='Sberbank')
        asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            bank=bank,
            last_4_digits='1234'
        )
        self.assertEqual(asset.bank_name, 'Sberbank')
        self.assertIsInstance(asset, BankAsset)

    def test_credit_card_inherits_bank_name(self):
        bank = Bank.objects.create(name='Tinkoff')
        asset = CreditCardAsset.objects.create(
            user=self.user,
            name='Tinkoff Credit',
            type=AssetType.CREDIT_CARD,
            bank=bank,
            credit_limit=Decimal('100000.00')
        )
        self.assertEqual(asset.bank_name, 'Tinkoff')
        self.assertIsInstance(asset, BankAsset)

    def test_bank_asset_is_abstract(self):
        self.assertTrue(BankAsset._meta.abstract)


class BankInvestmentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_deposit_asset_inherits_interest_rate(self):
        asset = DepositAsset.objects.create(
            user=self.user,
            name='Savings Deposit',
            type=AssetType.DEPOSIT,
            interest_rate=Decimal('4.5')
        )
        self.assertEqual(asset.interest_rate, Decimal('4.5'))
        self.assertIsInstance(asset, BankInvestment)

    def test_bank_investment_is_abstract(self):
        self.assertTrue(BankInvestment._meta.abstract)


class SavingAccountTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_create_saving_account(self):
        asset = SavingAccount.objects.create(
            user=self.user,
            name='Emergency Fund',
            type=AssetType.SAVING_ACCOUNT,
            interest_rate=Decimal('5.5'),
            currency='RUB'
        )
        self.assertEqual(asset.name, 'Emergency Fund')
        self.assertEqual(asset.interest_rate, Decimal('5.5'))
        self.assertEqual(asset.type, AssetType.SAVING_ACCOUNT)
        self.assertIsInstance(asset, BankInvestment)

    def test_saving_account_inherits_from_asset(self):
        asset = SavingAccount.objects.create(
            user=self.user,
            name='Savings',
            type=AssetType.SAVING_ACCOUNT
        )
        self.assertIsInstance(asset, Asset)
        self.assertIsInstance(asset, BankInvestment)

    def test_saving_account_has_interest_rate(self):
        asset = SavingAccount.objects.create(
            user=self.user,
            name='Test Savings',
            type=AssetType.SAVING_ACCOUNT,
            interest_rate=Decimal('3.25')
        )
        self.assertEqual(asset.interest_rate, Decimal('3.25'))

    def test_saving_account_balance_from_transactions(self):
        asset = SavingAccount.objects.create(
            user=self.user,
            name='Test Savings',
            type=AssetType.SAVING_ACCOUNT,
            interest_rate=Decimal('3.0')
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=asset,
            date=timezone.now()
        )
        self.assertEqual(asset.balance, Decimal('10000.00'))


class EWalletAssetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.provider = Provider.objects.create(name='Yandex')

    def test_create_e_wallet_asset(self):
        asset = EWalletAsset.objects.create(
            user=self.user,
            name='Yandex Money',
            type=AssetType.E_WALLET,
            currency='RUB',
            provider=self.provider
        )
        self.assertEqual(asset.name, 'Yandex Money')
        self.assertEqual(asset.type, AssetType.E_WALLET)
        self.assertEqual(asset.provider_name, 'Yandex')
        self.assertTrue(asset.is_active)
        self.assertEqual(asset.balance, Decimal('0'))

    def test_e_wallet_inherits_from_asset(self):
        asset = EWalletAsset.objects.create(
            user=self.user,
            name='Qiwi Wallet',
            type=AssetType.E_WALLET,
        )
        self.assertIsInstance(asset, Asset)

    def test_e_wallet_with_initial_balance(self):
        provider = Provider.objects.create(name='Webmoney')
        asset = EWalletAsset.objects.create(
            user=self.user,
            name='Webmoney',
            type=AssetType.E_WALLET,
            currency='RUB',
            provider=provider
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=asset,
            date=timezone.now()
        )
        self.assertEqual(asset.balance, Decimal('10000.00'))

    def test_e_wallet_str_representation(self):
        asset = EWalletAsset.objects.create(
            user=self.user,
            name='Test Wallet',
            type=AssetType.E_WALLET,
        )
        self.assertEqual(str(asset), 'E-Wallet: Test Wallet')

    def test_e_wallet_transactions(self):
        asset = EWalletAsset.objects.create(
            user=self.user,
            name='Test Wallet',
            type=AssetType.E_WALLET,
            currency='RUB'
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=asset,
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('2000.00'),
            currency='RUB',
            from_asset=asset,
            date=timezone.now()
        )
        self.assertEqual(asset.incoming_transactions.count(), 1)
        self.assertEqual(asset.outgoing_transactions.count(), 1)
        self.assertEqual(asset.balance, Decimal('3000.00'))

    def test_user_e_wallet_relation(self):
        EWalletAsset.objects.create(
            user=self.user,
            name='Wallet 1',
            type=AssetType.E_WALLET,
        )
        EWalletAsset.objects.create(
            user=self.user,
            name='Wallet 2',
            type=AssetType.E_WALLET,
        )
        self.assertEqual(EWalletAsset.objects.filter(user=self.user).count(), 2)


class TransactionCommissionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def test_transaction_with_default_commission(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('0'),
            date=timezone.now()
        )
        self.assertEqual(transaction.commission_rate, Decimal('0'))

    def test_transaction_with_custom_commission(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('0.02'),
            date=timezone.now()
        )
        self.assertEqual(transaction.commission_rate, Decimal('0.02'))

    def test_transaction_default_commission_type_is_percent(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('0.02'),
            date=timezone.now()
        )
        self.assertEqual(transaction.commission_type, CommissionType.PERCENT)

    def test_transaction_with_absolute_commission_type(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('10.00'),
            commission_type=CommissionType.ABSOLUTE,
            date=timezone.now()
        )
        self.assertEqual(transaction.commission_type, CommissionType.ABSOLUTE)

    def test_commission_amount_for_percent_type(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('5'),
            commission_type=CommissionType.PERCENT,
            date=timezone.now()
        )
        self.assertEqual(transaction.commission_amount, Decimal('5.00'))

    def test_commission_amount_for_absolute_type(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('15.00'),
            commission_type=CommissionType.ABSOLUTE,
            date=timezone.now()
        )
        self.assertEqual(transaction.commission_amount, Decimal('15.00'))

    def test_commission_amount_zero_rate(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('0'),
            commission_type=CommissionType.PERCENT,
            date=timezone.now()
        )
        self.assertEqual(transaction.commission_amount, Decimal('0'))




class AssetBalanceWithCommissionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
        )

    def test_waste_with_no_commission(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('0'),
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('900.00'))

    def test_waste_with_commission_deducted_additionally(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('1'),
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('899.00'))

    def test_transfer_with_commission(self):
        asset_usd = DebitCardAsset.objects.create(
            user=self.user,
            name='USD Card',
            type=AssetType.DEBIT_CARD,
            currency='USD',
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=self.asset,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.TRANSFER,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            from_asset_rate=Decimal('1'),
            to_asset=asset_usd,
            to_asset_rate=Decimal('0.01'),
            commission_rate=Decimal('1'),
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('9899.00'))
        self.assertEqual(asset_usd.balance, Decimal('10000.00'))

    def test_waste_with_absolute_commission_type(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.WASTE,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            commission_rate=Decimal('5.00'),
            commission_type=CommissionType.ABSOLUTE,
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('895.00'))

    def test_transfer_with_absolute_commission(self):
        asset_usd = DebitCardAsset.objects.create(
            user=self.user,
            name='USD Card',
            type=AssetType.DEBIT_CARD,
            currency='USD',
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.CHANGING_BALANCE,
            amount=Decimal('10000.00'),
            currency='RUB',
            to_asset=self.asset,
            to_asset_rate=Decimal('1'),
            date=timezone.now()
        )
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.TRANSFER,
            amount=Decimal('100.00'),
            currency='RUB',
            from_asset=self.asset,
            from_asset_rate=Decimal('1'),
            to_asset=asset_usd,
            to_asset_rate=Decimal('0.01'),
            commission_rate=Decimal('5.00'),
            commission_type=CommissionType.ABSOLUTE,
            date=timezone.now()
        )
        self.assertEqual(self.asset.balance, Decimal('9895.00'))
        self.assertEqual(asset_usd.balance, Decimal('10000.00'))


class InvitationCodeModelTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123'
        )

    def test_generate_invitation_code(self):
        code = InvitationCode.generate_code(self.admin_user)
        self.assertIsNotNone(code.code)
        self.assertEqual(len(code.code), 22)
        self.assertEqual(code.created_by, self.admin_user)
        self.assertFalse(code.is_used)

    def test_invitation_code_unique(self):
        code1 = InvitationCode.generate_code(self.admin_user)
        code2 = InvitationCode.generate_code(self.admin_user)
        self.assertNotEqual(code1.code, code2.code)

    def test_invitation_code_mark_as_used(self):
        code = InvitationCode.generate_code(self.admin_user)
        new_user = User.objects.create_user(username='newuser', password='pass123')
        code.used_by = new_user
        code.used_at = timezone.now()
        code.save()
        self.assertTrue(code.is_used)
        self.assertEqual(code.used_by, new_user)

    def test_invitation_code_str_representation(self):
        code = InvitationCode.generate_code(self.admin_user)
        self.assertIn('available', str(code))
        code.used_by = User.objects.create_user(username='used', password='pass')
        code.save()
        self.assertIn('used', str(code))


class InvitationCodeSignupTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123'
        )
        self.invitation_code = InvitationCode.generate_code(self.admin_user)

    def test_signup_with_valid_invitation_code(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'invitation_code': self.invitation_code.code
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.invitation_code.refresh_from_db()
        self.assertTrue(self.invitation_code.is_used)

    def test_signup_without_invitation_code(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'invitation_code': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_signup_with_invalid_invitation_code(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'invitation_code': 'invalidcode123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_signup_with_used_invitation_code(self):
        user = User.objects.create_user(username='firstuser', password='pass123')
        self.invitation_code.used_by = user
        self.invitation_code.used_at = timezone.now()
        self.invitation_code.save()
        
        response = self.client.post('/signup/', {
            'username': 'seconduser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'invitation_code': self.invitation_code.code
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='seconduser').exists())

    def test_invitation_code_single_use(self):
        self.client.post('/signup/', {
            'username': 'firstuser',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'invitation_code': self.invitation_code.code
        })
        self.invitation_code.refresh_from_db()
        self.assertTrue(self.invitation_code.is_used)
        
        codes = InvitationCode.objects.filter(code=self.invitation_code.code)
        self.assertEqual(codes.count(), 1)


class ProviderModelTest(TestCase):
    def test_create_provider(self):
        provider = Provider.objects.create(name='Qiwi')
        self.assertEqual(provider.name, 'Qiwi')
        self.assertFalse(provider.image)

    def test_provider_str(self):
        provider = Provider.objects.create(name='YooMoney')
        self.assertEqual(str(provider), 'YooMoney')

    def test_provider_unique_name(self):
        Provider.objects.create(name='UniqueProvider')
        with self.assertRaises(Exception):
            Provider.objects.create(name='UniqueProvider')

    def test_provider_ordering(self):
        Provider.objects.create(name='Zebra')
        Provider.objects.create(name='Alpha')
        Provider.objects.create(name='Beta')
        providers = list(Provider.objects.all())
        self.assertEqual(providers[0].name, 'Alpha')
        self.assertEqual(providers[1].name, 'Beta')
        self.assertEqual(providers[2].name, 'Zebra')


class BankCashbackModelTest(TestCase):
    def setUp(self):
        self.bank = Bank.objects.create(name='Sberbank', cashback_categories_limit=5)

    def test_create_bank_with_cashback_limit(self):
        self.assertEqual(self.bank.cashback_categories_limit, 5)

    def test_create_bank_default_cashback_limit(self):
        bank = Bank.objects.create(name='Tinkoff')
        self.assertEqual(bank.cashback_categories_limit, 3)

    def test_create_cashback_category(self):
        from finance.models import BankCashbackCategory, CashbackCategory
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0'),
            limit=Decimal('3000.00')
        )
        self.assertEqual(category.percent, Decimal('5.0'))
        self.assertEqual(category.limit, Decimal('3000.00'))

    def test_create_cashback_month(self):
        from finance.models import BankCashbackMonth
        cashback_month = BankCashbackMonth.objects.create(
            bank=self.bank,
            year=2026,
            month=3,
            common_limit=Decimal('10000.00'),
            max_categories=4
        )
        self.assertEqual(cashback_month.year, 2026)
        self.assertEqual(cashback_month.month, 3)
        self.assertEqual(cashback_month.common_limit, Decimal('10000.00'))
        self.assertEqual(cashback_month.get_max_categories(), 4)

    def test_cashback_month_defaults_to_bank_limit(self):
        from finance.models import BankCashbackMonth
        cashback_month = BankCashbackMonth.objects.create(
            bank=self.bank,
            year=2026,
            month=3
        )
        self.assertIsNone(cashback_month.max_categories)
        self.assertEqual(cashback_month.get_max_categories(), 5)

    def test_cashback_selection(self):
        from finance.models import BankCashbackCategory, BankCashbackMonth, BankCashbackSelection, CashbackCategory
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        cashback_month = BankCashbackMonth.objects.create(
            bank=self.bank,
            year=2026,
            month=3
        )
        selection = BankCashbackSelection.objects.create(
            bank_cashback_month=cashback_month,
            bank_cashback_category=category,
            is_selected=True
        )
        self.assertTrue(selection.is_selected)

    def test_unique_cashback_category_per_bank(self):
        from finance.models import BankCashbackCategory, CashbackCategory
        cashback_cat = CashbackCategory.objects.create(name='Products')
        BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        with self.assertRaises(Exception):
            BankCashbackCategory.objects.create(
                bank=self.bank,
                category=cashback_cat,
                percent=Decimal('3.0')
            )

    def test_unique_cashback_month_per_bank(self):
        from finance.models import BankCashbackMonth
        BankCashbackMonth.objects.create(
            bank=self.bank,
            year=2026,
            month=3
        )
        with self.assertRaises(Exception):
            BankCashbackMonth.objects.create(
                bank=self.bank,
                year=2026,
                month=3
            )

    def test_cashback_category_str(self):
        from finance.models import BankCashbackCategory, CashbackCategory
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        self.assertIn('Sberbank', str(category))
        self.assertIn('Products', str(category))


class BankCashbackViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bank = Bank.objects.create(name='Sberbank', cashback_categories_limit=3)
        self.client.force_login(self.user)

    def test_bank_view_shows_empty_cashback(self):
        from finance.models import CASHBACK_CATEGORIES
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Show all categories')
        self.assertContains(response, str(self.bank.cashback_categories_limit))

    def test_add_cashback_categories(self):
        from finance.models import CashbackCategory
        today = timezone.now()
        
        # Create some test cashback categories
        CashbackCategory.objects.get_or_create(name='Products')
        CashbackCategory.objects.get_or_create(name='Transport')
        
        response = self.client.get(f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/add/')
        self.assertEqual(response.status_code, 302)
        
        from finance.models import BankCashbackCategory, BankCashbackMonth
        categories = BankCashbackCategory.objects.filter(bank=self.bank)
        self.assertEqual(categories.count(), CashbackCategory.objects.count())
        
        month_obj = BankCashbackMonth.objects.filter(bank=self.bank, year=today.year, month=today.month)
        self.assertTrue(month_obj.exists())

    def test_select_cashback_category(self):
        from finance.models import BankCashbackCategory, BankCashbackMonth, BankCashbackSelection, CashbackCategory
        today = timezone.now()
        
        BankCashbackMonth.objects.create(bank=self.bank, year=today.year, month=today.month)
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        
        response = self.client.get(f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/select/{category.pk}/')
        self.assertEqual(response.status_code, 302)
        
        selection = BankCashbackSelection.objects.filter(
            bank_cashback_month__bank=self.bank,
            bank_cashback_category=category
        ).first()
        self.assertIsNotNone(selection)
        self.assertTrue(selection.is_selected)

    def test_select_cashback_category_first_time(self):
        from finance.models import BankCashbackCategory, BankCashbackMonth, BankCashbackSelection, CashbackCategory
        today = timezone.now()
        
        BankCashbackMonth.objects.create(bank=self.bank, year=today.year, month=today.month)
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        
        self.assertFalse(BankCashbackSelection.objects.filter(
            bank_cashback_month__bank=self.bank,
            bank_cashback_category=category
        ).exists())
        
        response = self.client.get(f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/select/{category.pk}/')
        self.assertEqual(response.status_code, 302)
        
        selection = BankCashbackSelection.objects.get(
            bank_cashback_month__bank=self.bank,
            bank_cashback_category=category
        )
        self.assertTrue(selection.is_selected)

    def test_deselect_cashback_category(self):
        from finance.models import BankCashbackCategory, BankCashbackMonth, BankCashbackSelection, CashbackCategory
        today = timezone.now()
        
        month = BankCashbackMonth.objects.create(bank=self.bank, year=today.year, month=today.month)
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        BankCashbackSelection.objects.create(
            bank_cashback_month=month,
            bank_cashback_category=category,
            is_selected=True
        )
        
        response = self.client.get(f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/select/{category.pk}/')
        self.assertEqual(response.status_code, 302)
        
        selection = BankCashbackSelection.objects.get(
            bank_cashback_month=month,
            bank_cashback_category=category
        )
        self.assertFalse(selection.is_selected)

    def test_cannot_select_more_than_limit(self):
        from finance.models import BankCashbackCategory, BankCashbackMonth, BankCashbackSelection, CashbackCategory
        today = timezone.now()
        
        month = BankCashbackMonth.objects.create(bank=self.bank, year=today.year, month=today.month, max_categories=2)
        
        cat1 = BankCashbackCategory.objects.create(bank=self.bank, category=CashbackCategory.objects.create(name='Products'), percent=Decimal('5.0'))
        cat2 = BankCashbackCategory.objects.create(bank=self.bank, category=CashbackCategory.objects.create(name='Cafe and restaurants'), percent=Decimal('3.0'))
        cat3 = BankCashbackCategory.objects.create(bank=self.bank, category=CashbackCategory.objects.create(name='Transport'), percent=Decimal('2.0'))
        
        BankCashbackSelection.objects.create(bank_cashback_month=month, bank_cashback_category=cat1, is_selected=True)
        BankCashbackSelection.objects.create(bank_cashback_month=month, bank_cashback_category=cat2, is_selected=True)
        
        response = self.client.get(f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/select/{cat3.pk}/')
        self.assertEqual(response.status_code, 302)
        
        selection = BankCashbackSelection.objects.get(bank_cashback_month=month, bank_cashback_category=cat3)
        self.assertFalse(selection.is_selected)

    def test_bank_view_with_cashback(self):
        from finance.models import BankCashbackCategory, BankCashbackMonth, BankCashbackSelection, CashbackCategory
        today = timezone.now()
        
        month = BankCashbackMonth.objects.create(bank=self.bank, year=today.year, month=today.month)
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        BankCashbackSelection.objects.create(
            bank_cashback_month=month,
            bank_cashback_category=category,
            is_selected=True
        )
        
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Products')
        self.assertContains(response, '5.00%')

    def test_cashback_edit_limits(self):
        from finance.models import BankCashbackMonth
        today = timezone.now()
        
        month = BankCashbackMonth.objects.create(
            bank=self.bank, 
            year=today.year, 
            month=today.month,
            common_limit=Decimal('5000.00')
        )
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/edit/',
            {'common_limit': '10000', 'max_categories': '4'}
        )
        self.assertEqual(response.status_code, 302)
        
        month.refresh_from_db()
        self.assertEqual(month.common_limit, Decimal('10000.00'))
        self.assertEqual(month.max_categories, 4)


class CashbackOverviewViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bank = Bank.objects.create(name='Sberbank', cashback_categories_limit=3)
        self.client.force_login(self.user)

    def test_cashback_overview_empty(self):
        response = self.client.get('/cashback/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No cashback data')

    def test_cashback_overview_with_data(self):
        from finance.models import BankCashbackCategory, BankCashbackMonth, BankCashbackSelection, CashbackCategory
        today = timezone.now()
        
        month = BankCashbackMonth.objects.create(
            bank=self.bank,
            year=today.year,
            month=today.month,
            common_limit=Decimal('10000.00')
        )
        cashback_cat = CashbackCategory.objects.create(name='Products')
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=cashback_cat,
            percent=Decimal('5.0')
        )
        BankCashbackSelection.objects.create(
            bank_cashback_month=month,
            bank_cashback_category=category,
            is_selected=True
        )
        
        response = self.client.get(f'/cashback/{today.year}/{today.month}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sberbank')
        self.assertContains(response, 'Products')

    def test_cashback_overview_navigation(self):
        from datetime import datetime
        response = self.client.get('/cashback/')
        self.assertEqual(response.status_code, 200)
        
        next_month = datetime.now().month + 1
        next_year = datetime.now().year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        response = self.client.get(f'/cashback/{next_year}/{next_month}/')
        self.assertEqual(response.status_code, 200)


class CashbackCategoryModelTest(TestCase):
    """Tests for the new CashbackCategory model."""
    
    def test_create_cashback_category(self):
        from finance.models import CashbackCategory
        category = CashbackCategory.objects.create(
            name='Test Category',
            image='cashback_categories/test.svg',
            waste_category='PRODUCTS'
        )
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.image, 'cashback_categories/test.svg')
        self.assertEqual(category.waste_category, 'PRODUCTS')
    
    def test_cashback_category_str(self):
        from finance.models import CashbackCategory
        category = CashbackCategory.objects.create(name='Products')
        self.assertEqual(str(category), 'Products')
    
    def test_cashback_category_optional_waste_category(self):
        from finance.models import CashbackCategory
        category = CashbackCategory.objects.create(
            name='Custom Category',
            waste_category=None
        )
        self.assertIsNone(category.waste_category)
    
    def test_cashback_category_unique_name(self):
        from finance.models import CashbackCategory
        CashbackCategory.objects.create(name='Products')
        with self.assertRaises(Exception):
            CashbackCategory.objects.create(name='Products')
    
    def test_cashback_category_ordering(self):
        from finance.models import CashbackCategory
        CashbackCategory.objects.create(name='Zebra')
        CashbackCategory.objects.create(name='Apple')
        CashbackCategory.objects.create(name='Mango')
        
        categories = list(CashbackCategory.objects.values_list('name', flat=True))
        self.assertEqual(categories, ['Apple', 'Mango', 'Zebra'])


class BankCashbackCategoryForeignKeyTest(TestCase):
    """Tests for BankCashbackCategory with ForeignKey to CashbackCategory."""
    
    def setUp(self):
        from finance.models import CashbackCategory, Bank
        self.bank = Bank.objects.create(name='Test Bank')
        self.cashback_cat = CashbackCategory.objects.create(name='Products')
    
    def test_bank_cashback_category_with_fk(self):
        from finance.models import BankCashbackCategory
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=self.cashback_cat,
            percent=Decimal('5.0'),
            limit=Decimal('3000.00')
        )
        self.assertEqual(category.category.name, 'Products')
        self.assertEqual(category.percent, Decimal('5.0'))
    
    def test_bank_cashback_category_str(self):
        from finance.models import BankCashbackCategory
        category = BankCashbackCategory.objects.create(
            bank=self.bank,
            category=self.cashback_cat,
            percent=Decimal('5.0')
        )
        self.assertIn('Test Bank', str(category))
        self.assertIn('Products', str(category))
        self.assertIn('5.0', str(category))


class BankSaveCategoriesViewTest(TestCase):
    """Tests for the bank_save_categories view (Step 1)."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bank = Bank.objects.create(name='Sberbank', cashback_categories_limit=3)
        self.client.force_login(self.user)
        
        from finance.models import CashbackCategory
        self.cat1 = CashbackCategory.objects.create(name='Products')
        self.cat2 = CashbackCategory.objects.create(name='Transport')
        self.cat3 = CashbackCategory.objects.create(name='Cafe')
    
    def test_save_categories_creates_month_categories(self):
        from finance.models import BankCashbackMonth, BankCashbackMonthCategory
        today = timezone.now()
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/save/',
            {
                'category_ids[]': [self.cat1.pk, self.cat2.pk],
                f'percent_{self.cat1.pk}': '5.0',
                f'percent_{self.cat2.pk}': '3.0',
                f'limit_{self.cat1.pk}': '3000',
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Check that BankCashbackMonth was created
        month_obj = BankCashbackMonth.objects.get(bank=self.bank, year=today.year, month=today.month)
        self.assertIsNotNone(month_obj)
        
        # Check that BankCashbackMonthCategory objects were created
        self.assertEqual(BankCashbackMonthCategory.objects.filter(bank_cashback_month=month_obj).count(), 2)
        
        cat1_month = BankCashbackMonthCategory.objects.get(bank_cashback_month=month_obj, category=self.cat1)
        self.assertEqual(cat1_month.percent, Decimal('5.0'))
        self.assertEqual(cat1_month.limit, Decimal('3000'))
    
    def test_save_categories_redirects_to_bank_view(self):
        today = timezone.now()
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/save/',
            {
                'category_ids[]': [self.cat1.pk],
                f'percent_{self.cat1.pk}': '5.0',
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/bank/{self.bank.pk}/')
    
    def test_save_categories_updates_existing(self):
        from finance.models import BankCashbackMonth, BankCashbackMonthCategory
        today = timezone.now()
        
        # Create initial month and category
        month_obj = BankCashbackMonth.objects.create(
            bank=self.bank,
            year=today.year,
            month=today.month
        )
        BankCashbackMonthCategory.objects.create(
            bank_cashback_month=month_obj,
            category=self.cat1,
            percent=Decimal('1.0')
        )
        
        # Update via view
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/save/',
            {
                'category_ids[]': [self.cat1.pk],
                f'percent_{self.cat1.pk}': '10.0',
            }
        )
        self.assertEqual(response.status_code, 302)
        
        cat1_month = BankCashbackMonthCategory.objects.get(bank_cashback_month=month_obj, category=self.cat1)
        self.assertEqual(cat1_month.percent, Decimal('10.0'))

    def test_save_categories_then_bank_view_shows_categories(self):
        """Test that after Step 1, the bank page shows categories in Available section."""
        from finance.models import BankCashbackMonth, BankCashbackMonthCategory
        today = timezone.now()
        
        # Step 1: Save categories
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/save/',
            {
                'category_ids[]': [self.cat1.pk, self.cat2.pk],
                f'percent_{self.cat1.pk}': '5.0',
                f'percent_{self.cat2.pk}': '3.0',
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify month categories exist in database
        month_obj = BankCashbackMonth.objects.get(bank=self.bank, year=today.year, month=today.month)
        month_cats = BankCashbackMonthCategory.objects.filter(bank_cashback_month=month_obj)
        self.assertEqual(month_cats.count(), 2)
        
        # Check bank page shows "Available categories" with Products and Transport
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available categories')
        self.assertContains(response, 'Products')
        self.assertContains(response, 'Transport')
        self.assertContains(response, 'Save')
    
    def test_save_categories_debug_flow(self):
        """Debug test to trace the full flow."""
        from finance.models import BankCashbackMonth, BankCashbackMonthCategory
        today = timezone.now()
        
        # Initial state - should show "Show all categories"
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Show all categories')
        
        # Initial database state - no month categories
        self.assertEqual(BankCashbackMonthCategory.objects.count(), 0)
        
        # Step 1: Save categories via POST
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/save/',
            {
                'category_ids[]': [str(self.cat1.pk), str(self.cat2.pk)],
                f'percent_{self.cat1.pk}': '5.0',
                f'percent_{self.cat2.pk}': '3.0',
                f'limit_{self.cat1.pk}': '3000',
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Database should have month and 2 BankCashbackMonthCategory objects
        month_obj = BankCashbackMonth.objects.get(bank=self.bank, year=today.year, month=today.month)
        month_cats = BankCashbackMonthCategory.objects.filter(bank_cashback_month=month_obj)
        self.assertEqual(month_cats.count(), 2, f"Expected 2 month categories, got {month_cats.count()}")
        
        # Verify the saved data
        cat1_month = BankCashbackMonthCategory.objects.get(bank_cashback_month=month_obj, category=self.cat1)
        self.assertEqual(cat1_month.percent, Decimal('5.0'))
        self.assertEqual(cat1_month.limit, Decimal('3000'))
        
        cat2_month = BankCashbackMonthCategory.objects.get(bank_cashback_month=month_obj, category=self.cat2)
        self.assertEqual(cat2_month.percent, Decimal('3.0'))
        
        # After Step 1, bank page should show month config exists
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        
        # Check that month object was created
        self.assertIn('current_month_obj', response.context)
        self.assertIsNotNone(response.context['current_month_obj'])
        
        # Check rendered HTML has Save form (since month exists)
        content = response.content.decode()
        self.assertIn('Save', content)
        
    def test_save_categories_persists_in_database(self):
        """Test that saved categories persist in database after Step 1."""
        from finance.models import BankCashbackMonth, BankCashbackMonthCategory
        today = timezone.now()
        
        # Save categories via POST
        self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/save/',
            {
                'category_ids[]': [str(self.cat1.pk), str(self.cat2.pk)],
                f'percent_{self.cat1.pk}': '5.0',
                f'percent_{self.cat2.pk}': '3.0',
                f'limit_{self.cat1.pk}': '3000',
            }
        )
        
        # Get the month
        month_obj = BankCashbackMonth.objects.get(bank=self.bank, year=today.year, month=today.month)
        
        # Verify in database
        cat1_month = BankCashbackMonthCategory.objects.filter(bank_cashback_month=month_obj, category=self.cat1).first()
        self.assertIsNotNone(cat1_month, "BankCashbackMonthCategory for cat1 should exist")
        self.assertEqual(cat1_month.percent, Decimal('5.0'))
        self.assertEqual(cat1_month.limit, Decimal('3000'))
        
        cat2_month = BankCashbackMonthCategory.objects.filter(bank_cashback_month=month_obj, category=self.cat2).first()
        self.assertIsNotNone(cat2_month, "BankCashbackMonthCategory for cat2 should exist")
        self.assertEqual(cat2_month.percent, Decimal('3.0'))
        self.assertIsNone(cat2_month.limit)
        
        # Verify cat3 was NOT saved
        cat3_month = BankCashbackMonthCategory.objects.filter(bank_cashback_month=month_obj, category=self.cat3).first()
        self.assertIsNone(cat3_month, "BankCashbackMonthCategory for cat3 should NOT exist")


class BankAddNewCategoryViewTest(TestCase):
    """Tests for the bank_add_new_category view."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bank = Bank.objects.create(name='Sberbank', cashback_categories_limit=3)
        self.client.force_login(self.user)
    
    def test_add_new_category_creates_cashback_category(self):
        from finance.models import CashbackCategory
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/add-category/',
            {'name': 'New Category'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Check CashbackCategory was created
        self.assertTrue(CashbackCategory.objects.filter(name='New Category').exists())
    
    def test_add_new_category_with_existing_name(self):
        from finance.models import CashbackCategory
        
        # Create existing category
        CashbackCategory.objects.create(name='Existing Category')
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/add-category/',
            {'name': 'Existing Category'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Should only have one CashbackCategory
        self.assertEqual(CashbackCategory.objects.filter(name='Existing Category').count(), 1)
    
    def test_add_new_category_empty_name(self):
        from finance.models import CashbackCategory
        
        initial_count = CashbackCategory.objects.count()
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/add-category/',
            {'name': ''}
        )
        self.assertEqual(response.status_code, 302)
        
        # No new categories should be created
        self.assertEqual(CashbackCategory.objects.count(), initial_count)


class BankSelectCategoriesViewTest(TestCase):
    """Tests for the bank_select_categories view (Step 2)."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bank = Bank.objects.create(name='Sberbank', cashback_categories_limit=3)
        self.client.force_login(self.user)
        
        from finance.models import CashbackCategory, BankCashbackCategory
        self.cat1 = CashbackCategory.objects.create(name='Products')
        self.cat2 = CashbackCategory.objects.create(name='Transport')
        self.cat3 = CashbackCategory.objects.create(name='Cafe')
        
        # Create bank categories
        self.bank_cat1 = BankCashbackCategory.objects.create(
            bank=self.bank, category=self.cat1, percent=Decimal('5.0')
        )
        self.bank_cat2 = BankCashbackCategory.objects.create(
            bank=self.bank, category=self.cat2, percent=Decimal('3.0')
        )
        self.bank_cat3 = BankCashbackCategory.objects.create(
            bank=self.bank, category=self.cat3, percent=Decimal('2.0')
        )
    
    def test_select_categories_creates_month_and_selections(self):
        from finance.models import BankCashbackMonth, BankCashbackSelection
        today = timezone.now()
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/choose/',
            {
                'selected_categories[]': [self.bank_cat1.pk, self.bank_cat2.pk]
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Check BankCashbackMonth was created
        month = BankCashbackMonth.objects.get(
            bank=self.bank,
            year=today.year,
            month=today.month
        )
        self.assertIsNotNone(month)
        
        # Check selections were created
        selections = BankCashbackSelection.objects.filter(
            bank_cashback_month=month,
            is_selected=True
        )
        self.assertEqual(selections.count(), 2)
    
    def test_select_categories_respects_max_limit(self):
        from finance.models import BankCashbackMonth, BankCashbackSelection
        today = timezone.now()
        
        # Set max_categories to 2
        self.bank.cashback_categories_limit = 2
        self.bank.save()
        
        response = self.client.post(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/choose/',
            {
                'selected_categories[]': [self.bank_cat1.pk, self.bank_cat2.pk, self.bank_cat3.pk]
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Check only 2 were selected
        month = BankCashbackMonth.objects.get(
            bank=self.bank,
            year=today.year,
            month=today.month
        )
        selections = BankCashbackSelection.objects.filter(
            bank_cashback_month=month,
            is_selected=True
        )
        self.assertEqual(selections.count(), 2)
    
    def test_select_categories_view_get_request(self):
        today = timezone.now()
        
        response = self.client.get(
            f'/bank/{self.bank.pk}/cashback/{today.year}/{today.month}/choose/'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Products')
        self.assertContains(response, 'Transport')
        self.assertContains(response, 'Cafe')


class BankViewWithNewCategoriesTest(TestCase):
    """Tests for bank_view with the new category system."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.bank = Bank.objects.create(name='Sberbank', cashback_categories_limit=3)
        self.client.force_login(self.user)
        
        from finance.models import CashbackCategory
        self.cat1 = CashbackCategory.objects.create(name='Products')
        self.cat2 = CashbackCategory.objects.create(name='Transport')
    
    def test_bank_view_shows_show_all_categories_button_when_no_month(self):
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Show all categories')
    
    def test_bank_view_shows_available_categories_when_month_categories_exist(self):
        from finance.models import BankCashbackMonth, BankCashbackMonthCategory, BankCashbackCategory
        
        # Create month and month-specific categories
        today = timezone.now()
        month_obj = BankCashbackMonth.objects.create(
            bank=self.bank,
            year=today.year,
            month=today.month
        )
        BankCashbackMonthCategory.objects.create(
            bank_cashback_month=month_obj,
            category=self.cat1,
            percent=Decimal('5.0')
        )
        # Also create BankCashbackCategory (would be created by Step 1)
        BankCashbackCategory.objects.create(
            bank=self.bank,
            category=self.cat1,
            percent=Decimal('5.0')
        )
        
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available categories')
        self.assertContains(response, 'Products')
    
    def test_bank_view_passes_available_categories_to_template(self):
        from finance.models import BankCashbackMonth, BankCashbackMonthCategory, BankCashbackCategory
        
        today = timezone.now()
        month_obj = BankCashbackMonth.objects.create(
            bank=self.bank,
            year=today.year,
            month=today.month
        )
        # Create BankCashbackMonthCategory (month-specific config)
        BankCashbackMonthCategory.objects.create(
            bank_cashback_month=month_obj,
            category=self.cat1,
            percent=Decimal('5.0')
        )
        BankCashbackMonthCategory.objects.create(
            bank_cashback_month=month_obj,
            category=self.cat2,
            percent=Decimal('3.0')
        )
        # Create BankCashbackCategory (bank-level)
        BankCashbackCategory.objects.create(
            bank=self.bank,
            category=self.cat1,
            percent=Decimal('5.0')
        )
        BankCashbackCategory.objects.create(
            bank=self.bank,
            category=self.cat2,
            percent=Decimal('3.0')
        )
        
        response = self.client.get(f'/bank/{self.bank.pk}/')
        self.assertEqual(response.status_code, 200)
        
        # Check current_available is in context
        self.assertIn('current_available', response.context)
        self.assertEqual(len(response.context['current_available']), 2)

