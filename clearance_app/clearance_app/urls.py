from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from clearance import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clearance.urls')),  # Make sure this line is present
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
