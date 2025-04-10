from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Transaction


class PaymentForm(forms.Form):
    """
    creating Form for making payments directly to other users in the app/website
    """
    recipient_email = forms.EmailField(
        label='Recipient Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        label='Amount',
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    description = forms.CharField(
        label='Description (optional)',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean_recipient_email(self):
        email = self.cleaned_data.get('recipient_email')

        # Check if the recipient exists
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("No user with this email address exists.")

        # Make sure the user isn't sending money to themselves
        if self.user and self.user.email == email:
            raise ValidationError("You cannot send money to yourself.")

        return email

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PaymentForm, self).__init__(*args, **kwargs)


class RequestPaymentForm(forms.Form):
    """
    creating Form for requesting payment from other users
    """
    sender_email = forms.EmailField(
        label='Requestee Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        label='Amount',
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    description = forms.CharField(
        label='Description (optional)',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean_sender_email(self):
        email = self.cleaned_data.get('sender_email')

        # to  Check if the sender exists or not
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("No user with this email address exists.")

        # Makeing sure the user isn't requesting money from themselves is yes then error message shows up
        if self.user and self.user.email == email:
            raise ValidationError("You cannot request money from yourself.")

        return email

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(RequestPaymentForm, self).__init__(*args, **kwargs)


class RespondRequestForm(forms.Form):
    """
    creating Form for responding to payment requests
    """
    RESPONSE_CHOICES = (
        ('ACCEPT', 'Accept and Pay'),
        ('REJECT', 'Reject Request'),
    )

    response = forms.ChoiceField(
        label='Your Response',
        choices=RESPONSE_CHOICES,
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )