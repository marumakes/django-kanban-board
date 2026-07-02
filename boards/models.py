from django.db import models
from django.conf import settings

class Board(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)

class List(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='lists')
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default = 0)

class Card(models.Model):
    list = models.ForeignKey(List,on_delete=models.CASCADE, related_name="cards")
    title = models.CharField(max_length = 200)
    description = models.TextField(blank = True)
    position = models.PositiveIntegerField(default = 0)
