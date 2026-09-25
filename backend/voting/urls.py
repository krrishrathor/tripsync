from django.urls import path
from .views import VoteView, SelectDestinationView

urlpatterns = [
    path('votes/', VoteView.as_view(), name='trip-votes'),
    path('select-destination/', SelectDestinationView.as_view(), name='select-destination'),
]
