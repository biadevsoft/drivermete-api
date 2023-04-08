from django.urls import path

from user.views import (
    UserRegisterView,
)

app_name = 'user'


urlpatterns = [
    path('register/rider/', UserRegisterView.as_view(), name='register-rider'),
]
