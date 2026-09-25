from django.urls import path
from .views import ExpenseListCreateView, ExpenseSettlementsView

urlpatterns = [
    path('', ExpenseListCreateView.as_view(), name='trip-expenses'),
    path('settlements/', ExpenseSettlementsView.as_view(), name='trip-settlements'),
]
