from django.urls import path
from . import views

urlpatterns = [
    path("", views.board_list, name="board_list"),
    path("new/", views.board_create, name="board_create"),
    path("<int:board_id>/", views.board_detail, name="board_detail"),
    path("<int:board_id>/lists/new/", views.list_create, name="list_create"),
    path("lists/<int:list_id>/cards/new/", views.card_create, name="card_create"),
    path("cards/<int:card_id>/", views.card_detail, name="card_detail"),
    path("cards/<int:card_id>/delete/", views.card_delete, name="card_delete"),
    path("cards/reorder/", views.card_reorder, name="card_reorder"),
    path("<int:board_id>/edit/", views.board_update, name="board_update"),
    path("<int:board_id>/delete/", views.board_delete, name="board_delete"),
    path("<int:board_id>/lists/reorder/", views.list_reorder, name ="list_reorder"),
    path("lists/<int:list_id>/edit/", views.list_update, name="list_update"),
    path("lists/<int:list_id>/delete/", views.list_delete, name="list_delete"),

]