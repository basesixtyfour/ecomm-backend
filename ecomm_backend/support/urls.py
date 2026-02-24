from django.urls import path

from .views import ActiveRoomsView, ChatRoomView

urlpatterns = [
    path("support/chat/", ChatRoomView.as_view(), name="support-chat"),
    path("support/chat/rooms/", ActiveRoomsView.as_view(), name="support-rooms"),
]
