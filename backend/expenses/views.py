from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from trips.models import Trip
from trips.permissions import IsTripMemberOrOwner
from .models import Expense
from .serializers import ExpenseSerializer
from .services import add_expense, calculate_settlements

class ExpenseListCreateView(APIView):
    permission_classes = [IsTripMemberOrOwner]

    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        self.check_object_permissions(request, trip)
        
        expenses = Expense.objects.filter(trip=trip).select_related('paid_by').prefetch_related('splits__user')
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        self.check_object_permissions(request, trip)
        
        data = request.data
        try:
            expense = add_expense(
                trip=trip,
                paid_by=request.user,
                amount=data.get('amount'),
                description=data.get('description'),
                splits=data.get('splits', []),
                category=data.get('category', '')
            )
            serializer = ExpenseSerializer(expense)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (ValueError, PermissionError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "Failed to create expense."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExpenseSettlementsView(APIView):
    permission_classes = [IsTripMemberOrOwner]
    
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id)
        self.check_object_permissions(request, trip)
        
        settlements = calculate_settlements(trip)
        return Response(settlements)
