import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Board, List, Card
from .forms import BoardForm, ListForm, CardForm

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("board_list")
        
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

@login_required
def board_list(request):
    boards = Board.objects.filter(owner=request.user)
    return render(request, "boards/board_list.html", {"boards": boards})

@login_required
def board_create(request):
    if request.method == "POST":
        form = BoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.owner = request.user
            board.save()
            return redirect("board_detail", board_id=board.id)
    
    else: 
        form = BoardForm()
    
    return render(request, "boards/board_form.html", {"form": form})

@login_required
def board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    lists = board.lists.prefetch_related("cards").order_by("position")
    return render(request, "boards/board_detail.html", {
        "board": board,
        "lists": lists,
        "list_form": ListForm(),
        "card_form": CardForm(),
    })

@login_required
def list_create(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    if request.method == "POST":
        form = ListForm(request.POST)
        if form.is_valid():
            new_list = form.save(commit=False)
            new_list.board = board
            new_list.position = board.lists.count()
            new_list.save()

    return redirect("board_detail", board_id=board.id)

@login_required
def card_create(request, list_id):
    target_list = get_object_or_404(List, id = list_id, board__owner=request.user)
    if request.method == "POST":
        form = CardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.list = target_list
            card.position = target_list.cards.count()
            card.save()
    return redirect("board_detail", board_id=target_list.board_id)


@login_required
def card_detail(request, card_id):
    card = get_object_or_404(Card, id = card_id, list__board__owner= request.user)
    if request.method == "POST":
        form = CardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            return redirect("board_detail", board_id=card.list.board_id)
    else:
        form = CardForm(instance=card)
    return render(request, "boards/card_detail.html", {"card": card, "form": form})


@login_required
def card_delete(request, card_id):
    card = get_object_or_404(Card, id=card_id, list__board__owner = request.user)
    board_id = card.list.board_id
    if request.method == "POST":
        card.delete()
    return redirect("board_detail", board_id = board_id)


@login_required
@require_POST
def card_reorder(request):
    data = json.loads(request.body)
    target_list = get_object_or_404(List, id=data["list_id"], board__owner=request.user)
    cards = Card.objects.filter(id__in=data["ordered_ids"], list__board__owner = request.user)
    cards_by_id = {card.id: card for card in cards}
    for position, card_id in enumerate(data["ordered_ids"]):
        card = cards_by_id[int(card_id)]
        card.list = target_list
        card.position = position
        card.save(update_fields=["list","position"])
    return JsonResponse({"status": "ok"})

@login_required
def board_update(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    if request.method == "POST":
        form = BoardForm(request.POST, instance=board)
        if form.is_valid():
            form.save()
            return redirect("board_detail", board_id=board.id)
    else:
        form = BoardForm(instance=board)
    return render(request, "boards/board_form.html", {"form": form, "board": board})


@login_required
def board_delete(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    if request.method == "POST":
        board.delete()
        return redirect("board_list")
    return render(request, "boards/board_confirm_delete.html", {"board": board})


@login_required
def list_update(request, list_id):
    target_list = get_object_or_404(List, id=list_id, board__owner=request.user)
    if request.method == "POST":
        form = ListForm(request.POST, instance=target_list)
        if form.is_valid():
            form.save()
    return redirect("board_detail", board_id=target_list.board_id)


@login_required
def list_delete(request, list_id):
    target_list = get_object_or_404(List, id=list_id, board__owner=request.user)
    board_id = target_list.board_id
    if request.method == "POST":
        target_list.delete()
    return redirect("board_detail", board_id=board_id)

@login_required
@require_POST
def list_reorder(request, board_id):
    board = get_object_or_404(Board, id=board_id, owner=request.user)
    data = json.loads(request.body)
    lists = List.objects.filter(id__in = data["ordered_ids"], board=board)
    lists_by_id = {lst.id: lst for lst in lists}
    for position, list_id in enumerate(data["ordered_ids"]):
        lst = lists_by_id[int(list_id)]
        lst.position = position
        lst.save(update_fields=["position"])
    return JsonResponse({"status": "ok"})

