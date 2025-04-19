from decimal import Decimal
from chores.models import EarnedWage  # Update 'chores' to your app

def run():
    for wage in EarnedWage.objects.all():
        if not isinstance(wage.earnedLifetime, Decimal):
            wage.earnedLifetime = Decimal(wage.earnedLifetime or '0.00')
        if not isinstance(wage.earnedSincePayout, Decimal):
            wage.earnedSincePayout = Decimal(wage.earnedSincePayout or '0.00')
        wage.save()
    print("Done fixing EarnedWage values.")