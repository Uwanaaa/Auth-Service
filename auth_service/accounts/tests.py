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
    
    
    @override_settings(
            AXES_ENABLED=True,  # Enable rate limiting
            AXES_LOGIN_FAILURE_LIMIT=5,  # Allow 5 attempts before rate limiting
            AXES_COOLOFF_TIME=1,  # Cool-off period in seconds (for testing)
            AXES_RESET_ON_SUCCESS=True,  # Reset attempts on successful login
        )
    def test_rate_limiting(self):
        cache.clear()  # Clear cache to reset rate limit tracking
        client_ip = '127.0.0.1'  # Simulate consistent client IP for rate limiting

        # Perform login attempts within the allowed limit
        for _ in range(5):
            response = self.client.post(
                self.login_url,
                data={
                    'email': self.user_data['email'],
                    'password': 'wrongpassword'  # Simulate failed login attempts
                },
                REMOTE_ADDR=client_ip  # Ensure consistent IP for rate limiting
            )
            print(response.content.decode().lower())
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Expect failure due to wrong password

        # The 6th attempt should be rate-limited
        response = self.client.post(
            self.login_url,
            data={
                'email': self.user_data['email'],
                'password': 'wrongpassword'
            },
            REMOTE_ADDR=client_ip
        )
        print(response.content.decode().lower())
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.data)  # Check for error key in JSON response
        self.assertTrue(
            'too many login attempts' in str(response.data).lower(),
            msg="Rate limit error message not found"
        )

    @override_settings(
        AXES_ENABLED=True,
        AXES_LOGIN_FAILURE_LIMIT=5,
        AXES_COOLOFF_TIME=1,
        AXES_RESET_ON_SUCCESS=True,
    )
    def test_rate_limit_reset_on_success(self):
        cache.clear()  # Clear cache to reset rate limit tracking
        client_ip = '127.0.0.1'

        # Perform 4 failed login attempts
        for _ in range(4):
            response = self.client.post(
                self.login_url,
                data={
                    'email': self.user_data['email'],
                    'password': 'wrongpassword'
                },
                REMOTE_ADDR=client_ip
            )
            print(response.content.decode().lower())
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Perform a successful login to reset the rate limit
        response = self.client.post(
            self.login_url,
            data={
                'email': self.user_data['email'],
                'password': self.user_data['password']
            },
            REMOTE_ADDR=client_ip
        )
        print(response.content.decode().lower())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try another login attempt, which should not be rate-limited
        response = self.client.post(
            self.login_url,
            data={
                'email': self.user_data['email'],
                'password': 'wrongpassword'
            },
            REMOTE_ADDR=client_ip
        )
        print(response.content.decode().lower())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
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
