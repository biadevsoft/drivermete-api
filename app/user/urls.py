from django.urls import path

from user.views import (
    UserRegisterView,
    DeleteUserAccount,
)

app_name = 'user'


urlpatterns = [
    path('register/rider/', UserRegisterView.as_view(), name='register_rider'),
    path('delete-account/', DeleteUserAccount.as_view(), name='delete_user_account'),
]
