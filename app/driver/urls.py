from django.urls import path

from driver.views import (
    DriverRegisterView,
)

app_name = 'driver'


urlpatterns = [
    path('register/', DriverRegisterView.as_view(), name='register_driver'),
]
