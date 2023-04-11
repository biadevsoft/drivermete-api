from django.urls import path

from rider.views import (
    UserRegisterView,
)

app_name = 'rider'


urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register_rider'),
]
