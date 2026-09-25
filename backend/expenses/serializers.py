from rest_framework import serializers
from .models import Expense, ExpenseSplit
from django.contrib.auth import get_user_model

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    
    class Meta:
        model = ExpenseSplit
        fields = ['id', 'user', 'user_id', 'amount_owed']

class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserBasicSerializer(read_only=True)
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    
    class Meta:
        model = Expense
        fields = ['id', 'trip_id', 'paid_by', 'amount', 'description', 'category', 'date', 'created_at', 'splits']
