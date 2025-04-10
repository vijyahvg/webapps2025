from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction as db_transaction
from django.conf import settings
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
import datetime
import decimal
import json

from .models import Transaction
from .forms import PaymentForm, RequestPaymentForm, RespondRequestForm
from register.models import UserProfile

# Import Thrift client for timestamp service
from thrift_client import get_timestamp

# Exchange rates (hardcoded as per requirements)
EXCHANGE_RATES = {
    'GBP': {'GBP': 1.0, 'USD': 1.25, 'EUR': 1.15},
    'USD': {'GBP': 0.8, 'USD': 1.0, 'EUR': 0.92},
    'EUR': {'GBP': 0.87, 'USD': 1.09, 'EUR': 1.0}
}


@login_required
def dashboard_view(request):
    """
    Main dashboard view for regular users
    """
    # Redirect admin users to admin dashboard
    if request.user.profile.is_admin:
        return redirect('admin_dashboard')

    # Get user's profile and transaction counts
    profile = request.user.profile

    # Get pending payment requests where the user is the sender (ones they need to respond to)
    pending_requests = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).count()

    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        sender=request.user
    ).order_by('-timestamp')[:5]

    context = {
        'profile': profile,
        'pending_requests': pending_requests,
        'notification_count': pending_requests,  # Add this for notification badge
        'recent_transactions': recent_transactions
    }

    return render(request, 'payapp/dashboard.html', context)


@login_required
def transaction_list_view(request):
    """
    View for listing a user's transactions
    """
    # Get all transactions for the current user
    sent_transactions = Transaction.objects.filter(sender=request.user)
    received_transactions = Transaction.objects.filter(receiver=request.user)

    # Combine and sort by timestamp
    all_transactions = sorted(
        list(sent_transactions) + list(received_transactions),
        key=lambda x: x.timestamp,
        reverse=True
    )

    # Calculate notification count
    notification_count = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).count()

    # Return the rendered template with transaction and notification data
    return render(request, 'payapp/transactions.html', {
        'transactions': all_transactions,
        'notification_count': notification_count  # Add this line
    })


@login_required
def admin_transaction_list_view(request):
    """
    Admin view for listing all transactions
    """
    # Check if user is admin
    if not request.user.profile.is_admin:
        return HttpResponseForbidden("You don't have permission to access this page.")

    # Get all transactions
    all_transactions = Transaction.objects.all().order_by('-timestamp')

    # Add this to each view before the render statement
    notification_count = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).count()

    return render(request, 'payapp/admin_transactions.html',
                  {'transactions': all_transactions, 'notification_count': notification_count
                   })


@login_required
def notification_view(request):
    """
    View for showing notifications (pending payment requests)
    """
    # Get pending payment requests for the current user
    pending_requests = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).order_by('-timestamp')

    # Add this to each view before the render statement
    notification_count = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).count()

    return render(request, 'payapp/notifications.html',
                  {'pending_requests': pending_requests, 'notification_count': notification_count})


@login_required
def make_payment_view(request):
    """
    View for making a direct payment to another user
    """
    # Calculate notification count at the beginning of the function
    notification_count = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).count()

    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        if form.is_valid():
            recipient_email = form.cleaned_data['recipient_email']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']

            # Get recipient user
            recipient = User.objects.get(email=recipient_email)

            # Check if user has enough balance
            if request.user.profile.balance < amount:
                messages.error(request, "Insufficient balance for this transaction.")
                return redirect('make_payment')

            # Get currencies
            sender_currency = request.user.profile.currency
            receiver_currency = recipient.profile.currency

            # Convert amount to recipient's currency
            if sender_currency != receiver_currency:
                # Use the exchange rate from our dictionary
                exchange_rate = EXCHANGE_RATES[sender_currency][receiver_currency]
                amount_receiver_currency = amount * decimal.Decimal(exchange_rate)
            else:
                amount_receiver_currency = amount

            # Get timestamp from Thrift service
            try:
                timestamp = get_timestamp()
            except Exception:
                # Fallback to current time if Thrift service is unavailable
                timestamp = datetime.datetime.now()

            # Create transaction with atomic operation
            try:
                with db_transaction.atomic():
                    # Update sender's balance
                    request.user.profile.balance -= amount
                    request.user.profile.save()

                    # Update recipient's balance
                    recipient.profile.balance += amount_receiver_currency
                    recipient.profile.save()

                    # Create transaction record
                    transaction_obj = Transaction.objects.create(
                        sender=request.user,
                        receiver=recipient,
                        amount=amount,
                        amount_sender_currency=amount,
                        amount_receiver_currency=amount_receiver_currency,
                        sender_currency=sender_currency,
                        receiver_currency=receiver_currency,
                        transaction_type='PAYMENT',
                        status='COMPLETED',
                        timestamp=timestamp,
                        description=description
                    )

                    messages.success(request,
                                     f"Payment of {amount} {sender_currency} sent successfully to {recipient.email}")
                    return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error processing payment: {str(e)}")
                return redirect('make_payment')
    else:
        form = PaymentForm(user=request.user)

    return render(request, 'payapp/make_payment.html', {
        'form': form,
        'notification_count': notification_count  # Add this line
    })


