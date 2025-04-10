from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseForbidden
from django.db import transaction
import requests
import json

from .forms import UserRegistrationForm, AdminRegistrationForm
from .models import UserProfile


def register_view(request):
    """
    View for registering new regular users
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # Setting initial balance based on currency
                currency = form.cleaned_data.get('currency')

                # Converting initial balance to the user's currency
                if currency != 'GBP':
                    # Making request to the conversion API
                    try:
                        response = requests.get(
                            f'http://localhost:8000/webapps2025/conversion/GBP/{currency}/{settings.INITIAL_BALANCE_GBP}'
                        )
                        if response.status_code == 200:
                            conversion_data = response.json()
                            initial_balance = conversion_data['converted_amount']
                        else:
                            # Fallback to GBP if conversion fails
                            initial_balance = settings.INITIAL_BALANCE_GBP
                    except:
                        # Fallback to GBP if request fails
                        initial_balance = settings.INITIAL_BALANCE_GBP
                else:
                    initial_balance = settings.INITIAL_BALANCE_GBP

                # Update user's balance
                user.profile.balance = initial_balance
                user.profile.save()

                # Log the user in
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                login(request, user)

                return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'register/register.html', {'form': form})


@login_required
def admin_register_view(request):
    """
    View for registering new administrators (only accessible by admins)
    """
    # Check if the user is an admin
    if not request.user.profile.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")

    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                return redirect('admin_dashboard')
    else:
        form = AdminRegistrationForm()

    return render(request, 'register/admin_register.html', {'form': form})


@login_required
def dashboard_view(request):
    """
    User dashboard view
    """
    #if user is admin and redirect to admin dashboard
    if request.user.profile.is_admin:
        return redirect('admin_dashboard')

    return render(request, 'payapp/dashboard.html')


@login_required
def admin_dashboard_view(request):
    """
    Admin dashboard view
    """
    # Check if the user is an admin
    if not request.user.profile.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")

    # Get all users and their profiles
    user_profiles = UserProfile.objects.all()

    # Counting admins and regular users correctly
    total_users = user_profiles.count()
    admin_users = user_profiles.filter(is_admin=True).count()
    regular_users = user_profiles.filter(is_admin=False).count()

    context = {
        'user_profiles': user_profiles,
        'total_users': total_users,
        'admin_users': admin_users,
        'regular_users': regular_users
    }

    return render(request, 'register/admin_dashboard.html', context)


def create_initial_admin():
    """
    Function to create initial admin user (called in apps.py)
    """
    from django.contrib.auth.models import User

    if not User.objects.filter(username='admin1').exists():
        user = User.objects.create_user(
            username='admin1',
            password='admin1',
            email='admin1@example.com',
            first_name='Admin',
            last_name='User'
        )
        user.profile.is_admin = True
        user.profile.save()
        print("Created initial admin user: admin1")