from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UpdateProfileTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            is_verified=True
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
    def test_update_profile_success(self):
        """Test successful profile update"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith'
        }
        
        response = self.client.patch('/api/users/update-profile/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'Jane')
        self.assertEqual(response.data['user']['last_name'], 'Smith')
        self.assertIn('Profile updated successfully', response.data['detail'])
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Smith')
    
    def test_update_email_requires_verification(self):
        """Test that updating email marks user as unverified"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        data = {
            'email': 'newemail@example.com'
        }
        
        response = self.client.patch('/api/users/update-profile/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'newemail@example.com')
        self.assertEqual(response.data['user']['is_verified'], False)
        self.assertIn('verify your new email', response.data['detail'])
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.user.is_verified, False)
    
    def test_update_profile_unauthenticated(self):
        """Test that unauthenticated users cannot update profile"""
        data = {
            'first_name': 'Jane'
        }
        
        response = self.client.patch('/api/users/update-profile/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile_empty_fields(self):
        """Test that empty strings are not allowed for names"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        data = {'first_name': ''}
        response = self.client.patch('/api/users/update-profile/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
        
        data = {'last_name': ''}
        response = self.client.patch('/api/users/update-profile/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('last_name', response.data)

