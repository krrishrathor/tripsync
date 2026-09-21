from django.urls import path
from .views import UserPreferenceView, GroupPreferenceView

urlpatterns = [
    path('trip/<uuid:trip_id>/my-preferences/', UserPreferenceView.as_view(), name='my-preferences'),
    path('trip/<uuid:trip_id>/group/', GroupPreferenceView.as_view(), name='group-preferences'),
]
