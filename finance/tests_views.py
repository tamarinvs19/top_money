from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import datetime

from finance.models import Asset, Transaction, AssetType, TransactionType


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
    
    def test_signup_get(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
    
    def test_signup_post_creates_user(self):
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_signup_redirects_to_transactions(self):
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }, follow=True)
        self.assertRedirects(response, reverse('transactions'))
    
    def test_login_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Finance Manager')
    
    def test_login_success(self):
        user = User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('transactions'))
    
    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'wronguser',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')


class TransactionViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.asset = Asset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.BANK_CARD,
            currency='RUB',
            balance=Decimal('10000.00')
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_transactions_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('transactions'))
        self.assertRedirects(response, f"{reverse('login')}?next=/")
    
    def test_transactions_list_get(self):
        response = self.client.get(reverse('transactions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transactions')
    
    def test_transactions_list_with_data(self):
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('5000.00'),
            currency='RUB',
            to_asset=self.asset,
            category='Salary',
            date=datetime.now()
        )
        response = self.client.get(reverse('transactions'))
        self.assertContains(response, '5000.00')
        self.assertContains(response, 'Salary')
    
    def test_transactions_navigation(self):
        response = self.client.get(reverse('transactions_month', args=[2026, 1]))
        self.assertEqual(response.status_code, 200)
    
    def test_transaction_add_get(self):
        response = self.client.get(reverse('transaction_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Transaction')
    
    def test_transaction_add_post(self):
        response = self.client.post(reverse('transaction_add'), {
            'type': TransactionType.REFILL,
            'amount': '3000',
            'currency': 'RUB',
            'category': 'Test',
            'description': 'Test transaction',
            'date': '2026-02-18',
            'to_asset': self.asset.pk,
        })
        self.assertTrue(Transaction.objects.filter(amount=Decimal('3000.00')).exists())
        self.assertRedirects(response, reverse('transactions'))
    
    def test_transaction_add_with_year_month_day(self):
        url = reverse('transaction_add_day', args=[2026, 2, 15])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="2026-02-15"')
    
    def test_transaction_edit_get(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=datetime.now()
        )
        url = reverse('transaction_edit', args=[transaction.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Transaction')
    
    def test_transaction_edit_post(self):
        transaction = Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=datetime.now()
        )
        url = reverse('transaction_edit', args=[transaction.pk])
        response = self.client.post(url, {
            'type': TransactionType.WASTE,
            'amount': '500',
            'currency': 'RUB',
            'category': 'Updated',
            'description': 'Updated desc',
            'date': '2026-02-18',
            'from_asset': self.asset.pk,
        })
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, Decimal('500.00'))
        self.assertEqual(transaction.category, 'Updated')
    
    def test_transaction_edit_other_user_forbidden(self):
        other_user = User.objects.create_user(username='other', password='otherpass')
        other_asset = Asset.objects.create(
            user=other_user,
            name='Other Card',
            type=AssetType.BANK_CARD,
            currency='RUB'
        )
        transaction = Transaction.objects.create(
            user=other_user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=other_asset,
            date=datetime.now()
        )
        url = reverse('transaction_edit', args=[transaction.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class AssetViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
    
    def test_assets_list_get(self):
        response = self.client.get(reverse('assets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assets')
    
    def test_assets_list_with_data(self):
        Asset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.BANK_CARD,
            currency='RUB',
            balance=Decimal('5000.00')
        )
        response = self.client.get(reverse('assets'))
        self.assertContains(response, '5000.00')
        self.assertContains(response, 'Test Card')
    
    def test_assets_list_grouped_by_type(self):
        Asset.objects.create(user=self.user, name='Card1', type=AssetType.BANK_CARD, currency='RUB', balance=Decimal('1000'))
        Asset.objects.create(user=self.user, name='Card2', type=AssetType.BANK_CARD, currency='RUB', balance=Decimal('2000'))
        Asset.objects.create(user=self.user, name='Cash', type=AssetType.CASH, currency='RUB', balance=Decimal('500'))
        
        response = self.client.get(reverse('assets'))
        self.assertContains(response, 'BANK_CARD')
        self.assertContains(response, 'CASH')
        self.assertContains(response, '3000')  # total for BANK_CARD
        self.assertContains(response, '500')   # total for CASH
    
    def test_assets_total_balance(self):
        Asset.objects.create(user=self.user, name='Card1', type=AssetType.BANK_CARD, currency='RUB', balance=Decimal('1000'))
        Asset.objects.create(user=self.user, name='Cash', type=AssetType.CASH, currency='RUB', balance=Decimal('500'))
        
        response = self.client.get(reverse('assets'))
        self.assertContains(response, 'Total Balance')
        self.assertContains(response, '1500')
    
    def test_asset_add_get(self):
        response = self.client.get(reverse('asset_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Asset')
    
    def test_asset_add_post(self):
        response = self.client.post(reverse('asset_add'), {
            'name': 'New Card',
            'type': AssetType.BANK_CARD,
            'currency': 'RUB',
            'balance': '5000',
            'bank_name': 'Sberbank',
            'last_4_digits': '1234',
        })
        self.assertTrue(Asset.objects.filter(name='New Card').exists())
        self.assertRedirects(response, reverse('assets'))
    
    def test_asset_edit_get(self):
        asset = Asset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.BANK_CARD,
            currency='RUB',
            balance=Decimal('1000.00')
        )
        url = reverse('asset_edit', args=[asset.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Asset')
        self.assertContains(response, 'Test Card')
    
    def test_asset_edit_post(self):
        asset = Asset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.BANK_CARD,
            currency='RUB',
            balance=Decimal('1000.00')
        )
        url = reverse('asset_edit', args=[asset.pk])
        response = self.client.post(url, {
            'name': 'Updated Card',
            'type': AssetType.BANK_CARD,
            'currency': 'USD',
            'balance': '2000',
            'bank_name': 'Tinkoff',
            'is_active': 'on',
        })
        asset.refresh_from_db()
        self.assertEqual(asset.name, 'Updated Card')
        self.assertEqual(asset.currency, 'USD')
        self.assertEqual(asset.balance, Decimal('2000'))
    
    def test_asset_edit_other_user_forbidden(self):
        other_user = User.objects.create_user(username='other', password='otherpass')
        asset = Asset.objects.create(
            user=other_user,
            name='Other Card',
            type=AssetType.BANK_CARD,
            currency='RUB'
        )
        url = reverse('asset_edit', args=[asset.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TransactionMonthNavigationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.asset = Asset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.BANK_CARD,
            currency='RUB',
            balance=Decimal('10000.00')
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_prev_month_navigation(self):
        from datetime import timedelta
        now = datetime.now()
        prev_month = now - timedelta(days=1)
        
        Transaction.objects.create(
            user=self.user,
            type=TransactionType.REFILL,
            amount=Decimal('1000.00'),
            currency='RUB',
            to_asset=self.asset,
            date=prev_month
        )
        
        url = reverse('transactions_month', args=[prev_month.year, prev_month.month])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1000')


class TransactionFormFieldsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.asset = Asset.objects.create(
            user=self.user,
            name='Test Card',
            type=AssetType.BANK_CARD,
            currency='RUB',
            balance=Decimal('10000.00')
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_refill_shows_to_asset_only(self):
        response = self.client.get(reverse('transaction_add'))
        self.assertContains(response, 'To Asset')
    
    def test_waste_shows_from_asset_only(self):
        response = self.client.get(reverse('transaction_add'))
        self.assertContains(response, 'From Asset')
    
    def test_transfer_shows_both_assets(self):
        response = self.client.get(reverse('transaction_add'))
        self.assertContains(response, 'From Asset')
        self.assertContains(response, 'To Asset')
