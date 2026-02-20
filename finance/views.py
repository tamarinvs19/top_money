from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from finance.models import Asset, Transaction, AssetType, TransactionType, WasteCategory, RefillCategory, BrokerageAccountType
from finance.models import CashAsset, DebitCardAsset, DepositAsset, CreditCardAsset, BrokerageAsset


from django.http import HttpResponse


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('transactions')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def transactions(request, year=None, month=None):
    today = timezone.now()
    if year is None:
        year = today.year
    if month is None:
        month = today.month
    
    current_date = make_aware(datetime(int(year), int(month), 1))
    
    prev_month = current_date - timedelta(days=1)
    next_month = current_date + timedelta(days=31)
    next_month = next_month.replace(day=1)
    
    start_date = current_date
    end_date = current_date.replace(day=1, month=int(month) + 1) if int(month) < 12 else current_date.replace(year=int(year)+1, month=1)
    if int(month) == 12:
        end_date = make_aware(datetime(int(year) + 1, 1, 1)) - timedelta(seconds=1)
    else:
        from calendar import monthrange
        _, days = monthrange(int(year), int(month))
        end_date = make_aware(datetime(int(year), int(month), days, 23, 59, 59))
    
    transactions_list = Transaction.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('from_asset', 'to_asset').order_by('-date')
    
    grouped = {}
    for t in transactions_list:
        day = t.date.date()
        if day not in grouped:
            grouped[day] = {'transactions': [], 'day_total': Decimal('0')}
        grouped[day]['transactions'].append(t)
        
        if t.type == TransactionType.REFILL:
            amount = t.amount
        elif t.type == TransactionType.WASTE:
            amount = -t.amount
        elif t.type == TransactionType.TRANSFER:
            if t.from_asset:
                amount = -t.amount
            else:
                amount = t.amount
        else:
            amount = Decimal('0')
        grouped[day]['day_total'] += amount
    
    month_income = Decimal('0')
    month_expense = Decimal('0')
    
    for day_data in grouped.values():
        for t in day_data['transactions']:
            if t.type == TransactionType.REFILL:
                month_income += t.amount
            elif t.type == TransactionType.WASTE:
                month_expense += t.amount
    
    month_balance = month_income - month_expense
    
    return render(request, 'transactions.html', {
        'transactions_by_day': grouped,
        'year': int(year),
        'month': int(month),
        'prev_month': prev_month,
        'next_month': next_month,
        'month_income': month_income,
        'month_expense': month_expense,
        'month_balance': month_balance,
    })


@login_required
def transaction_add(request, year=None, month=None, day=None):
    initial_date = None
    if year and month and day:
        initial_date = make_aware(datetime(int(year), int(month), int(day)))
    elif year and month:
        initial_date = make_aware(datetime(int(year), int(month), 1))
    else:
        initial_date = timezone.now()
    
    assets = Asset.objects.filter(user=request.user, is_active=True)
    
    if request.method == 'POST':
        t_type = request.POST.get('type')
        amount = Decimal(request.POST.get('amount'))
        currency = request.POST.get('currency')
        category = request.POST.get('category')
        description = request.POST.get('description')
        date = make_aware(datetime.strptime(request.POST.get('date'), '%Y-%m-%d'))
        
        from_asset_id = request.POST.get('from_asset')
        to_asset_id = request.POST.get('to_asset')
        
        Transaction.objects.create(
            user=request.user,
            type=t_type,
            amount=amount,
            currency=currency,
            category=category,
            description=description,
            date=date,
            from_asset_id=from_asset_id if from_asset_id else None,
            to_asset_id=to_asset_id if to_asset_id else None,
        )
        
        return redirect('transactions')
    
    return render(request, 'transaction_form.html', {
        'assets': assets,
        'transaction_types': TransactionType.choices,
        'transaction_categories': WasteCategory.choices,
        'refill_categories': RefillCategory.choices,
        'initial_date': initial_date.strftime('%Y-%m-%d'),
    })


@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    assets = Asset.objects.filter(user=request.user, is_active=True)
    
    if request.method == 'POST':
        transaction.type = request.POST.get('type')
        transaction.amount = Decimal(request.POST.get('amount'))
        transaction.currency = request.POST.get('currency')
        transaction.category = request.POST.get('category')
        transaction.description = request.POST.get('description')
        transaction.date = make_aware(datetime.strptime(request.POST.get('date'), '%Y-%m-%d'))
        
        from_asset_id = request.POST.get('from_asset')
        to_asset_id = request.POST.get('to_asset')
        
        transaction.from_asset_id = from_asset_id if from_asset_id else None
        transaction.to_asset_id = to_asset_id if to_asset_id else None
        transaction.save()
        
        return redirect('transactions')
    
    return render(request, 'transaction_form.html', {
        'transaction': transaction,
        'assets': assets,
        'transaction_types': TransactionType.choices,
        'transaction_categories': WasteCategory.choices,
        'refill_categories': RefillCategory.choices,
        'initial_date': transaction.date.strftime('%Y-%m-%d'),
    })


