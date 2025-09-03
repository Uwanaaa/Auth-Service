from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest import mock
from django.core.cache import cache
from django.test import override_settings

User = get_user_model()

class UserAccountTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            'email': 'testuser@mail.com',
            'password': 'testpassword',
            'full_name': 'Test User',
        }
        self.user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            full_name=self.user_data['full_name'],
            username=self.user_data['email'],  
        )

    def test_user_registration(self):
        response = self.client.post(self.register_url, {
            'email': 'newuser@mail.com',
            'password': 'newpassword',
            'full_name': 'New User',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_user_login(self):
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

     
    @mock.patch('accounts.views.redis_client')
    def test_forgot_password(self, mock_redis):
        mock_redis.setex.return_value = True
        # This test would require implementation of the forgot password feature
        response = self.client.post(reverse('forgot_password'), {
            'email': self.user.email,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Additional assertions can be added based on the implementation


    def test_login_with_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'email': 'wronguser@mail.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    @override_settings(AXES_ENABLED=False)
    def test_rate_limiting(self):
        cache.clear()  # Reset rate limit tracking
        for _ in range(5):
            response = self.client.post(self.login_url, {
                'email': self.user_data['email'],
                'password': self.user_data['password'],
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('rate limit', response.content.decode().lower())
    # def test_brute_force_lockout(self):
    #     # Simulate failed login attempts up to the lockout threshold
    #     for _ in range(5):  # Assuming AXES_FAILURE_LIMIT = 5
    #         response = self.client.post(self.login_url, {
    #             'email': 'wronguser',
    #             'password': 'wrongpassword',
    #         })
    #     # The next attempt should trigger lockout
    #     response = self.client.post(self.login_url, {
    #         'email': 'wronguser',
    #         'password': 'wrongpassword',
    #     })
    #     self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    #     self.assertIn('locked', response.content.decode().lower())
