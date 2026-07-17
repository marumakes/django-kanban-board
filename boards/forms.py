from django import forms
from .models import Board, List, Card


class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Website Redesign"}),
        }


class ListForm(forms.ModelForm):
    class Meta:
        model = List
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "List name"}),
        }


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Card title"}),
            "description": forms.Textarea(attrs={"placeholder": "Add a description...", "rows": 4}),
        }
