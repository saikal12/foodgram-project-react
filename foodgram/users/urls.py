from django.conf.urls import url
from django.urls import include
from rest_framework import routers

from users.views import MyUserViewSet

app_name = 'users'

router = routers.DefaultRouter()
router.register('users', MyUserViewSet, basename='users')


urlpatterns = [
    url('', include(router.urls)),
    url('', include('djoser.urls')),
    url('auth/', include('djoser.urls.authtoken')),
]
