from django.contrib import admin
from django.urls import path, include
from users.views import CookieTokenRefreshView, EmailTokenObtainPairView
from users.views import RegisterUserView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', RegisterUserView.as_view(), name='register_user'),
    path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('products.urls')),
]
