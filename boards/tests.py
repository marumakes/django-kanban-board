import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Board, List, Card

User = get_user_model()


class SignupTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse("signup"), {
            "username": "alice",
            "password1": "SuperSecret123!",
            "password2": "SuperSecret123!",
        })
        self.assertRedirects(response, reverse("board_list"))
        self.assertTrue(User.objects.filter(username="alice").exists())


class LoginRequiredTests(TestCase):
    def test_board_list_redirects_anonymous_user(self):
        response = self.client.get(reverse("board_list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('board_list')}")


class BoardCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw12345!")
        self.client.force_login(self.user)

    def test_create_board(self):
        response = self.client.post(reverse("board_create"), {"name": "Launch Plan"})
        board = Board.objects.get(name="Launch Plan")
        self.assertEqual(board.owner, self.user)
        self.assertRedirects(response, reverse("board_detail", args=[board.id]))

    def test_update_board(self):
        board = Board.objects.create(name="Old Name", owner=self.user)
        self.client.post(reverse("board_update", args=[board.id]), {"name": "New Name"})
        board.refresh_from_db()
        self.assertEqual(board.name, "New Name")

    def test_delete_board_requires_post(self):
        board = Board.objects.create(name="Temp", owner=self.user)
        self.client.get(reverse("board_delete", args=[board.id]))
        self.assertTrue(Board.objects.filter(id=board.id).exists())
        response = self.client.post(reverse("board_delete", args=[board.id]))
        self.assertFalse(Board.objects.filter(id=board.id).exists())
        self.assertRedirects(response, reverse("board_list"))

    def test_delete_board_cascades_lists_and_cards(self):
        board = Board.objects.create(name="Temp", owner=self.user)
        lst = List.objects.create(board=board, name="To Do")
        card = Card.objects.create(list=lst, title="Task")
        self.client.post(reverse("board_delete", args=[board.id]))
        self.assertFalse(List.objects.filter(id=lst.id).exists())
        self.assertFalse(Card.objects.filter(id=card.id).exists())


class ListAndCardCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw12345!")
        self.client.force_login(self.user)
        self.board = Board.objects.create(name="Board", owner=self.user)

    def test_create_list(self):
        self.client.post(reverse("list_create", args=[self.board.id]), {"name": "To Do"})
        self.assertTrue(List.objects.filter(board=self.board, name="To Do").exists())

    def test_rename_list(self):
        lst = List.objects.create(board=self.board, name="Old")
        self.client.post(reverse("list_update", args=[lst.id]), {"name": "New"})
        lst.refresh_from_db()
        self.assertEqual(lst.name, "New")

    def test_delete_list_cascades_cards(self):
        lst = List.objects.create(board=self.board, name="To Do")
        card = Card.objects.create(list=lst, title="Task")
        self.client.post(reverse("list_delete", args=[lst.id]))
        self.assertFalse(List.objects.filter(id=lst.id).exists())
        self.assertFalse(Card.objects.filter(id=card.id).exists())

    def test_create_card(self):
        lst = List.objects.create(board=self.board, name="To Do")
        self.client.post(reverse("card_create", args=[lst.id]), {"title": "Write tests"})
        self.assertTrue(Card.objects.filter(list=lst, title="Write tests").exists())

    def test_edit_card(self):
        lst = List.objects.create(board=self.board, name="To Do")
        card = Card.objects.create(list=lst, title="Old title")
        self.client.post(reverse("card_detail", args=[card.id]), {
            "title": "New title", "description": "Updated",
        })
        card.refresh_from_db()
        self.assertEqual(card.title, "New title")

    def test_delete_card(self):
        lst = List.objects.create(board=self.board, name="To Do")
        card = Card.objects.create(list=lst, title="Task")
        self.client.post(reverse("card_delete", args=[card.id]))
        self.assertFalse(Card.objects.filter(id=card.id).exists())


class OwnershipIsolationTests(TestCase):
    """One user should never be able to view or modify another user's data via a guessed URL."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pw12345!")
        self.intruder = User.objects.create_user(username="intruder", password="pw12345!")
        self.board = Board.objects.create(name="Private Board", owner=self.owner)
        self.list = List.objects.create(board=self.board, name="To Do")
        self.card = Card.objects.create(list=self.list, title="Secret Task")
        self.client.force_login(self.intruder)

    def test_cannot_view_other_users_board(self):
        response = self.client.get(reverse("board_detail", args=[self.board.id]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_view_other_users_card(self):
        response = self.client.get(reverse("card_detail", args=[self.card.id]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_other_users_board(self):
        self.client.post(reverse("board_delete", args=[self.board.id]))
        self.assertTrue(Board.objects.filter(id=self.board.id).exists())

    def test_cannot_add_list_to_other_users_board(self):
        response = self.client.post(reverse("list_create", args=[self.board.id]), {"name": "Sneaky"})
        self.assertEqual(response.status_code, 404)

    def test_cannot_add_card_to_other_users_list(self):
        response = self.client.post(reverse("card_create", args=[self.list.id]), {"title": "Sneaky"})
        self.assertEqual(response.status_code, 404)


class ReorderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw12345!")
        self.client.force_login(self.user)
        self.board = Board.objects.create(name="Board", owner=self.user)
        self.list_a = List.objects.create(board=self.board, name="A", position=0)
        self.list_b = List.objects.create(board=self.board, name="B", position=1)
        self.card_1 = Card.objects.create(list=self.list_a, title="Card 1", position=0)
        self.card_2 = Card.objects.create(list=self.list_a, title="Card 2", position=1)

    def test_reorder_cards_within_same_list(self):
        self.client.post(
            reverse("card_reorder"),
            data=json.dumps({"list_id": self.list_a.id, "ordered_ids": [self.card_2.id, self.card_1.id]}),
            content_type="application/json",
        )
        self.card_1.refresh_from_db()
        self.card_2.refresh_from_db()
        self.assertEqual(self.card_2.position, 0)
        self.assertEqual(self.card_1.position, 1)

    def test_move_card_to_different_list(self):
        self.client.post(
            reverse("card_reorder"),
            data=json.dumps({"list_id": self.list_b.id, "ordered_ids": [self.card_1.id]}),
            content_type="application/json",
        )
        self.card_1.refresh_from_db()
        self.assertEqual(self.card_1.list_id, self.list_b.id)
        self.assertEqual(self.card_1.position, 0)

    def test_reorder_lists(self):
        self.client.post(
            reverse("list_reorder", args=[self.board.id]),
            data=json.dumps({"ordered_ids": [self.list_b.id, self.list_a.id]}),
            content_type="application/json",
        )
        self.list_a.refresh_from_db()
        self.list_b.refresh_from_db()
        self.assertEqual(self.list_b.position, 0)
        self.assertEqual(self.list_a.position, 1)

    def test_reorder_rejects_get(self):
        response = self.client.get(reverse("card_reorder"))
        self.assertEqual(response.status_code, 405)
