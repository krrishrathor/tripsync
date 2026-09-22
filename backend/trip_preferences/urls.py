from django.urls import path
from .views import MyPreferenceView, GroupPreferenceAggregateView

urlpatterns = [
    path('me/', MyPreferenceView.as_view(), name='my-preference'),
    path('aggregate/', GroupPreferenceAggregateView.as_view(), name='preference-aggregate'),
]
