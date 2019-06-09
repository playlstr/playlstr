"""playlstr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('list/<int:playlist_id>/', views.playlist, name='playlist'),
    path('track/<int:track_id>/', views.track, name='track'),
    path('import/', views.import_playlist, name='import'),
    path('import/spotify/', views.spotify_import, name='spotify_import'),
    path('create/', views.create_playlist, name='playlist_create'),
    path('track-autocomplete/', views.track_autocomplete, name='track_autocomplete'),
    path('playlist-update/', views.playlist_update, name='playlist_update'),
    path('', include('social_django.urls', namespace='social')),
    path('logout/', views.logout_view, name='logout'),
    path('get-spotify-token/', views.get_spotify_token, name='get_spotify_token'),
    path('spotify-auth-user/', views.spotify_auth_user, name='spotify_auth_user'),
    path('client-import/', views.client_import, name='client_import'),
    path('local-import/', views.local_file_import, name='local_import')
]
