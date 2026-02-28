from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationAPITest(APITestCase):
    """Tests for registration, login, and profile APIs."""

    def test_register_user(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'StrongPass123!',
                'password_confirm': 'StrongPass123!',
                'bio': 'Reader and writer',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_login_user(self):
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            '/api/auth/token/',
            {'email': 'existing@example.com', 'password': 'StrongPass123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_get_profile(self):
        user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='StrongPass123!',
        )
        self.client.force_authenticate(user=user)

        response = self.client.get('/api/auth/profile/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'profile@example.com')


class RootEndpointTest(APITestCase):
    """Tests for root service endpoint."""

    def test_root_endpoint_returns_api_info(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/html', response['Content-Type'])
        self.assertContains(response, 'Interactive Story Graph Platform')
        self.assertContains(response, '/login/')
        self.assertContains(response, '/register/')
        self.assertContains(response, '/app/')