@login_required
def request_payment_view(request):
    """
    View for requesting payment from another user
    """
    # Calculate notification count at the beginning of the function
    notification_count = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).count()

    if request.method == 'POST':
        form = RequestPaymentForm(request.POST, user=request.user)
        if form.is_valid():
            sender_email = form.cleaned_data['sender_email']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']

            # Get sender user
            sender = User.objects.get(email=sender_email)

            # Get currencies
            receiver_currency = request.user.profile.currency
            sender_currency = sender.profile.currency

            # Convert amount to sender's currency
            if receiver_currency != sender_currency:
                exchange_rate = EXCHANGE_RATES[receiver_currency][sender_currency]
                amount_sender_currency = amount * decimal.Decimal(exchange_rate)
            else:
                amount_sender_currency = amount

            # Get timestamp from Thrift service
            try:
                timestamp = get_timestamp()
            except Exception:
                # Fallback to current time if Thrift service is unavailable
                timestamp = datetime.datetime.now()

            # Create payment request
            try:
                transaction_obj = Transaction.objects.create(
                    sender=sender,
                    receiver=request.user,
                    amount=amount,
                    amount_sender_currency=amount_sender_currency,
                    amount_receiver_currency=amount,
                    sender_currency=sender_currency,
                    receiver_currency=receiver_currency,
                    transaction_type='REQUEST',
                    status='PENDING',
                    timestamp=timestamp,
                    description=description
                )

                messages.success(request, f"Payment request of {amount} {receiver_currency} sent to {sender.email}")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"Error creating payment request: {str(e)}")
                return redirect('request_payment')
    else:
        form = RequestPaymentForm(user=request.user)

    return render(request, 'payapp/request_payment.html', {'form': form, 'notification_count': notification_count
                                                           })


@login_required
def respond_to_request_view(request, request_id):
    """
    View for responding to payment requests
    """
    # Calculate notification count at the beginning of the function
    notification_count = Transaction.objects.filter(
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    ).count()

    # Get the payment request
    payment_request = get_object_or_404(
        Transaction,
        id=request_id,
        sender=request.user,
        transaction_type='REQUEST',
        status='PENDING'
    )

    if request.method == 'POST':
        form = RespondRequestForm(request.POST)
        if form.is_valid():
            response = form.cleaned_data['response']

            # Update the payment request status
            if response == 'ACCEPT':
                # Check if user has enough balance
                if request.user.profile.balance < payment_request.amount_sender_currency:
                    messages.error(request, "Insufficient balance to accept this payment request.")
                    return redirect('notifications')

                # Get timestamp from Thrift service
                try:
                    timestamp = get_timestamp()
                except Exception:
                    # Fallback to current time if Thrift service is unavailable
                    timestamp = datetime.datetime.now()

                # Process the payment with atomic operation
                try:
                    with db_transaction.atomic():
                        # Update sender's balance
                        request.user.profile.balance -= payment_request.amount_sender_currency
                        request.user.profile.save()

                        # Update receiver's balance
                        payment_request.receiver.profile.balance += payment_request.amount_receiver_currency
                        payment_request.receiver.profile.save()

                        # Update the payment request
                        payment_request.status = 'COMPLETED'
                        payment_request.timestamp = timestamp
                        payment_request.save()

                        messages.success(request,
                                         f"Payment of {payment_request.amount_sender_currency} {payment_request.sender_currency} completed successfully.")
                except Exception as e:
                    messages.error(request, f"Error processing payment: {str(e)}")
            else:
                # Reject the payment request
                payment_request.status = 'REJECTED'
                payment_request.save()
                messages.info(request, "Payment request rejected.")

            return redirect('notifications')
    else:
        form = RespondRequestForm()

    return render(request, 'payapp/respond_request.html', {
        'form': form,
        'payment_request': payment_request,
        'notification_count': notification_count
    })


@api_view(['GET'])
def currency_conversion_view(request, from_currency, to_currency, amount):
    """
    RESTful API view for currency conversion
    """
    # Validate currencies
    valid_currencies = ['GBP', 'USD', 'EUR']
    if from_currency not in valid_currencies or to_currency not in valid_currencies:
        return Response({
            'error': 'Invalid currency code. Supported currencies are GBP, USD, and EUR.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Convert amount to float
        amount_value = float(amount)

        # Get exchange rate
        exchange_rate = EXCHANGE_RATES[from_currency][to_currency]

        # Calculate converted amount
        converted_amount = amount_value * exchange_rate

        return Response({
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount_value,
            'exchange_rate': exchange_rate,
            'converted_amount': converted_amount
        })
    except ValueError:
        return Response({
            'error': 'Invalid amount format. Please provide a valid number.'
        }, status=status.HTTP_400_BAD_REQUEST)