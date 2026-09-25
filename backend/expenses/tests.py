from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from trips.models import Trip, TripMember
from expenses.models import Expense, ExpenseSplit
from expenses.services import add_expense, calculate_settlements

User = get_user_model()

class ExpenseServiceTests(TestCase):
    def setUp(self):
        self.u1 = User.objects.create_user('alice', 'a@a.com', 'pw')
        self.u2 = User.objects.create_user('bob', 'b@a.com', 'pw')
        self.u3 = User.objects.create_user('charlie', 'c@a.com', 'pw')
        
        self.trip = Trip.objects.create(name='Test Trip', owner=self.u1)
        TripMember.objects.create(trip=self.trip, user=self.u1, role='OWNER')
        TripMember.objects.create(trip=self.trip, user=self.u2, role='MEMBER')
        TripMember.objects.create(trip=self.trip, user=self.u3, role='MEMBER')

    def test_add_expense(self):
        expense = add_expense(
            self.trip, self.u1, Decimal('300.00'), 'Dinner',
            splits=[
                {'user_id': self.u1.id, 'amount': 100},
                {'user_id': self.u2.id, 'amount': 100},
                {'user_id': self.u3.id, 'amount': 100},
            ]
        )
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(ExpenseSplit.objects.count(), 3)
        self.assertEqual(expense.amount, Decimal('300.00'))

    def test_add_expense_invalid_split(self):
        with self.assertRaises(ValueError):
            add_expense(
                self.trip, self.u1, Decimal('300.00'), 'Dinner',
                splits=[
                    {'user_id': self.u1.id, 'amount': 100},
                    {'user_id': self.u2.id, 'amount': 100},
                ]
            )

    def test_calculate_settlements_simple(self):
        # u1 pays 300, split 100 each.
        add_expense(
            self.trip, self.u1, Decimal('300.00'), 'Dinner',
            splits=[
                {'user_id': self.u1.id, 'amount': 100},
                {'user_id': self.u2.id, 'amount': 100},
                {'user_id': self.u3.id, 'amount': 100},
            ]
        )
        # Expected:
        # u1 balance = +300 - 100 = +200
        # u2 balance = -100
        # u3 balance = -100
        # So u2 owes u1 100, u3 owes u1 100.
        settlements = calculate_settlements(self.trip)
        
        self.assertEqual(len(settlements), 2)
        
        # Verify amounts
        total_settled = sum(s['amount'] for s in settlements)
        self.assertEqual(total_settled, 200.0)
        
        for s in settlements:
            self.assertEqual(s['to_user_id'], self.u1.id)
            self.assertIn(s['from_user_id'], [self.u2.id, self.u3.id])
            self.assertEqual(s['amount'], 100.0)

    def test_calculate_settlements_complex(self):
        # u1 pays 300, split 100 each
        add_expense(
            self.trip, self.u1, Decimal('300.00'), 'Dinner',
            splits=[
                {'user_id': self.u1.id, 'amount': 100},
                {'user_id': self.u2.id, 'amount': 100},
                {'user_id': self.u3.id, 'amount': 100},
            ]
        )
        # u2 pays 150 for cab, split 50 each
        add_expense(
            self.trip, self.u2, Decimal('150.00'), 'Cab',
            splits=[
                {'user_id': self.u1.id, 'amount': 50},
                {'user_id': self.u2.id, 'amount': 50},
                {'user_id': self.u3.id, 'amount': 50},
            ]
        )
        # Balances:
        # u1: paid 300, owes 150 -> +150
        # u2: paid 150, owes 150 -> 0
        # u3: paid 0, owes 150 -> -150
        # Expected settlement: u3 owes u1 150
        settlements = calculate_settlements(self.trip)
        
        self.assertEqual(len(settlements), 1)
        self.assertEqual(settlements[0]['from_user_id'], self.u3.id)
        self.assertEqual(settlements[0]['to_user_id'], self.u1.id)
        self.assertEqual(settlements[0]['amount'], 150.0)

class ExpenseAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.u1 = User.objects.create_user('alice2', 'a2@a.com', 'pw')
        self.u2 = User.objects.create_user('bob2', 'b2@a.com', 'pw')
        
        self.trip = Trip.objects.create(name='API Trip', owner=self.u1)
        TripMember.objects.create(trip=self.trip, user=self.u1, role='OWNER')
        TripMember.objects.create(trip=self.trip, user=self.u2, role='MEMBER')
        
        self.client.force_authenticate(user=self.u1)
        self.url = f'/api/trips/{self.trip.id}/expenses/'

    def test_post_expense(self):
        payload = {
            "amount": 200,
            "description": "Hotel",
            "splits": [
                {"user_id": self.u1.id, "amount": 100},
                {"user_id": self.u2.id, "amount": 100}
            ]
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(ExpenseSplit.objects.count(), 2)

    def test_get_settlements(self):
        add_expense(
            self.trip, self.u1, Decimal('200.00'), 'Hotel',
            splits=[
                {'user_id': self.u1.id, 'amount': 100},
                {'user_id': self.u2.id, 'amount': 100},
            ]
        )
        res = self.client.get(f'{self.url}settlements/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['amount'], 100.0)
