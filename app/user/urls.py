from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from user.views import (
    UserRegisterView,
    UserDriverRegisterView,
    ActivateAccountView,
)

app_name = 'user'


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('driver-register/', UserDriverRegisterView.as_view(), name='driver-register'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate-account'),
    path('token/', obtain_auth_token, name='token'),
]
