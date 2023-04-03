from django.urls import path

from user.views import (
    UserView,
    UserRegisterView,
    ActivateAccountView,
    LoginView,
    LogoutView,
)

app_name = 'user'


urlpatterns = [
    path('user/', UserView.as_view(), name='user'),
    path('rider-register/', UserRegisterView.as_view(), name='rider-register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate-account'),
]
