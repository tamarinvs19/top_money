from pathlib import Path
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse, Http404
from finance import views


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.transactions, name='transactions'),
    path('<int:year>/<int:month>/', views.transactions, name='transactions_month'),
    path('transactions/<uuid:asset_uuid>/', views.transactions, name='transactions_asset'),
    path('transactions/<int:year>/<int:month>/<uuid:asset_uuid>/', views.transactions, name='transactions_month_asset'),
    
    path('transaction/add/', views.transaction_add, name='transaction_add'),
    path('transaction/add/<int:year>/<int:month>/<int:day>/', views.transaction_add, name='transaction_add_day'),
    path('transaction/<uuid:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transaction/<uuid:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    
    path('statistics/', views.statistics, name='statistics'),
    path('statistics/<int:year>/', views.statistics, name='statistics_year'),
    path('statistics/<int:year>/<int:month>/', views.statistics, name='statistics_month'),
    path('statistics/<int:year>/<int:month>/<str:stat_type>/', views.statistics, name='statistics_month_type'),
    path('statistics/<int:year>/<str:stat_type>/', views.statistics, name='statistics_year_type'),
    
    path('assets/', views.assets, name='assets'),
    path('asset/add/', views.asset_add, name='asset_add'),
    path('asset/<uuid:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('asset/<uuid:pk>/delete/', views.asset_delete, name='asset_delete'),
    
    path('banks/', views.banks, name='banks'),
    path('bank/add/', views.bank_add, name='bank_add'),
    path('bank/<int:pk>/edit/', views.bank_edit, name='bank_edit'),
    path('bank/<int:pk>/', views.bank_view, name='bank_view'),
    path('bank/<int:pk>/cashback/<int:year>/<int:month>/add/', views.add_cashback_categories, name='add_cashback_categories'),
    path('bank/<int:pk>/cashback/<int:year>/<int:month>/select/<int:category_id>/', views.select_cashback_category, name='select_cashback_category'),
    path('bank/<int:pk>/cashback/<int:year>/<int:month>/edit/', views.bank_cashback_edit, name='bank_cashback_edit'),
    path('bank/<int:pk>/cashback/<int:year>/<int:month>/save/', views.bank_save_categories, name='bank_save_categories'),
    path('bank/<int:pk>/cashback/<int:year>/<int:month>/choose/', views.bank_select_categories, name='bank_select_categories'),
    path('bank/<int:pk>/cashback/<int:year>/<int:month>/selection/', views.bank_save_month_selection, name='bank_save_month_selection'),
    path('bank/<int:pk>/add-category/', views.bank_add_new_category, name='bank_add_new_category'),
    
    path('cashback/', views.cashback_overview, name='cashback_overview'),
    path('cashback/<int:year>/<int:month>/', views.cashback_overview, name='cashback_overview_month'),
    path('cashback/<int:year>/<int:month>/save/<int:pk>/', views.cashback_overview_save, name='cashback_overview_save'),
    path('cashback/<int:year>/<int:month>/select/<int:bank_id>/', views.cashback_overview_select, name='cashback_overview_select'),
    
    path('cashback/categories/', views.cashback_categories_list, name='cashback_categories_list'),
    path('cashback/category/create/', views.cashback_category_create, name='cashback_category_create'),
    path('cashback/category/<int:pk>/edit/', views.cashback_category_edit, name='cashback_category_edit'),
    
    path('provider/add/', views.provider_add, name='provider_add'),
    path('provider/<int:pk>/edit/', views.provider_edit, name='provider_edit'),
    path('provider/<int:pk>/', views.provider_view, name='provider_view'),
    
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('profile/export/', views.export_transactions, name='export_transactions'),
    path('profile/import/', views.import_transactions, name='import_transactions'),
    
    path('api/exchange-rate/', views.api_exchange_rate, name='api_exchange_rate'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
