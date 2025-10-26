from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet, ChatRoomViewSet

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='messages')
router.register(r'rooms', ChatRoomViewSet, basename='rooms')

urlpatterns = [
    path('', include(router.urls)),
]