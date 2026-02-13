from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import EmailTokenObtainPairView
from users.views import RegisterUserView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', RegisterUserView.as_view(), name='register_user'),
    path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
