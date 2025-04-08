from django.db import models
from django.contrib.auth.models import User


class Transaction(models.Model):
    """
    Model for tracking all payment transactions
    """
    TRANSACTION_TYPES = (
        ('PAYMENT', 'Direct Payment'),
        ('REQUEST', 'Payment Request'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # Amount in sender's currency
    amount_sender_currency = models.DecimalField(max_digits=12, decimal_places=2)
    # Amount in receiver's currency
    amount_receiver_currency = models.DecimalField(max_digits=12, decimal_places=2)
    sender_currency = models.CharField(max_length=3)
    receiver_currency = models.CharField(max_length=3)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField()
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.amount} {self.sender_currency} ({self.transaction_type}, {self.status})"

    class Meta:
        ordering = ['-timestamp']
