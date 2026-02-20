from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import CookieTokenRefreshView, EmailTokenObtainPairView, RegisterUserView, UserInfoView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', UserInfoView.as_view(), name='user_info'),
    path('api/register/', RegisterUserView.as_view(), name='register_user'),
    path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('products.urls')),
    path('api/', include('cart.urls')),
    path('api/', include('orders.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
