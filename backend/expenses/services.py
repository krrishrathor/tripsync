from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from trips.models import Trip, TripMember
from .models import Expense, ExpenseSplit
from typing import List, Dict

def add_expense(trip: Trip, paid_by, amount: Decimal, description: str, splits: List[Dict], category: str = "") -> Expense:
    """
    Creates an expense and its splits atomically.
    `splits` should be a list of dicts: [{'user_id': <id>, 'amount': <amount>}, ...]
    Validates that the sum of splits equals the total amount.
    """
    if not TripMember.objects.filter(trip=trip, user=paid_by).exists():
        raise PermissionError("Payer must be a member of the trip.")

    total_split = sum(Decimal(str(s['amount'])) for s in splits)
    if abs(total_split - Decimal(str(amount))) > Decimal('0.01'):
        raise ValueError(f"Sum of splits ({total_split}) does not equal total amount ({amount}).")

    with transaction.atomic():
        expense = Expense.objects.create(
            trip=trip,
            paid_by=paid_by,
            amount=amount,
            description=description,
            category=category
        )
        
        split_objects = []
        for s in splits:
            split_objects.append(
                ExpenseSplit(
                    expense=expense,
                    user_id=s['user_id'],
                    amount_owed=Decimal(str(s['amount']))
                )
            )
        
        ExpenseSplit.objects.bulk_create(split_objects)
        
    return expense


def calculate_settlements(trip: Trip) -> List[Dict]:
    """
    Calculates who owes whom using a debt simplification algorithm.
    Returns a list of transactions: [{'from_user_id': X, 'from_user_name': '...', 'to_user_id': Y, 'to_user_name': '...', 'amount': Z}]
    """
    # 1. Calculate net balances for each user in the trip
    balances = {}
    
    # Initialize balances for all members to 0
    members = TripMember.objects.filter(trip=trip).select_related('user')
    user_map = {}
    for m in members:
        balances[m.user.id] = Decimal('0.00')
        user_map[m.user.id] = m.user

    # Add what they paid (they are owed this amount)
    expenses = Expense.objects.filter(trip=trip)
    for e in expenses:
        if e.paid_by_id in balances:
            balances[e.paid_by_id] += e.amount
            
    # Subtract what they owe
    splits = ExpenseSplit.objects.filter(expense__trip=trip)
    for s in splits:
        if s.user_id in balances:
            balances[s.user_id] -= s.amount_owed

    # 2. Separate into debtors and creditors
    debtors = []
    creditors = []
    
    for uid, balance in balances.items():
        if balance < Decimal('-0.01'):
            debtors.append({'user_id': uid, 'amount': abs(balance)})
        elif balance > Decimal('0.01'):
            creditors.append({'user_id': uid, 'amount': balance})
            
    # Sort by largest amounts first to minimize transactions (greedy approach)
    debtors.sort(key=lambda x: x['amount'], reverse=True)
    creditors.sort(key=lambda x: x['amount'], reverse=True)
    
    # 3. Resolve debts
    settlements = []
    i, j = 0, 0
    
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        
        settle_amount = min(debtor['amount'], creditor['amount'])
        
        # Format the settlement transaction
        settlements.append({
            'from_user_id': debtor['user_id'],
            'from_user_name': user_map[debtor['user_id']].first_name or user_map[debtor['user_id']].username,
            'to_user_id': creditor['user_id'],
            'to_user_name': user_map[creditor['user_id']].first_name or user_map[creditor['user_id']].username,
            'amount': float(settle_amount)
        })
        
        debtor['amount'] -= settle_amount
        creditor['amount'] -= settle_amount
        
        if debtor['amount'] < Decimal('0.01'):
            i += 1
        if creditor['amount'] < Decimal('0.01'):
            j += 1
            
    return settlements
