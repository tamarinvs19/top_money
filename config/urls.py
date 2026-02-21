from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from finance import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.transactions, name='transactions'),
    path('<int:year>/<int:month>/', views.transactions, name='transactions_month'),
    
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
    
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
]
