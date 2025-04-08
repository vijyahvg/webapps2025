from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='register/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Admin URLs
    path('admin/register/', views.admin_register_view, name='admin_register'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
]