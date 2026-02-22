from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models

from finance.models import Asset, Transaction, AssetType, TransactionType, WasteCategory, RefillCategory, BrokerageAccountType, get_asset_type_label
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
def transactions(request, year=None, month=None, asset_uuid=None):
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
    
    if asset_uuid:
        transactions_list = transactions_list.filter(
            models.Q(from_asset_id=asset_uuid) | models.Q(to_asset_id=asset_uuid)
        )
    
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
        'asset': Asset.objects.filter(id=asset_uuid).first() or "",
        'prev_month': prev_month,
        'next_month': next_month,
        'month_income': month_income,
        'month_expense': month_expense,
        'month_balance': month_balance,
    })


@login_required
def transaction_add(request, year=None, month=None, day=None):
    initial_date = None
    now = datetime.now()
    if year and month and day:
        initial_date = make_aware(datetime(int(year), int(month), int(day), now.hour, now.minute))
    elif year and month:
        initial_date = make_aware(datetime(int(year), int(month), 1, now.hour, now.minute))
    else:
        initial_date = make_aware(now)
    
    assets = Asset.objects.filter(user=request.user, is_active=True)
    
    if request.method == 'POST':
        t_type = request.POST.get('type')
        amount = Decimal(request.POST.get('amount'))
        currency = request.POST.get('currency')
        category = request.POST.get('category') or ''
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time', '00:00')
        date = make_aware(datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M'))
        
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
        'transaction_types': [t for t in TransactionType.choices if t[0] != TransactionType.CHANGING_BALANCE],
        'transaction_categories': WasteCategory.choices,
        'refill_categories': RefillCategory.choices,
        'initial_date': initial_date.strftime('%Y-%m-%d'),
        'initial_time': initial_date.strftime('%H:%M'),
    })


@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    assets = Asset.objects.filter(user=request.user, is_active=True)
    
    if request.method == 'POST':
        transaction.type = request.POST.get('type')
        transaction.amount = Decimal(request.POST.get('amount'))
        transaction.currency = request.POST.get('currency')
        transaction.category = request.POST.get('category') or ''
        transaction.description = request.POST.get('description')
        transaction.date = make_aware(datetime.strptime(f"{request.POST.get('date')} {request.POST.get('time', '00:00')}", '%Y-%m-%d %H:%M'))
        
        from_asset_id = request.POST.get('from_asset')
        to_asset_id = request.POST.get('to_asset')
        
        transaction.from_asset_id = from_asset_id if from_asset_id else None
        transaction.to_asset_id = to_asset_id if to_asset_id else None
        transaction.save()
        
        return redirect('transactions')
    
    return render(request, 'transaction_form.html', {
        'transaction': transaction,
        'assets': assets,
        'transaction_types': [t for t in TransactionType.choices if t[0] != TransactionType.CHANGING_BALANCE],
        'transaction_categories': WasteCategory.choices,
        'refill_categories': RefillCategory.choices,
        'initial_date': transaction.date.strftime('%Y-%m-%d'),
        'initial_time': transaction.date.strftime('%H:%M'),
    })


