from django.urls import path

from user.views import (
    UserListAllView,
    ManagerRegisterView,
    UpdateUserStatus,
    UserPasswordChangeView,
    #UserLogoutView,
)
app_name = 'user'


urlpatterns = [
    path('list/', UserListAllView.as_view(), name='list_user'),
    path('register/manager/', ManagerRegisterView.as_view(), name='register_manager'),
    path('status/<int:pk>/', UpdateUserStatus.as_view(), name='update_user_status'),
    path('change-password/', UserPasswordChangeView.as_view(), name='change_password'),
    #path('logout/', UserLogoutView.as_view(), name='logout'),
]