@login_required
def assets(request):
    assets_list = Asset.objects.filter(user=request.user, is_active=True)
    
    grouped = {}
    total_balance = Decimal('0')
    
    for asset in assets_list:
        if asset.type not in grouped:
            grouped[asset.type] = {'assets': [], 'total': Decimal('0')}
        grouped[asset.type]['assets'].append(asset)
        grouped[asset.type]['total'] += asset.balance
        total_balance += asset.balance
    
    return render(request, 'assets.html', {
        'assets_by_type': grouped,
        'total_balance': total_balance,
    })


@login_required
def asset_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        asset_type = request.POST.get('type')
        currency = request.POST.get('currency')
        balance = Decimal(request.POST.get('balance', '0'))

        if asset_type == AssetType.CASH:
            asset = CashAsset.objects.create(
                user=request.user,
                name=name,
                type=asset_type,
                currency=currency,
                balance=balance,
                location=request.POST.get('location', ''),
            )
        elif asset_type == AssetType.DEBIT_CARD:
            asset = DebitCardAsset.objects.create(
                user=request.user,
                name=name,
                type=asset_type,
                currency=currency,
                balance=balance,
                bank_name=request.POST.get('bank_name', ''),
                last_4_digits=request.POST.get('last_4_digits', ''),
            )
        elif asset_type == AssetType.DEPOSIT:
            renewal_date = request.POST.get('renewal_date')
            asset = DepositAsset.objects.create(
                user=request.user,
                name=name,
                type=asset_type,
                currency=currency,
                balance=balance,
                interest_rate=request.POST.get('interest_rate') or None,
                term_months=request.POST.get('term_months') or None,
                renewal_date=renewal_date if renewal_date else None,
                is_capitalized=request.POST.get('is_capitalized') == 'on',
            )
        elif asset_type == AssetType.CREDIT_CARD:
            asset = CreditCardAsset.objects.create(
                user=request.user,
                name=name,
                type=asset_type,
                currency=currency,
                balance=balance,
                credit_limit=request.POST.get('credit_limit') or None,
                grace_period_days=request.POST.get('grace_period_days') or None,
                last_4_digits=request.POST.get('last_4_digits', ''),
                billing_day=request.POST.get('billing_day') or None,
            )
        elif asset_type == AssetType.BROKERAGE:
            asset = BrokerageAsset.objects.create(
                user=request.user,
                name=name,
                type=asset_type,
                currency=currency,
                balance=balance,
                broker_name=request.POST.get('broker_name', ''),
                account_number=request.POST.get('account_number', ''),
                brokerage_account_type=request.POST.get('brokerage_account_type', ''),
            )
        else:
            asset = Asset.objects.create(
                user=request.user,
                name=name,
                type=asset_type,
                currency=currency,
                balance=balance,
            )
        
        return redirect('assets')
    
    return render(request, 'asset_form.html', {
        'asset_types': AssetType.choices,
        'brokerage_account_types': BrokerageAccountType.choices,
    })


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    
    if asset.type == AssetType.CASH:
        asset = get_object_or_404(CashAsset, pk=pk)
    elif asset.type == AssetType.DEBIT_CARD:
        asset = get_object_or_404(DebitCardAsset, pk=pk)
    elif asset.type == AssetType.DEPOSIT:
        asset = get_object_or_404(DepositAsset, pk=pk)
    elif asset.type == AssetType.CREDIT_CARD:
        asset = get_object_or_404(CreditCardAsset, pk=pk)
    elif asset.type == AssetType.BROKERAGE:
        asset = get_object_or_404(BrokerageAsset, pk=pk)
    
    if request.method == 'POST':
        asset.name = request.POST.get('name')
        asset.currency = request.POST.get('currency')
        asset.is_active = request.POST.get('is_active') == 'on'
        
        balance = request.POST.get('balance')
        if balance:
            asset.balance = Decimal(balance)
        
        if asset.type == AssetType.CASH:
            asset.location = request.POST.get('location', '')
        elif asset.type == AssetType.DEBIT_CARD:
            asset.bank_name = request.POST.get('bank_name', '')
            asset.last_4_digits = request.POST.get('last_4_digits', '')
        elif asset.type == AssetType.DEPOSIT:
            asset.interest_rate = request.POST.get('interest_rate') or None
            asset.term_months = request.POST.get('term_months') or None
            renewal_date = request.POST.get('renewal_date')
            asset.renewal_date = renewal_date if renewal_date else None
            asset.is_capitalized = request.POST.get('is_capitalized') == 'on'
        elif asset.type == AssetType.CREDIT_CARD:
            asset.credit_limit = request.POST.get('credit_limit') or None
            asset.grace_period_days = request.POST.get('grace_period_days') or None
            asset.last_4_digits = request.POST.get('last_4_digits', '')
            asset.billing_day = request.POST.get('billing_day') or None
        elif asset.type == AssetType.BROKERAGE:
            asset.broker_name = request.POST.get('broker_name', '')
            asset.account_number = request.POST.get('account_number', '')
            asset.brokerage_account_type = request.POST.get('brokerage_account_type', '')
        
        asset.save()
        return redirect('assets')
    
    return render(request, 'asset_form.html', {
        'asset': asset,
        'asset_types': AssetType.choices,
        'brokerage_account_types': BrokerageAccountType.choices,
    })


@login_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    if request.method == 'POST':
        asset.delete()
        return redirect('assets')
    return HttpResponse(f"Delete asset: {asset.name}")


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('transactions')
    return HttpResponse(f"Delete transaction: {transaction.id}")