@login_required
def assets(request):
    assets_list = Asset.objects.filter(user=request.user, is_active=True)
    
    grouped = {}
    total_balance = Decimal('0')
    
    for asset in assets_list:
        asset_type = get_asset_type_label(asset.type)
        if asset_type not in grouped:
            grouped[asset_type] = {'assets': [], 'total': Decimal('0')}
        grouped[asset_type]['assets'].append(asset)
        grouped[asset_type]['total'] += asset.balance
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
                location=request.POST.get('location', ''),
            )
        elif asset_type == AssetType.DEBIT_CARD:
            asset = DebitCardAsset.objects.create(
                user=request.user,
                name=name,
                type=asset_type,
                currency=currency,
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
            )
        
        if balance > 0:
            Transaction.objects.create(
                user=request.user,
                type=TransactionType.CHANGING_BALANCE,
                amount=balance,
                currency=currency,
                to_asset=asset,
                description='Initial balance',
                date=timezone.now()
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
    
    current_balance = asset.balance
    
    if request.method == 'POST':
        asset.name = request.POST.get('name')
        asset.currency = request.POST.get('currency')
        asset.is_active = request.POST.get('is_active') == 'on'
        
        new_balance = Decimal(request.POST.get('balance', '0'))
        
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
        
        if new_balance != current_balance:
            balance_diff = new_balance - current_balance
            if balance_diff > 0:
                Transaction.objects.create(
                    user=request.user,
                    type=TransactionType.CHANGING_BALANCE,
                    amount=abs(balance_diff),
                    currency=asset.currency,
                    to_asset=asset,
                    description='Balance correction',
                    date=timezone.now()
                )
            else:
                Transaction.objects.create(
                    user=request.user,
                    type=TransactionType.CHANGING_BALANCE,
                    amount=abs(balance_diff),
                    currency=asset.currency,
                    from_asset=asset,
                    description='Balance correction',
                    date=timezone.now()
                )
        
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
def statistics(request, year=None, month=None, stat_type='outcome'):
    today = timezone.now()
    
    if stat_type not in ['income', 'outcome']:
        stat_type = 'outcome'
    
    if year is None:
        year = today.year
        month = today.month
        period = 'month'
    elif month is None:
        month = 1
        period = 'year'
    else:
        period = 'month'
    
    if period == 'year':
        start_date = make_aware(datetime(int(year), 1, 1))
        end_date = make_aware(datetime(int(year), 12, 31, 23, 59, 59))
        prev_year = int(year) - 1
        next_year = int(year) + 1
        prev_date = prev_year
        next_date = next_year
    else:
        current_date = make_aware(datetime(int(year), int(month), 1))
        start_date = current_date
        if int(month) == 12:
            end_date = make_aware(datetime(int(year) + 1, 1, 1)) - timedelta(seconds=1)
        else:
            from calendar import monthrange
            _, days = monthrange(int(year), int(month))
            end_date = make_aware(datetime(int(year), int(month), days, 23, 59, 59))
        prev_year = int(year)
        next_year = int(year)
        if int(month) == 1:
            prev_year = int(year) - 1
            prev_month = 12
        else:
            prev_month = int(month) - 1
        if int(month) == 12:
            next_year = int(year) + 1
            next_month = 1
        else:
            next_month = int(month) + 1
        prev_date = (prev_year, prev_month)
        next_date = (next_year, next_month)
    
    transactions_list = Transaction.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    ).exclude(type=TransactionType.CHANGING_BALANCE)
    
    income_by_category = {}
    outcome_by_category = {}
    total_income = Decimal('0')
    total_outcome = Decimal('0')
    
    for t in transactions_list:
        if t.type == TransactionType.REFILL:
            cat = t.category if t.category else 'OTHER_REFILL'
            income_by_category[cat] = income_by_category.get(cat, Decimal('0')) + t.amount
            total_income += t.amount
        elif t.type == TransactionType.WASTE:
            cat = t.category if t.category else 'OTHER_WASTE'
            outcome_by_category[cat] = outcome_by_category.get(cat, Decimal('0')) + t.amount
            total_outcome += t.amount
    
    income_sorted = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
    outcome_sorted = sorted(outcome_by_category.items(), key=lambda x: x[1], reverse=True)
    
    def format_category(cat):
        for choice in RefillCategory.choices:
            if choice[0] == cat:
                return choice[1]
        for choice in WasteCategory.choices:
            if choice[0] == cat:
                return choice[1]
        return cat
    
    income_data = []
    colors = ['#ff6b6b', '#ffa07a', '#ffd93d', '#6bcb77', '#4d96ff', '#9b59b6', '#ff9ff3', '#54a0ff', '#5f27cd', '#48dbfb', '#ff9f43', '#ee5a24', '#009432', '#1289A7', '#D980FA']
    for i, (cat, amount) in enumerate(income_sorted):
        percent = (amount / total_income * 100) if total_income > 0 else 0
        income_data.append({
            'category': format_category(cat),
            'amount': amount,
            'percent': percent,
            'color': colors[i % len(colors)],
        })
    
    outcome_data = []
    for i, (cat, amount) in enumerate(outcome_sorted):
        percent = (amount / total_outcome * 100) if total_outcome > 0 else 0
        outcome_data.append({
            'category': format_category(cat),
            'amount': amount,
            'percent': percent,
            'color': colors[i % len(colors)],
        })
    
    return render(request, 'statistics.html', {
        'year': int(year),
        'month': int(month),
        'period': period,
        'prev_year': prev_date[0] if period == 'month' else prev_date,
        'prev_month': prev_date[1] if period == 'month' else None,
        'next_year': next_date[0] if period == 'month' else next_date,
        'next_month': next_date[1] if period == 'month' else None,
        'stat_type': stat_type,
        'income_data': income_data,
        'outcome_data': outcome_data,
        'total_income': total_income,
        'total_outcome': total_outcome,
    })


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        return redirect('transactions')
    return HttpResponse(f"Delete transaction: {transaction.id}")
