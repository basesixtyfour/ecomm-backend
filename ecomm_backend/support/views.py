from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatRoom
from .serializers import AgentChatRoomSerializer, ChatRoomSerializer


class ChatRoomView(APIView):
    """Get-or-create an active chat room for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        room = ChatRoom.objects.filter(
            user=request.user,
            status=ChatRoom.Status.ACTIVE,
        ).first()

        created = False
        if not room:
            room = ChatRoom.objects.create(user=request.user)
            created = True

        serializer = ChatRoomSerializer(room)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ActiveRoomsView(APIView):
    """List active chat rooms for support agents."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        rooms = (
            ChatRoom.objects.filter(status=ChatRoom.Status.ACTIVE)
            .select_related("user")
            .order_by("-last_message_at")
        )
        serializer = AgentChatRoomSerializer(rooms, many=True)
        return Response(serializer.data)
