from django.urls import path
from .views import CallHistoryView, CallDetailView

urlpatterns = [
    path('history/', CallHistoryView.as_view(), name='call-history'),
    path('<uuid:pk>/', CallDetailView.as_view(), name='call-detail'),
]