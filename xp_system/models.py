from django.db import models

# class XPTable(models.Model):
#     level = models.PositiveIntegerField(unique=True)
#     xp_required = models.PositiveIntegerField()
#
#     class Meta:
#         ordering = ['level']
#
#     def __str__(self):
#         return f"Level {self.level} – {self.xp_required} XP"
#
# class ChoreXPTable(models.Model):
#     chore_level = models.PositiveIntegerField(unique=True)
#     chore_xp_required = models.PositiveIntegerField()
#
#     class Meta:
#         ordering = ['level']
#
#     def __str__(self):
#         return f"Level {self.chore_level} – {self.chore_xp_required} XP"
#
# class ReadingXPTable(models.Model):
#     reading_level = models.PositiveIntegerField(unique=True)
#     reading_xp_required = models.PositiveIntegerField()
#
#     class Meta:
#         ordering = ['level']
#
#     def __str__(self):
#         return f"Level {self.reading_level} – {self.reading_xp_required} XP"