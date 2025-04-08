from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends the built-in User model with additional fields
    """
    CURRENCY_CHOICES = (
        ('GBP', 'British Pound (£)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile ({self.currency})"


# Create a user profile automatically when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

