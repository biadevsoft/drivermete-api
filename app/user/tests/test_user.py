from unittest import mock

from django.urls import reverse
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode

from rest_framework import status
from rest_framework.test import APITestCase

from user.serializers import UserSerializer

User = get_user_model()


class UserRegisterViewTests(APITestCase):
    def test_user_register_valid_data(self):
        url = reverse('rider-register')
        data = {
            'email': 'test@example.com',
            'password': 'password',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '1234567890',
            'date_of_birth': '2000-01-01',
            'gender': 'M',
            'address': '123 Test St.',
            'profile_image': None,
            'timezone': 'UTC',
        }
        with mock.patch('user.views.send_activation_email.delay') as mock_send_activation_email:
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(mock_send_activation_email.call_count, 1)
            self.assertEqual(mock_send_activation_email.call_args[0][0], 'test@example.com')
            self.assertIn('activate-account', mock_send_activation_email.call_args[0][1])

    def test_user_register_invalid_data(self):
        url = reverse('rider-register')
        data = {
            'email': 'invalidemail',
            'password': 'pass',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '1234567890',
            'date_of_birth': '2000-01-01',
            'gender': 'M',
            'address': '123 Test St.',
            'profile_image': None,
            'timezone': 'UTC',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ActivateAccountViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password',
            username='testuser',
            first_name='Test',
            last_name='User',
            phone_number='1234567890',
            date_of_birth='2000-01-01',
            gender='M',
            address='123 Test St.',
            profile_image=None,
            timezone='UTC',
            user_type='rider',
            status='pending',
        )
        self.token_generator = UserSerializer().fields['remember_token'].default_token_generator

    def test_activate_account_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk)).decode()
        token = self.token_generator.make_token(self.user)
        url = reverse('activate-account', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verified_at)
        self.assertIsNotNone(self.user.souvenir_token)

    def test_activate_account_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk)).decode()
        token = 'invalidtoken'
        url = reverse('activate-account', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.email_verified_at)
        self.assertIsNone(self.user.souvenir_token)

    def test_activate_account_already_activated(self):
        self.user.email_verified_at = '2022-01-01 00:00:00+00'
        self.user.save()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk)).decode()
        token = self.token_generator.make_token(self.user)
        url = reverse('activate-account', kwargs={'uidb64': uid, 'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Account already activated')
