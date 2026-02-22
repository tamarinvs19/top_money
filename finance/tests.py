from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

from finance.models import (
    Asset, CashAsset, DebitCardAsset, DepositAsset, 
    CreditCardAsset, BrokerageAsset, Transaction, 
    AssetType, TransactionType, WasteCategory, RefillCategory, BrokerageAccountType,
    BankAsset, BankInvestment, SavingAccount
)
from finance.currency import CurrencyConverter


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
        asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            currency='RUB',
            bank_name='Sberbank',
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


class CurrencyConverterTest(TestCase):
    def test_same_currency(self):
        result = CurrencyConverter.convert(Decimal('100'), 'RUB', 'RUB')
        self.assertEqual(result, Decimal('100'))

    def test_rub_to_usd(self):
        result = CurrencyConverter.convert(Decimal('1000'), 'RUB', 'USD')
        self.assertEqual(result, Decimal('11.0'))

    def test_usd_to_rub(self):
        result = CurrencyConverter.convert(Decimal('100'), 'USD', 'RUB')
        self.assertEqual(result, Decimal('9000.0'))

    def test_rub_to_eur(self):
        result = CurrencyConverter.convert(Decimal('1000'), 'RUB', 'EUR')
        self.assertEqual(result, Decimal('10.0'))

    def test_eur_to_rub(self):
        result = CurrencyConverter.convert(Decimal('100'), 'EUR', 'RUB')
        self.assertEqual(result, Decimal('10000.0'))

    def test_usd_to_eur(self):
        result = CurrencyConverter.convert(Decimal('100'), 'USD', 'EUR')
        self.assertEqual(result, Decimal('92.0'))

    def test_eur_to_usd(self):
        result = CurrencyConverter.convert(Decimal('100'), 'EUR', 'USD')
        self.assertEqual(result, Decimal('109.0'))

    def test_unsupported_conversion(self):
        with self.assertRaises(ValueError):
            CurrencyConverter.convert(Decimal('100'), 'GBP', 'RUB')


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
            date=timezone.now()
        )
        calculated = self.asset.calculate_balance()
        self.assertEqual(calculated, Decimal('100000.00'))

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
        from datetime import datetime
        from django.utils.timezone import make_aware
        
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
        asset = DebitCardAsset.objects.create(
            user=self.user,
            name='Sberbank Card',
            type=AssetType.DEBIT_CARD,
            bank_name='Sberbank',
            last_4_digits='1234'
        )
        self.assertEqual(asset.bank_name, 'Sberbank')
        self.assertIsInstance(asset, BankAsset)

    def test_credit_card_inherits_bank_name(self):
        asset = CreditCardAsset.objects.create(
            user=self.user,
            name='Tinkoff Credit',
            type=AssetType.CREDIT_CARD,
            bank_name='Tinkoff',
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
