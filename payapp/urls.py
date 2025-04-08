from django.urls import path
from . import views

urlpatterns = [
    # Main dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Transaction routes
    path('transactions/', views.transaction_list_view, name='transactions'),
    path('make-payment/', views.make_payment_view, name='make_payment'),
    path('request-payment/', views.request_payment_view, name='request_payment'),
    path('respond-request/<int:request_id>/', views.respond_to_request_view, name='respond_request'),

    # Admin transaction view
    path('admin/transactions/', views.admin_transaction_list_view, name='admin_transactions'),

    # Notification routes
    path('notifications/', views.notification_view, name='notifications'),

    # RESTful currency conversion service
    path('conversion/<str:from_currency>/<str:to_currency>/<str:amount>/',
         views.currency_conversion_view, name='currency_conversion'),
]