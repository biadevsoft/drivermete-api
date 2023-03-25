from django.urls import reverse
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class UserRegisterViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('user:register')

    def test_register_rider(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'password_confirmation': 'testpassword',
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue('user' in response.data['data'])
        self.assertTrue(User.objects.filter(email='testuser@example.com').exists())

    def test_register_valid_user_type(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'testpassword',
            'password_confirmation': 'testpassword',
            'user_type': 'rider'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ActivateAccountViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='testpassword',
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.url = reverse('user:activate-account', kwargs={'uidb64': self.uidb64, 'token': self.token})

    def test_activate_account(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(get_user_model().objects.get(email='testuser@example.com').email_verified_at)

    def test_activate_account_invalid_link(self):
        invalid_url = reverse('user:activate-account', kwargs={'uidb64': 'invalid_uidb64', 'token': 'invalid_token'})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
