from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@gmail.com',
            password='password123'
        )
        # it automatically logs the user in for testing purposes.
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='password123',
            name='Test user full name'
        )

    def test_users_listed(self):
        # to test that the users are listed in the user page

        # this will create a url for list user page
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)  # sends a get request to the given url

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        # to test that user edit page works

        # how to the id is assigned - /admin/core/user/1
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        # testing that the status code for the response is 200 which means ok.
        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        # to test create user page works

        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
