from django.urls import path
from . import views

app_name = 'shop'
urlpatterns = [
    # Artist URLs
    path('artists/', views.artist_list, name='artist_list'),
    path('artists/add/', views.artist_create, name='artist_create'),
    path('artists/<int:pk>/edit/', views.artist_update, name='artist_update'),
    path('artists/<int:pk>/delete/', views.artist_delete, name='artist_delete'),

    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Purchase URLs
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/edit/', views.purchase_update, name='purchase_update'),
    path('purchases/<int:pk>/delete/', views.purchase_delete, name='purchase_delete'),

    # Sale URLs
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/add/', views.sale_create, name='sale_create'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/edit/', views.sale_update, name='sale_update'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),

    # Transaction URLs
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),

    # Balance URLs
    path('balances/', views.balance_list, name='balance_list'),

    # Dashboard URL
    path('dashboard/', views.dashboard, name='dashboard'),
]