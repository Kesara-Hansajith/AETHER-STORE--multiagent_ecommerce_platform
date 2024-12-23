from django.urls import path
from .views import (
    UserProductView, AdminProductView, OrderView, AdminView, ViewOrdersView,
    LoginView, UserDashboardView
)
from django.shortcuts import render

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('baseUser/', UserDashboardView.as_view(), name='baseUser'),
    path('userproducts/', UserProductView.as_view(), name='user_product_list'),
    path('adminproducts/', AdminProductView.as_view(), name='admin_product_list'),
    path('order/', OrderView.as_view(), name='place_order'),
    path('baseAdmin/', AdminView.as_view(), name='baseAdmin'),
    path('orders/', ViewOrdersView.as_view(), name='view_orders'),
    path('success/', lambda request: render(request, 'store/user/success.html'), name='order_success'),
]
