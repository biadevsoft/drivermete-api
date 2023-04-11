from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rider.serializers import UserSerializer
from core.models import User


class UserRegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('rider:register_rider')

    def test_create_valid_user(self):
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword',
            'phone_number': '+1 123-456-7890',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': User.GenderUnitChoices.MALE,
            'address': '123 Main St',
            'timezone': 'America/New_York',
            'user_type': User.UserTypeChoices.RIDER,
            'status': User.StatusUnitChoices.ACTIVE,
            'login_type': User.LoginTypeChoices.EMAIL,
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=data['email'])
        serializer = UserSerializer(user)
        self.assertEqual(response.data['data']['user'], serializer.data)
