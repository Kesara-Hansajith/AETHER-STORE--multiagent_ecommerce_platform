# store/urls.py
from django.urls import path
from .views import ProductView, OrderView, AdminView, ViewOrdersView
from django.shortcuts import render

urlpatterns = [
    path('', ProductView.as_view(), name='product_list'),
    path('order/', OrderView.as_view(), name='place_order'),
    path('admin-dashboard/', AdminView.as_view(), name='admin_dashboard'),
    path('orders/', ViewOrdersView.as_view(), name='view_orders'),
    path('success/', lambda request: render(request, 'store/success.html'), name='order_success'),
]
