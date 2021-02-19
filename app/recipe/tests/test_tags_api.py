from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core import models
from .. import serializers

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    # to test the publicly available tags API

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        # to test that login is required for retrieving tags
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    # to test the authorized user tags API

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'testpassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        # to test retrieving tags
        models.Tag.objects.create(user=self.user, name='Vegan')
        models.Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        # this makes sure that the tags are returned in descending order
        tags = models.Tag.objects.all().order_by('-name')

        # many=True passed to make sure a list of objects is serialized not one
        serializer = serializers.TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        # to test tags returned are for the authenticated user
        user2 = get_user_model().objects.create_user(
            'test2@gmail.com',
            'testpassword'
        )

        models.Tag.objects.create(user=user2, name='Savoury')
        tag = models.Tag.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        # to test creating a new tag
        payload = {'name': 'Simple'}
        self.client.post(TAGS_URL, payload)

        exists = models.Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        # test creating a new tag with invalid payload
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
