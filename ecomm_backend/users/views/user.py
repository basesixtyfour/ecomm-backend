from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..serializers import UserInfoSerializer, RegisterUserSerializer


class UserInfoView(generics.RetrieveAPIView):
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RegisterUserView(generics.CreateAPIView):
    serializer_class = RegisterUserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            response.data,
            status=response.status_code,
            headers=response.headers,
        )
