from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .web_views import home_view, login_view, register_view, app_view

urlpatterns = [
    path('', home_view, name='root'),
    path('login/', login_view, name='login-page'),
    path('register/', register_view, name='register-page'),
    path('app/', app_view, name='app-page'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/', include('stories.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 