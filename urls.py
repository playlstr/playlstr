from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('playlstr/', include('playlstr.urls')),
    path('admin/', admin.site.urls),
]
