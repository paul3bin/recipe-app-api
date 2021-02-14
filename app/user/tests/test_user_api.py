from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')


def create_user(**params):
    return get_user_model().objects.create(**params)


class PublicUserApiTests(TestCase):
    # to test the users API (public)

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        # to test creating user with valid payload successful
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'Test Name',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        # checking whether the user is created or not
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**res.data)

        # checking if the password matches what user entered
        self.assertTrue(user.check_password(payload['password']))

        # checking whether the passoword is not returned in the response
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        # to test whether user already exists or not
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        # checking whether the user already exists or not.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        # to test whether the password is atleast 8 characters
        payload = {
            'email': 'test@gmail.com',
            'password': 'pw',
            'name': 'Test',
        }

        res = self.client.post(CREATE_USER_URL, payload)

        # checking for the password length
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()

        self.assertFalse(user_exists)
