from django.db import models
from django.utils import timezone

class Dishes(models.Model):
    """Doing the dishes"""
    dishes_laborer = models.CharField(max_length=20)
    dishes_cost = models.IntegerField()

class Trash(models.Model):
    """Taking out the trash"""
    trash_laborer = models.CharField(max_length=20)
    trash_cost = models.IntegerField()

class Bathroom_one(models.Model):
    """Clean Bathroom 1"""
    bathroom_one_laborer = models.CharField(max_length=20)
    bathroom_one_cost = models.IntegerField()

class Bathroom_two(models.Model):
    """Clean Bathroom 2"""
    bathroom_two_laborer = models.CharField(max_length=20)
    bathroom_two_cost = models.IntegerField()

class Playroom(models.Model):
    """Clean Playroom"""
    playroom_laborer = models.CharField(max_length=20)
    playroom_cost = models.IntegerField()

class Vacuum(models.Model):
    """Vacuum different rooms of the hous"""
    vacuum_laborer = models.CharField(max_length=20)
    vacuum_cost = models.IntegerField()

class Dust(models.Model):
    """Dust in different rooms of the house"""
    dust_laborer = models.CharField(max_length=20)
    dust_cost = models.IntegerField()

class ChoreLogging(models.Model):
    """For logging the labor"""
    chore_done = models.CharField(max_length=20)
    time_done = models.DateTimeField

class DateTimeField(models.Model):
    """For storing the datetime for logging the chores"""
    current_datetime = timezone.now()