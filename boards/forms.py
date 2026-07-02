from django import forms
from .models import Board, List, Card

class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ["name"]

class ListForm(forms.ModelForm):
    class Meta:
        model = List
        fields = ["name"]

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ["title", "description"]
