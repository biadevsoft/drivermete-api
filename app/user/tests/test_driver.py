from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()

CREATE_USER_DRIVER_URL = reverse('user:driver-register')


class UserDriverRegisterViewTestCase(APITestCase):
    """Test that a new user can be created successfully"""
    def test_create_user(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }
        response = self.client.post(CREATE_USER_DRIVER_URL, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Driver registered successfully.')
        self.assertIn('user', response.data['data'])
        self.assertIn('user_detail', response.data['data'])
