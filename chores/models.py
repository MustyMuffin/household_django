from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User


class ChoreCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'chore_categories'

    def __str__(self):
        return self.name

class Chore(models.Model):
    """Table mapping admin selected chores to variables"""
    text = models.CharField(max_length=20)
    wage = models.DecimalField(max_digits=5, decimal_places=2)
    date_added = models.DateTimeField(auto_now_add=True)
    chore_category = models.ForeignKey(ChoreCategory, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text

class ChoreEntry(models.Model):
    """For logging the labor"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
    wage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'chore_entries'
        # permissions = (("can_log_chore", "Can Log Chore"))

    def save(self, *args, **kwargs):
        if self.chore and not self.wage:
            self.wage = self.chore.wage
        super().save(*args, **kwargs)
#
class EarnedWage(models.Model):
    """For tracking the wages earned"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    earnedLifetime = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    earnedSincePayout = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name_plural = 'earned_wages'

class PayoutLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payouts_made')
    test_field = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.performed_by} paid ${self.amount} to {self.user} on {self.created_at}"
