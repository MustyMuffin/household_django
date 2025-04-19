from django.db import models
from django.contrib.auth.models import User


class Chore(models.Model):
    """Table mapping admin selected chores to variables"""
    text = models.CharField(max_length=20)
    wage = models.DecimalField(max_digits=5, decimal_places=2)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the model."""
        return self.text

class ChoreEntry(models.Model):
    """For logging the labor"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'chore_entries'
        # permissions = (("can_log_chore", "Can Log Chore"))
#
class EarnedWage(models.Model):
    """For tracking the wages earned"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    earnedLifetime = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    earnedSincePayout = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        verbose_name_plural = 'earned_wages'