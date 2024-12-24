from django.urls import path
from .views import (
    UserProductView, AdminProductView, OrderView, AdminView, ViewOrdersView,
    LoginView, UserDashboardView, FeedbackView, AddFeedbackView  # Remove view_feedbacks import
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
    path('feedbacks/', FeedbackView.as_view(), name='view_feedbacks'),
    path('feedbacks/delete/<int:pk>/', FeedbackView.as_view(), name='delete_feedback'),
    path('feedback/add/', AddFeedbackView.as_view(), name='add_feedback'),
    path('update-product/<str:product_id>/', AdminProductView.as_view(), name='update_product'),
]
