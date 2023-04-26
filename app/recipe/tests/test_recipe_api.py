import os
import tempfile

from core.models import Ingredient, Recipe, Tag
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from recipe.serializers import RecipeDetailSerializer, RecipeSerializer
from rest_framework import status
from rest_framework.test import APIClient

RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    # return url for recipe image upload
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id):
    # return recipe detail url
    return reverse("recipe:recipe-detail", args=[recipe_id])


def sample_tag(user, name="Main course"):
    # create and return sample tag
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Cinnamon"):
    # create and return a sample ingredient
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    # create and return sample recipe
    defaults = {"title": "Smaple recipe", "time_minutes": 10, "price": 5.00}
    # for updating default dict when values excluding user is passed
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    # to test unauthenticated recipe api access

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        # to test that authentication is required
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    # to test authenticated recipe api

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@gmail.com", "testpassword"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        # to test retrieving a list of recipes
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        # to test retrieving recipes for user
        user2 = get_user_model().objects.create_user("other@gmail.com", "testpassword")
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        # test viewing a recipe detail
        recipe = sample_recipe(user=self.user)

        # adding an item to a many-many field
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        # many=True is not required for a serilizing a single object
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        # to test creating a recipe
        payload = {"title": "Chocolate Cheesecake", "time_minutes": 30, "price": 5.00}
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        # to test creating a recipe with tags
        tag1 = sample_tag(user=self.user, name="Vegan")
        tag2 = sample_tag(user=self.user, name="Dessert")
        payload = {
            "title": "Avocado Lime Cheesecake",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 60,
            "price": 20.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        # to test creating a recipe with ingredients
        ingredient1 = sample_ingredient(user=self.user, name="Prawns")
        ingredient2 = sample_ingredient(user=self.user, name="Ginger")
        payload = {
            "title": "Thai Prawn Red Curry",
            "ingredients": [ingredient1.id, ingredient2.id],
            "time_minutes": 20,
            "price": 7.00,
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        # to test updating recipe with a patch request
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Curry")
        payload = {"title": "Chicken Tikka", "tags": [new_tag.id]}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        # to test updating a recipe with put request
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {"title": "Spaghetti Carbonara", "time_minutes": 25, "price": 5.00}
        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.time_minutes, payload["time_minutes"])
        self.assertEqual(recipe.price, payload["price"])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "testuser@gmail.com", "testpassword"
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        # tear down function that runs after tests
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        # to test uploading image to recipe
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")

            # setting the pointer back to the beginning of the file
            ntf.seek(0)

            # format=multipart is passed for making a multipart form request
            # which means that the form contains data
            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        # to test uploading an invalid image
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        # to test returning recipes with specific tags
        recipe1 = sample_recipe(user=self.user, title="Thai Vegetable Curry")
        recipe2 = sample_recipe(user=self.user, title="Kadhai Paneer")

        tag1 = sample_tag(user=self.user, name="Vegan")
        tag2 = sample_tag(user=self.user, name="Vegetarian")

        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        recipe3 = sample_recipe(user=self.user, title="Fish and Chips")

        res = self.client.get(RECIPES_URL, {"tags": f"{tag1.id},{tag2.id}"})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        # to test returning recipes with specific ingredients
        recipe1 = sample_recipe(user=self.user, title="Thai Vegetable Curry")
        recipe2 = sample_recipe(user=self.user, title="Kadhai Paneer")

        ingredient1 = sample_ingredient(user=self.user, name="Ginger")
        ingredient2 = sample_ingredient(user=self.user, name="Cottage Cheese")

        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        recipe3 = sample_recipe(user=self.user, title="Fish and Chips")

        res = self.client.get(
            RECIPES_URL, {"ingredients": f"{ingredient1.id},{ingredient2.id}"}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
