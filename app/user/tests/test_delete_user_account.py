from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token


User = get_user_model()


class DeleteUserAccountTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            username='John',
            user_type='rider',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_delete_account_with_valid_password_and_confirm_password(self):
        data = {
            'password': 'password123',
            'password2': 'password123',
        }
        url = reverse('user:delete_user_account')
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_delete_account_with_invalid_password(self):
        data = {
            'password': 'wrongpassword',
            'password2': 'wrongpassword',
        }
        url = reverse('user:delete_user_account')
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(id=self.user.id).exists())

    def test_delete_account_with_password_and_unmatched_confirm_password(self):
        data = {
            'password': 'password123',
            'password2': 'wrongpassword',
        }
        url = reverse('user:delete_user_account')
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(id=self.user.id).exists())